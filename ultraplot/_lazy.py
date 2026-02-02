#!/usr/bin/env python3
"""
Helpers for lazy attribute loading in :mod:`ultraplot`.
"""

from __future__ import annotations

import ast
import importlib.util
import types
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional


class LazyLoader:
    """
    Encapsulates lazy-loading mechanics for the ultraplot top-level module.
    """

    def __init__(
        self,
        *,
        package: str,
        package_path: Path,
        exceptions: Mapping[str, tuple[str, Optional[str]]],
        setup_callback: Callable[[], None],
        registry_attr_callback: Callable[[str], Optional[type]],
        registry_build_callback: Callable[[], None],
        registry_names_callback: Callable[[], Optional[Mapping[str, type]]],
        attr_map_key: str = "_ATTR_MAP",
        eager_key: str = "_EAGER_DONE",
    ):
        self._package = package
        self._package_path = Path(package_path)
        self._exceptions = exceptions
        self._setup = setup_callback
        self._get_registry_attr = registry_attr_callback
        self._build_registry_map = registry_build_callback
        self._registry_names = registry_names_callback
        self._attr_map_key = attr_map_key
        self._eager_key = eager_key

    def _import_module(self, module_name: str) -> types.ModuleType:
        return import_module(f".{module_name}", self._package)

    def _get_attr_map(
        self, module_globals: Mapping[str, Any]
    ) -> Optional[Dict[str, tuple[str, Optional[str]]]]:
        return module_globals.get(self._attr_map_key)  # type: ignore[return-value]

    def _set_attr_map(
        self,
        module_globals: MutableMapping[str, Any],
        value: Dict[str, tuple[str, Optional[str]]],
    ) -> None:
        module_globals[self._attr_map_key] = value

    def _get_eager_done(self, module_globals: Mapping[str, Any]) -> bool:
        return bool(module_globals.get(self._eager_key))

    def _set_eager_done(
        self, module_globals: MutableMapping[str, Any], value: bool
    ) -> None:
        module_globals[self._eager_key] = value

    @staticmethod
    def _parse_all(path: Path) -> Optional[list[str]]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            return None
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    try:
                        value = ast.literal_eval(node.value)
                    except Exception:
                        return None
                    if isinstance(value, (list, tuple)) and all(
                        isinstance(item, str) for item in value
                    ):
                        return list(value)
                    return None
        return None

    def _discover_modules(self, module_globals: MutableMapping[str, Any]) -> None:
        if self._get_attr_map(module_globals) is not None:
            return

        attr_map = {}
        base = self._package_path

        protected = set(self._exceptions.keys())
        protected.add("figure")

        for path in base.glob("*.py"):
            if path.name.startswith("_") or path.name == "setup.py":
                continue
            module_name = path.stem
            if module_name in protected:
                continue

            names = self._parse_all(path)
            if names:
                for name in names:
                    if name not in protected:
                        attr_map[name] = (module_name, name)

            if module_name not in attr_map:
                attr_map[module_name] = (module_name, None)

        for path in base.iterdir():
            if not path.is_dir() or path.name.startswith("_") or path.name == "tests":
                continue
            module_name = path.name
            if module_name in protected:
                continue

            if (path / "__init__.py").is_file():
                names = self._parse_all(path / "__init__.py")
                if names:
                    for name in names:
                        if name not in protected:
                            attr_map[name] = (module_name, name)
                attr_map[module_name] = (module_name, None)

        attr_map.pop("figure", None)
        self._set_attr_map(module_globals, attr_map)

    def resolve_extra(self, name: str, module_globals: MutableMapping[str, Any]) -> Any:
        module_name, attr = self._exceptions[name]
        module = self._import_module(module_name)
        value = module if attr is None else getattr(module, attr)
        # Special handling for figure - don't set it as an attribute to allow module imports
        if name != "figure":
            module_globals[name] = value
        return value

    def load_all(self, module_globals: MutableMapping[str, Any]) -> list[str]:
        # If eager loading has been done but __all__ is not in globals, re-run the discovery
        if self._get_eager_done(module_globals) and "__all__" not in module_globals:
            # Reset eager loading to force re-discovery
            self._set_eager_done(module_globals, False)

        if self._get_eager_done(module_globals):
            return sorted(module_globals.get("__all__", []))
        self._set_eager_done(module_globals, True)
        self._setup()
        self._discover_modules(module_globals)
        names = set(self._get_attr_map(module_globals).keys())
        for name in list(names):
            try:
                self.get_attr(name, module_globals)
            except AttributeError:
                pass
        names.update(self._exceptions.keys())
        self._build_registry_map()
        registry_names = self._registry_names()
        if registry_names:
            names.update(registry_names)
        names.update({"__version__", "version", "name", "setup", "pyplot"})
        if importlib.util.find_spec("cartopy") is not None:
            names.add("cartopy")
        if importlib.util.find_spec("mpl_toolkits.basemap") is not None:
            names.add("basemap")
        return sorted(names)

    def get_attr(self, name: str, module_globals: MutableMapping[str, Any]) -> Any:
        if name in self._exceptions:
            self._setup()
            return self.resolve_extra(name, module_globals)

        self._discover_modules(module_globals)
        attr_map = self._get_attr_map(module_globals)
        if attr_map and name in attr_map:
            module_name, attr_name = attr_map[name]
            self._setup()
            module = self._import_module(module_name)
            value = getattr(module, attr_name) if attr_name else module
            # Special handling for figure - don't set it as an attribute to allow module imports
            if name != "figure":
                module_globals[name] = value
            return value

        if name[:1].isupper():
            value = self._get_registry_attr(name)
            if value is not None:
                module_globals[name] = value
                return value

        raise AttributeError(f"module {self._package!r} has no attribute {name!r}")

    def iter_dir_names(self, module_globals: MutableMapping[str, Any]) -> list[str]:
        self._discover_modules(module_globals)
        names = set(module_globals)
        attr_map = self._get_attr_map(module_globals)
        if attr_map:
            names.update(attr_map)
        names.update(self._exceptions)
        return sorted(names)


class _UltraPlotModule(types.ModuleType):
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "figure":
            if isinstance(value, types.ModuleType):
                # Store the figure module separately to avoid clobbering the callable
                super().__setattr__("_figure_module", value)
                return
            elif callable(value) and not isinstance(value, types.ModuleType):
                # Check if the figure module has already been imported
                if "_figure_module" in self.__dict__:
                    # The figure module has been imported, so don't set the function
                    # This allows import ultraplot.figure to work
                    return
        super().__setattr__(name, value)


def install_module_proxy(module: Optional[types.ModuleType]) -> None:
    """
    Prevent lazy-loading names from being clobbered by submodule imports.
    """
    if module is None or isinstance(module, _UltraPlotModule):
        return
    module.__class__ = _UltraPlotModule
