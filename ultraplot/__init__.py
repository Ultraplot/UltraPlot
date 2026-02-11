#!/usr/bin/env python3
"""
A succinct matplotlib wrapper for making beautiful, publication-quality graphics.
"""

from __future__ import annotations

import sys
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
    "Locator": ("constructor", "Locator"),
    "Scale": ("constructor", "Scale"),
    "Formatter": ("constructor", "Formatter"),
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
        from .internals import (
            fonts as _fonts,  # noqa: F401 - ensure mathtext override is active
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


def setup(eager: Optional[bool] = None) -> None:
    """
    Initialize registries and optionally import the public API eagerly.
    """
    _setup()
    if eager is None:
        from .config import rc

# Validate color names now that colors are registered
# NOTE: This updates all settings with 'color' in name (harmless if it's not a color)
rcsetup.VALIDATE_REGISTERED_COLORS = True
rc.sync()  # triggers validation

from .colors import _cmap_database as colormaps
from .utils import check_for_update

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
