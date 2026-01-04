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

# Exceptions to the automated lazy loading
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
    "tests": ("tests", None),
    "rcsetup": ("internals", "rcsetup"),
    "warnings": ("internals", "warnings"),
    "Figure": ("figure", "Figure"),
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


def _discover_modules():
    global _ATTR_MAP
    if _ATTR_MAP is not None:
        return

    attr_map = {}
    base = Path(__file__).resolve().parent

    for path in base.glob("*.py"):
        if path.name.startswith("_") or path.name == "setup.py":
            continue
        module_name = path.stem
        names = _parse_all(path)
        if names:
            if len(names) == 1:
                attr_map[module_name] = (module_name, names[0])
            else:
                for name in names:
                    attr_map[name] = (module_name, name)

    for path in base.iterdir():
        if not path.is_dir() or path.name.startswith("_") or path.name == "tests":
            continue
        if (path / "__init__.py").is_file():
            module_name = path.name
            names = _parse_all(path / "__init__.py")
            if names:
                for name in names:
                    attr_map[name] = (module_name, name)

            attr_map[module_name] = (module_name, None)

    _ATTR_MAP = attr_map


def _expose_module(module_name):
    if module_name in _EXPOSED_MODULES:
        return _import_module(module_name)
    module = _import_module(module_name)
    names = getattr(module, "__all__", None)
    if names is None:
        names = [name for name in dir(module) if not name.startswith("_")]
    for name in names:
        globals()[name] = getattr(module, name)
    _EXPOSED_MODULES.add(module_name)
    return module


def _setup():
    global _SETUP_DONE, _SETUP_RUNNING
    if _SETUP_DONE or _SETUP_RUNNING:
        return
    _SETUP_RUNNING = True
    success = False
    try:
        from .config import (
            rc,
            rc_matplotlib,
            rc_ultraplot,
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
        for key in (
            "cycle",
            "cmap.sequential",
            "cmap.diverging",
            "cmap.cyclic",
            "cmap.qualitative",
        ):
            try:
                rc[key] = rc[key]
            except ValueError as err:
                warnings._warn_ultraplot(f"Invalid user rc file setting: {err}")
                rc[key] = "Greys"

        rcsetup.VALIDATE_REGISTERED_COLORS = True
        for src in (rc_ultraplot, rc_matplotlib):
            for key in src:
                if "color" not in key:
                    continue
                try:
                    src[key] = src[key]
                except ValueError as err:
                    warnings._warn_ultraplot(f"Invalid user rc file setting: {err}")
                    src[key] = "black"

        if rc["ultraplot.check_for_latest_version"]:
            from .utils import check_for_update

            check_for_update("ultraplot")
        success = True
    finally:
        if success:
            _SETUP_DONE = True
        _SETUP_RUNNING = False


def _resolve_extra(name):
    module_name, attr = _LAZY_LOADING_EXCEPTIONS[name]
    module = _import_module(module_name)
    value = module if attr is None else getattr(module, attr)
    globals()[name] = value
    return value


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
    if not _REGISTRY_ATTRS:
        return None
    return _REGISTRY_ATTRS.get(name)


def _load_all():
    global _EAGER_DONE
    if _EAGER_DONE:
        try:
            return sorted(globals()["__all__"])
        except KeyError:
            pass
    _EAGER_DONE = True
    _setup()
    from .internals.benchmarks import _benchmark

    _discover_modules()
    names = set(_ATTR_MAP.keys())

    for name in names:
        try:
            __getattr__(name)
        except AttributeError:
            pass

    names.update(_LAZY_LOADING_EXCEPTIONS.keys())
    with _benchmark("registries"):
        _build_registry_map()
    if _REGISTRY_ATTRS:
        names.update(_REGISTRY_ATTRS)
    names.update(
        {"__version__", "version", "name", "setup", "pyplot", "cartopy", "basemap"}
    )
    _EAGER_DONE = True
    return sorted(names)


def _get_rc_eager():
    try:
        from .config import rc
    except Exception:
        return False
    try:
        return bool(rc["ultraplot.eager_import"])
    except Exception:
        return False


def _maybe_eager_import():
    if _EAGER_DONE:
        return
    if _get_rc_eager():
        _load_all()


def setup(*, eager=None):
    """
    Initialize ultraplot and optionally import the public API eagerly.
    """
    _setup()
    if eager is None:
        eager = _get_rc_eager()
    if eager:
        _load_all()


def __getattr__(name):
    if name == "pytest_plugins":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    if name in {"__version__", "version", "name", "__all__"}:
        if name == "__all__":
            value = _load_all()
            globals()["__all__"] = value
            return value
        return globals()[name]

    if name == "pyplot":
        import matplotlib.pyplot as pyplot

        globals()[name] = pyplot
        return pyplot
    if name == "cartopy":
        try:
            import cartopy
        except ImportError as err:
            raise AttributeError(
                f"module {__name__!r} has no attribute {name!r}"
            ) from err
        globals()[name] = cartopy
        return cartopy
    if name == "basemap":
        try:
            from mpl_toolkits import basemap
        except ImportError as err:
            raise AttributeError(
                f"module {__name__!r} has no attribute {name!r}"
            ) from err
        globals()[name] = basemap
        return basemap

    if name in _LAZY_LOADING_EXCEPTIONS:
        _setup()
        _maybe_eager_import()
        return _resolve_extra(name)

    _discover_modules()
    if _ATTR_MAP and name in _ATTR_MAP:
        module_name, attr_name = _ATTR_MAP[name]
        _setup()
        _maybe_eager_import()

        module = _import_module(module_name)
        value = getattr(module, attr_name) if attr_name else module
        globals()[name] = value
        return value

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
