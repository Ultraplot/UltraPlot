#!/usr/bin/env python3
"""
A succinct matplotlib wrapper for making beautiful, publication-quality graphics.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ._lazy import LazyLoader, install_module_proxy

if TYPE_CHECKING:
    # These imports are never executed at runtime, so they have zero effect on
    # import performance. They exist solely so that type checkers (pyright, mypy)
    # can resolve names that are otherwise provided by the lazy loader at runtime.
    #
    # Keep this block in sync with _LAZY_LOADING_EXCEPTIONS and every submodule's
    # __all__ — that is the only maintenance burden.
    import matplotlib.pyplot as pyplot

    from .axes import Axes as Axes
    from .axes import CartesianAxes as CartesianAxes
    from .axes import ExternalAxesContainer as ExternalAxesContainer
    from .axes import GeoAxes as GeoAxes
    from .axes import PlotAxes as PlotAxes
    from .axes import PolarAxes as PolarAxes
    from .axes import ThreeAxes as ThreeAxes
    from .colors import ColormapDatabase as ColormapDatabase
    from .colors import ColorDatabase as ColorDatabase
    from .colors import ContinuousColormap as ContinuousColormap
    from .colors import DiscreteColormap as DiscreteColormap
    from .colors import DiscreteNorm as DiscreteNorm
    from .colors import DivergingNorm as DivergingNorm
    from .colors import LinearSegmentedColormap as LinearSegmentedColormap
    from .colors import LinearSegmentedNorm as LinearSegmentedNorm
    from .colors import ListedColormap as ListedColormap
    from .colors import PerceptualColormap as PerceptualColormap
    from .colors import PerceptuallyUniformColormap as PerceptuallyUniformColormap
    from .colors import SegmentedNorm as SegmentedNorm
    from .colors import _cmap_database as colormaps
    from .config import Configurator as Configurator
    from .config import rc as rc
    from .config import rc_matplotlib as rc_matplotlib
    from .config import rc_ultraplot as rc_ultraplot
    from .config import use_style as use_style
    from .constructor import Colormap as Colormap
    from .constructor import Colors as Colors
    from .constructor import Cycle as Cycle
    from .constructor import Formatter as Formatter
    from .constructor import FORMATTERS as FORMATTERS
    from .constructor import Locator as Locator
    from .constructor import LOCATORS as LOCATORS
    from .constructor import Norm as Norm
    from .constructor import NORMS as NORMS
    from .constructor import Proj as Proj
    from .constructor import PROJS as PROJS
    from .constructor import Scale as Scale
    from .constructor import SCALES as SCALES
    from .demos import show_channels as show_channels
    from .demos import show_cmaps as show_cmaps
    from .demos import show_colorspaces as show_colorspaces
    from .demos import show_colors as show_colors
    from .demos import show_cycles as show_cycles
    from .demos import show_fonts as show_fonts
    from .figure import Figure as Figure
    from .gridspec import GridSpec as GridSpec
    from .gridspec import SubplotGrid as SubplotGrid
    from .proj import Aitoff as Aitoff
    from .proj import Hammer as Hammer
    from .proj import KavrayskiyVII as KavrayskiyVII
    from .proj import NorthPolarAzimuthalEquidistant as NorthPolarAzimuthalEquidistant
    from .proj import NorthPolarGnomonic as NorthPolarGnomonic
    from .proj import NorthPolarLambertAzimuthalEqualArea as NorthPolarLambertAzimuthalEqualArea
    from .proj import SouthPolarAzimuthalEquidistant as SouthPolarAzimuthalEquidistant
    from .proj import SouthPolarGnomonic as SouthPolarGnomonic
    from .proj import SouthPolarLambertAzimuthalEqualArea as SouthPolarLambertAzimuthalEqualArea
    from .proj import WinkelTripel as WinkelTripel
    from .scale import CutoffScale as CutoffScale
    from .scale import ExpScale as ExpScale
    from .scale import FuncScale as FuncScale
    from .scale import InverseScale as InverseScale
    from .scale import LinearScale as LinearScale
    from .scale import LogitScale as LogitScale
    from .scale import LogScale as LogScale
    from .scale import MercatorLatitudeScale as MercatorLatitudeScale
    from .scale import PowerScale as PowerScale
    from .scale import SineLatitudeScale as SineLatitudeScale
    from .scale import SymmetricalLogScale as SymmetricalLogScale
    from .text import CurvedText as CurvedText
    from .ticker import AutoCFDatetimeFormatter as AutoCFDatetimeFormatter
    from .ticker import AutoCFDatetimeLocator as AutoCFDatetimeLocator
    from .ticker import AutoFormatter as AutoFormatter
    from .ticker import CFDatetimeFormatter as CFDatetimeFormatter
    from .ticker import DegreeFormatter as DegreeFormatter
    from .ticker import DegreeLocator as DegreeLocator
    from .ticker import DiscreteLocator as DiscreteLocator
    from .ticker import FracFormatter as FracFormatter
    from .ticker import IndexFormatter as IndexFormatter
    from .ticker import IndexLocator as IndexLocator
    from .ticker import LatitudeFormatter as LatitudeFormatter
    from .ticker import LatitudeLocator as LatitudeLocator
    from .ticker import LongitudeFormatter as LongitudeFormatter
    from .ticker import LongitudeLocator as LongitudeLocator
    from .ticker import SciFormatter as SciFormatter
    from .ticker import SigFigFormatter as SigFigFormatter
    from .ticker import SimpleFormatter as SimpleFormatter
    from .ui import close as close
    from .ui import figure as figure
    from .ui import ioff as ioff
    from .ui import ion as ion
    from .ui import isinteractive as isinteractive
    from .ui import show as show
    from .ui import subplot as subplot
    from .ui import subplots as subplots
    from .ui import switch_backend as switch_backend
    from .utils import arange as arange
    from .utils import check_for_update as check_for_update
    from .utils import edges as edges
    from .utils import edges2d as edges2d
    from .utils import get_colors as get_colors
    from .utils import saturate as saturate
    from .utils import scale_luminance as scale_luminance
    from .utils import scale_saturation as scale_saturation
    from .utils import set_alpha as set_alpha
    from .utils import set_hue as set_hue
    from .utils import set_luminance as set_luminance
    from .utils import set_saturation as set_saturation
    from .utils import shade as shade
    from .utils import shift_hue as shift_hue
    from .utils import to_hex as to_hex
    from .utils import to_rgb as to_rgb
    from .utils import to_rgba as to_rgba
    from .utils import to_xyz as to_xyz
    from .utils import to_xyza as to_xyza
    from .utils import units as units

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

        eager = bool(rc["ultraplot.eager_import"])
    if eager:
        _LOADER.load_all(globals())


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
