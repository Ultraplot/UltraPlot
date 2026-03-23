#!/usr/bin/env python3
"""
A succinct matplotlib wrapper for making beautiful, publication-quality graphics.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ._lazy import LazyLoader, install_module_proxy

name = "ultraplot"

if TYPE_CHECKING:
    import matplotlib.pyplot as pyplot

    try:
        import cartopy as cartopy
        from cartopy.crs import (
            AlbersEqualArea,
            AzimuthalEquidistant,
            EckertI,
            EckertII,
            EckertIII,
            EckertIV,
            EckertV,
            EckertVI,
            EqualEarth,
            EquidistantConic,
            EuroPP,
            Geostationary,
            Gnomonic,
            InterruptedGoodeHomolosine,
            LambertAzimuthalEqualArea,
            LambertConformal,
            LambertCylindrical,
            Mercator,
            Miller,
            Mollweide,
            NearsidePerspective,
            NorthPolarStereo,
            OSGB,
            OSNI,
            Orthographic,
            PlateCarree,
            Robinson,
            RotatedPole,
            Sinusoidal,
            SouthPolarStereo,
            Stereographic,
            TransverseMercator,
            UTM,
        )
    except ModuleNotFoundError:
        cartopy: Any
        AlbersEqualArea: Any
        AzimuthalEquidistant: Any
        EckertI: Any
        EckertII: Any
        EckertIII: Any
        EckertIV: Any
        EckertV: Any
        EckertVI: Any
        EqualEarth: Any
        EquidistantConic: Any
        EuroPP: Any
        Geostationary: Any
        Gnomonic: Any
        InterruptedGoodeHomolosine: Any
        LambertAzimuthalEqualArea: Any
        LambertConformal: Any
        LambertCylindrical: Any
        Mercator: Any
        Miller: Any
        Mollweide: Any
        NearsidePerspective: Any
        NorthPolarStereo: Any
        OSGB: Any
        OSNI: Any
        Orthographic: Any
        PlateCarree: Any
        Robinson: Any
        RotatedPole: Any
        Sinusoidal: Any
        SouthPolarStereo: Any
        Stereographic: Any
        TransverseMercator: Any
        UTM: Any

    try:
        import mpl_toolkits.basemap as basemap
    except ImportError:
        basemap: Any

    from matplotlib import rcParams as rc_matplotlib
    from matplotlib.colors import (
        LogNorm,
        NoNorm,
        Normalize,
        PowerNorm,
        SymLogNorm,
        TwoSlopeNorm,
    )
    from matplotlib.dates import (
        AutoDateFormatter,
        AutoDateLocator,
        ConciseDateFormatter,
        DateFormatter,
        DayLocator,
        HourLocator,
        MicrosecondLocator,
        MinuteLocator,
        MonthLocator,
        SecondLocator,
        WeekdayLocator,
        YearLocator,
    )
    from matplotlib.projections.polar import ThetaFormatter, ThetaLocator
    from matplotlib.scale import AsinhScale, FuncScaleLog
    from matplotlib.ticker import (
        AutoLocator,
        AutoMinorLocator,
        EngFormatter,
        FixedLocator,
        FormatStrFormatter,
        FuncFormatter,
        LinearLocator,
        LogFormatterMathtext,
        LogFormatterSciNotation,
        LogLocator,
        LogitFormatter,
        LogitLocator,
        MaxNLocator,
        MultipleLocator,
        NullFormatter,
        NullLocator,
        PercentFormatter,
        ScalarFormatter,
        StrMethodFormatter,
        SymmetricalLogLocator,
    )

    from . import (
        axes,
        colorbar,
        colors,
        config,
        constructor,
        demos,
        externals,
        gridspec,
        internals,
        legend,
        proj,
        scale,
        tests,
        text,
        ticker,
        ui,
        ultralayout,
        utils,
    )
    from .axes.base import Axes
    from .axes.cartesian import CartesianAxes
    from .axes.container import ExternalAxesContainer
    from .axes.geo import GeoAxes
    from .axes.plot import PlotAxes
    from .axes.polar import PolarAxes
    from .axes.three import ThreeAxes
    from .colors import (
        ColorDatabase,
        ColormapDatabase,
        ContinuousColormap,
        DiscreteColormap,
        DiscreteNorm,
        DivergingNorm,
        PerceptualColormap,
        SegmentedNorm,
        _cmap_database as colormaps,
    )
    from .config import (
        Configurator,
        config_inline_backend,
        rc,
        register_cmaps,
        register_colors,
        register_cycles,
        register_fonts,
        use_style,
    )
    from .constructor import (
        FORMATTERS,
        LOCATORS,
        NORMS,
        PROJS,
        SCALES,
        Colormap,
        Cycle,
        Formatter,
        Locator,
        Norm,
        Proj,
        Scale,
    )
    from .demos import (
        show_channels,
        show_cmaps,
        show_colors,
        show_colorspaces,
        show_cycles,
        show_fonts,
    )
    from .figure import Figure
    from .gridspec import GridSpec, SubplotGrid
    from .internals import rcsetup, warnings
    from .internals.rcsetup import rc_ultraplot
    from .internals.warnings import (
        LinearSegmentedColormap,
        LinearSegmentedNorm,
        ListedColormap,
        PerceptuallyUniformColormap,
        RcConfigurator,
        inline_backend_fmt,
        saturate,
        shade,
    )
    from .legend import GeometryEntry, Legend, LegendEntry
    from .proj import (
        Aitoff,
        Hammer,
        KavrayskiyVII,
        NorthPolarAzimuthalEquidistant,
        NorthPolarGnomonic,
        NorthPolarLambertAzimuthalEqualArea,
        SouthPolarAzimuthalEquidistant,
        SouthPolarGnomonic,
        SouthPolarLambertAzimuthalEqualArea,
        WinkelTripel,
    )
    from . import proj as crs
    from .scale import (
        CutoffScale,
        ExpScale,
        FuncScale,
        InverseScale,
        LinearScale,
        LogScale,
        LogitScale,
        MercatorLatitudeScale,
        PowerScale,
        SineLatitudeScale,
        SymmetricalLogScale,
    )
    from .text import CurvedText
    from .ticker import (
        AutoCFDatetimeFormatter,
        AutoCFDatetimeLocator,
        AutoFormatter,
        CFDatetimeFormatter,
        DegreeFormatter,
        DegreeLocator,
        DiscreteLocator,
        FracFormatter,
        IndexFormatter,
        IndexLocator,
        LatitudeFormatter,
        LatitudeLocator,
        LongitudeFormatter,
        LongitudeLocator,
        SciFormatter,
        SigFigFormatter,
        SimpleFormatter,
    )
    from .ui import (
        close,
        figure,
        ioff,
        ion,
        isinteractive,
        show,
        subplot,
        subplots,
        switch_backend,
    )
    from .ultralayout import (
        ColorbarLayoutSolver,
        UltraLayoutSolver,
        compute_ultra_positions,
        get_grid_positions_ultra,
        is_orthogonal_layout,
    )
    from .utils import (
        arange,
        check_for_update,
        edges,
        edges2d,
        get_colors,
        scale_luminance,
        scale_saturation,
        set_alpha,
        set_hue,
        set_luminance,
        set_saturation,
        shift_hue,
        to_hex,
        to_rgb,
        to_rgba,
        to_xyz,
        to_xyza,
        units,
    )

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
