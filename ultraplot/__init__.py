#!/usr/bin/env python3
"""
A succinct matplotlib wrapper for making beautiful, publication-quality graphics.
"""
from __future__ import annotations

import sys
from functools import wraps
from pathlib import Path
from typing import Optional

from ._lazy import LazyLoader, install_module_proxy

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
        _patch_funcanimation_draw_idle()
        success = True
    finally:
        if success:
            _SETUP_DONE = True
        _SETUP_RUNNING = False


def setup(eager: Optional[bool] = None) -> None:
    """
    Initialize registries and optionally import the public API eagerly.
    """
    _setup()
    if eager is None:
        from .config import rc

        eager = bool(rc["ultraplot.eager_import"])
    if eager:
        _LOADER.load_all(globals())


def _patch_funcanimation_draw_idle():
    try:
        import matplotlib.animation as mpl_animation
    except Exception:
        return

    if getattr(mpl_animation.FuncAnimation, "_ultra_draw_idle_patched", False):
        return

    orig_init = mpl_animation.FuncAnimation.__init__
    orig_stop = getattr(mpl_animation.FuncAnimation, "_stop", None)

    def _install_draw_idle(self, fig):
        if fig is None or not hasattr(fig, "_layout_dirty"):
            return
        canvas = getattr(fig, "canvas", None)
        if canvas is None or not hasattr(canvas, "draw_idle"):
            return

        count = getattr(canvas, "_ultra_draw_idle_count", 0)
        if count == 0:
            canvas._ultra_draw_idle_orig = canvas.draw_idle

            def draw_idle(*args, **kwargs):
                return canvas.draw(*args, **kwargs)

            canvas.draw_idle = draw_idle
        canvas._ultra_draw_idle_count = count + 1

        import weakref

        canvas_ref = weakref.ref(canvas)

        def restore():
            canvas = canvas_ref()
            if canvas is None:
                return
            count = getattr(canvas, "_ultra_draw_idle_count", 0)
            if count <= 1:
                orig = getattr(canvas, "_ultra_draw_idle_orig", None)
                if orig is not None:
                    canvas.draw_idle = orig
                    delattr(canvas, "_ultra_draw_idle_orig")
                canvas._ultra_draw_idle_count = 0
            else:
                canvas._ultra_draw_idle_count = count - 1

        self._ultra_restore_draw_idle = restore
        self._ultra_draw_idle_finalizer = weakref.finalize(self, restore)

    @wraps(orig_init)
    def __init__(self, fig, *args, **kwargs):
        orig_init(self, fig, *args, **kwargs)
        _install_draw_idle(self, fig)

    mpl_animation.FuncAnimation.__init__ = __init__

    if orig_stop is not None:

        @wraps(orig_stop)
        def _stop(self, *args, **kwargs):
            restore = getattr(self, "_ultra_restore_draw_idle", None)
            if restore is not None:
                restore()
                self._ultra_restore_draw_idle = None
            return orig_stop(self, *args, **kwargs)

        mpl_animation.FuncAnimation._stop = _stop

    mpl_animation.FuncAnimation._ultra_draw_idle_patched = True


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


_LOADER: LazyLoader = LazyLoader(
    package=__name__,
    package_path=Path(__file__).resolve().parent,
    exceptions=_LAZY_LOADING_EXCEPTIONS,
    setup_callback=_setup,
    registry_attr_callback=_get_registry_attr,
    registry_build_callback=_build_registry_map,
    registry_names_callback=lambda: _REGISTRY_ATTRS,
)


def __getattr__(name):
    # If the name is already in globals, return it immediately
    # (Prevents re-running logic for already loaded attributes)
    if name in globals():
        return globals()[name]

    if name == "pytest_plugins":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    # Priority 2: Core metadata
    if name in {"__version__", "version", "name", "__all__"}:
        if name == "__all__":
            val = _LOADER.load_all(globals())
            globals()["__all__"] = val
            return val
        return globals().get(name)

    # Priority 3: Special handling for figure
    if name == "figure":
        # Special handling for figure to allow module imports
        import inspect
        import sys

        # Check if this is a module import by looking at the call stack
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            if caller_frame:
                # Check if the caller is likely the import system
                caller_code = caller_frame.f_code
                # Check if this is a module import
                is_import = (
                    "importlib" in caller_code.co_filename
                    or caller_code.co_name
                    in ("_handle_fromlist", "_find_and_load", "_load_unlocked")
                    or "_bootstrap" in caller_code.co_filename
                )

                # Also check if the caller is a module-level import statement
                if not is_import and caller_code.co_name == "<module>":
                    try:
                        source_lines = inspect.getframeinfo(caller_frame).code_context
                        if source_lines and any(
                            "import" in line and "figure" in line
                            for line in source_lines
                        ):
                            is_import = True
                    except Exception:
                        pass

                if is_import:
                    # This is likely a module import, let Python handle it
                    # Return early to avoid delegating to the lazy loader
                    raise AttributeError(
                        f"module {__name__!r} has no attribute {name!r}"
                    )
            # If no caller frame, delegate to the lazy loader
            return _LOADER.get_attr(name, globals())
        except Exception as e:
            if not (
                isinstance(e, AttributeError)
                and str(e) == f"module {__name__!r} has no attribute {name!r}"
            ):
                return _LOADER.get_attr(name, globals())
            raise
        finally:
            del frame

    # Priority 4: External dependencies
    if name == "pyplot":
        import matplotlib.pyplot as plt

        globals()[name] = plt
        return plt
    if name == "cartopy":
        try:
            import cartopy as ctp
        except ImportError as exc:
            raise AttributeError(
                f"module {__name__!r} has no attribute {name!r}"
            ) from exc
        globals()[name] = ctp
        return ctp
    if name == "basemap":
        try:
            import mpl_toolkits.basemap as basemap
        except ImportError as exc:
            raise AttributeError(
                f"module {__name__!r} has no attribute {name!r}"
            ) from exc
        globals()[name] = basemap
        return basemap

    return _LOADER.get_attr(name, globals())


def __dir__():
    return _LOADER.iter_dir_names(globals())


# Prevent "import ultraplot.figure" from clobbering the top-level callable.
install_module_proxy(sys.modules.get(__name__))
