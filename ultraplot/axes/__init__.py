#!/usr/bin/env python3
"""
The various axes classes used throughout ultraplot.
"""

import matplotlib.projections as mproj

from ..internals import context
from .base import Axes  # noqa: F401
from .cartesian import CartesianAxes
from .container import ExternalAxesContainer  # noqa: F401
from .geo import (
    GeoAxes,  # noqa: F401
    _BasemapAxes,
    _CartopyAxes,
)
from .plot import PlotAxes  # noqa: F401
from .polar import PolarAxes
from .shared import _SharedAxes  # noqa: F401
from .three import ThreeAxes  # noqa: F401

_ASTRO_AXES_CLASS = None
_ASTROPY_WCS_TYPES = ()
_ASTRO_LOADED = False

# Prevent importing module names and set order of appearance for objects
__all__ = [
    "Axes",
    "PlotAxes",
    "CartesianAxes",
    "PolarAxes",
    "GeoAxes",
    "ThreeAxes",
    "ExternalAxesContainer",
]

# Register projections with package prefix to avoid conflicts
# NOTE: We integrate with cartopy and basemap rather than using matplotlib's
# native projection system. Therefore axes names are not part of public API.
_cls_dict = {}  # track valid names


def _refresh_cls_table():
    global _cls_table
    _cls_table = "\n".join(
        " "
        + key
        + " " * (max(map(len, _cls_dict)) - len(key) + 7)
        + ("GeoAxes" if cls.__name__[:1] == "_" else cls.__name__)
        for key, cls in _cls_dict.items()
    )


def _register_projection_class(_cls):
    for _name in (_cls._name, *_cls._name_aliases):
        with context._state_context(_cls, name="ultraplot_" + _name):
            if "ultraplot_" + _name not in mproj.get_projection_names():
                mproj.register_projection(_cls)
            _cls_dict[_name] = _cls
    _refresh_cls_table()


for _cls in (CartesianAxes, PolarAxes, _CartopyAxes, _BasemapAxes, ThreeAxes):
    _register_projection_class(_cls)


def _load_astro_axes():
    global _ASTROPY_WCS_TYPES, _ASTRO_AXES_CLASS, _ASTRO_LOADED
    if _ASTRO_LOADED:
        return _ASTRO_AXES_CLASS
    try:
        from .astro import ASTROPY_WCS_TYPES as _types, AstroAxes as _astro_axes
    except ImportError as exc:
        raise ImportError(
            "AstroAxes support requires astropy. Install it with "
            '`pip install "ultraplot[astro]"` or `pip install astropy`.'
        ) from exc

    _ASTRO_LOADED = True
    _ASTROPY_WCS_TYPES = _types
    _ASTRO_AXES_CLASS = _astro_axes
    if "AstroAxes" not in __all__:
        __all__.append("AstroAxes")
    _register_projection_class(_ASTRO_AXES_CLASS)
    return _ASTRO_AXES_CLASS


def get_astro_axes_class(*, load=False):
    if load:
        _load_astro_axes()
    return _ASTRO_AXES_CLASS


def get_astropy_wcs_types(*, load=False):
    if load:
        _load_astro_axes()
    return _ASTROPY_WCS_TYPES


def __getattr__(name):
    if name == "AstroAxes":
        return get_astro_axes_class(load=True)
    if name == "ASTROPY_WCS_TYPES":
        return get_astropy_wcs_types(load=True)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
