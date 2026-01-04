#!/usr/bin/env python3
"""
A succinct matplotlib wrapper for making beautiful, publication-quality graphics.
"""
from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

name = "ultraplot"

try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"

version = __version__

_SETUP_DONE = False
_SETUP_RUNNING = False
_EAGER_DONE = False
_EXPOSED_MODULES = set()
_ATTR_MAP = None
_REGISTRY_ATTRS = None

_LAZY_LOADING_EXCEPTIONS = {
    "constructor": ("constructor", None),
    "crs": ("proj", None),
    "colormaps": ("colors", "_cmap_database"),
    "check_for_update": ("utils", "check_for_update"),
    "NORMS": ("constructor", "NORMS"),
    "LOCATORS": ("constructor", "LOCATORS"),
    "FORMATTERS": ("constructor", "FORMATTERS"),
    "SCALES": ("constructor", "SCALES"),
    "PROJS": ("constructor", "PROJS"),
    "internals": ("internals", None),
    "externals": ("externals", None),
    "Proj": ("constructor", "Proj"),
    "tests": ("tests", None),
    "rcsetup": ("internals", "rcsetup"),
    "warnings": ("internals", "warnings"),
    "figure": ("ui", "figure"),  # Points to the FUNCTION in ui.py
    "Figure": ("figure", "Figure"),  # Points to the CLASS in figure.py
    "Colormap": ("constructor", "Colormap"),
    "Cycle": ("constructor", "Cycle"),
    "Norm": ("constructor", "Norm"),
}


def _import_module(module_name):
    return import_module(f".{module_name}", __name__)


def _parse_all(path):
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


def _resolve_extra(name):
    module_name, attr = _LAZY_LOADING_EXCEPTIONS[name]
    module = _import_module(module_name)
    value = module if attr is None else getattr(module, attr)
    # This binds the resolved object (The Class) to the global name
    globals()[name] = value
    return value


def _setup():
    global _SETUP_DONE, _SETUP_RUNNING
    if _SETUP_DONE or _SETUP_RUNNING:
        return
    _SETUP_RUNNING = True
    success = False
    try:
        from .config import (
            rc,
            register_cmaps,
            register_colors,
            register_cycles,
            register_fonts,
        )
        from .internals import rcsetup, warnings
        from .internals.benchmarks import _benchmark

        with _benchmark("cmaps"):
            register_cmaps(default=True)
        with _benchmark("cycles"):
            register_cycles(default=True)
        with _benchmark("colors"):
            register_colors(default=True)
        with _benchmark("fonts"):
            register_fonts(default=True)

        rcsetup.VALIDATE_REGISTERED_CMAPS = True
        rcsetup.VALIDATE_REGISTERED_COLORS = True

        if rc["ultraplot.check_for_latest_version"]:
            from .utils import check_for_update

            check_for_update("ultraplot")
        success = True
    finally:
        if success:
            _SETUP_DONE = True
        _SETUP_RUNNING = False


def _build_registry_map():
    global _REGISTRY_ATTRS
    if _REGISTRY_ATTRS is not None:
        return
    from .constructor import FORMATTERS, LOCATORS, NORMS, PROJS, SCALES

    registry = {}
    for src in (NORMS, LOCATORS, FORMATTERS, SCALES, PROJS):
        for _, cls in src.items():
            if isinstance(cls, type):
                registry[cls.__name__] = cls
    _REGISTRY_ATTRS = registry


def _get_registry_attr(name):
    _build_registry_map()
    return _REGISTRY_ATTRS.get(name) if _REGISTRY_ATTRS else None


def _load_all():
    global _EAGER_DONE
    if _EAGER_DONE:
        return sorted(globals().get("__all__", []))
    _EAGER_DONE = True
    _setup()
    _discover_modules()
    names = set(_ATTR_MAP.keys())
    for name in names:
        try:
            __getattr__(name)
        except AttributeError:
            pass
    names.update(_LAZY_LOADING_EXCEPTIONS.keys())
    _build_registry_map()
    if _REGISTRY_ATTRS:
        names.update(_REGISTRY_ATTRS)
    names.update(
        {"__version__", "version", "name", "setup", "pyplot", "cartopy", "basemap"}
    )
    return sorted(names)


def _discover_modules():
    global _ATTR_MAP
    if _ATTR_MAP is not None:
        return

    attr_map = {}
    base = Path(__file__).resolve().parent

    # PROTECT 'figure' from auto-discovery
    # We must explicitly ignore the file 'figure.py' so it doesn't
    # populate the attribute map as a module.
    protected = set(_LAZY_LOADING_EXCEPTIONS.keys())
    protected.add("figure")

    for path in base.glob("*.py"):
        if path.name.startswith("_") or path.name == "setup.py":
            continue
        module_name = path.stem

        # If the filename is 'figure', don't let it be an attribute
        if module_name in protected:
            continue

        names = _parse_all(path)
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
            names = _parse_all(path / "__init__.py")
            if names:
                for name in names:
                    if name not in protected:
                        attr_map[name] = (module_name, name)
            attr_map[module_name] = (module_name, None)

    # Hard force-remove figure from discovery map
    attr_map.pop("figure", None)
    _ATTR_MAP = attr_map


def __getattr__(name):
    # If the name is already in globals, return it immediately
    # (Prevents re-running logic for already loaded attributes)
    if name in globals():
        return globals()[name]

    if name == "pytest_plugins":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    # Priority 1: Check Explicit Exceptions FIRST (This catches 'figure')
    if name in _LAZY_LOADING_EXCEPTIONS:
        _setup()
        return _resolve_extra(name)

    # Priority 2: Core metadata
    if name in {"__version__", "version", "name", "__all__"}:
        if name == "__all__":
            val = _load_all()
            globals()["__all__"] = val
            return val
        return globals().get(name)

    # Priority 3: External dependencies
    if name == "pyplot":
        import matplotlib.pyplot as plt

        globals()[name] = plt
        return plt

    # Priority 4: Automated discovery
    _discover_modules()
    if _ATTR_MAP and name in _ATTR_MAP:
        module_name, attr_name = _ATTR_MAP[name]
        _setup()
        module = _import_module(module_name)
        value = getattr(module, attr_name) if attr_name else module
        globals()[name] = value
        return value

    # Priority 5: Registry (Capital names)
    if name[:1].isupper():
        value = _get_registry_attr(name)
        if value is not None:
            globals()[name] = value
            return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    _discover_modules()
    names = set(globals())
    if _ATTR_MAP:
        names.update(_ATTR_MAP)
    names.update(_LAZY_LOADING_EXCEPTIONS)
    return sorted(names)


# Prevent "import ultraplot.figure" from clobbering the top-level callable.
import sys
import types


class _UltraPlotModule(types.ModuleType):
    def __setattr__(self, name, value):
        if name == "figure" and isinstance(value, types.ModuleType):
            super().__setattr__("_figure_module", value)
            return
        super().__setattr__(name, value)


_module = sys.modules.get(__name__)
if _module is not None and not isinstance(_module, _UltraPlotModule):
    _module.__class__ = _UltraPlotModule
