#!/usr/bin/env python3
"""
Internal utilities.
"""

# Import statements
from importlib import import_module
from numbers import Integral, Real

import numpy as np

try:  # print debugging (used with internal modules)
    from icecream import ic
except ImportError:  # graceful fallback if IceCream isn't installed
    ic = lambda *args: print(*args)  # noqa: E731

from . import warnings

# Keyword-argument and alias resolution helpers live in ``kwargs.py``. Re-export
# them here so that the many ``from ..internals import _not_none`` (and friends)
# imports throughout the package keep working unchanged.
from .kwargs import (  # noqa: F401
    _alias_kwargs,
    _alias_maps,
    _get_aliases,
    _get_signature,
    _kwargs_to_args,
    _not_none,
    _pop_kwargs,
    _pop_params,
    _pop_props,
    _signature_cached,
    _INTERNAL_POP_PARAMS,
)


def _get_rc_matplotlib():
    from matplotlib import rcParams as rc_matplotlib

    return rc_matplotlib


_LAZY_ATTRS = {
    "benchmarks": ("benchmarks", None),
    "context": ("context", None),
    "docstring": ("docstring", None),
    "fonts": ("fonts", None),
    "guides": ("guides", None),
    "inputs": ("inputs", None),
    "labels": ("labels", None),
    "rcsetup": ("rcsetup", None),
    "versions": ("versions", None),
    "warnings": ("warnings", None),
    "_version_mpl": ("versions", "_version_mpl"),
    "_version_cartopy": ("versions", "_version_cartopy"),
    "UltraPlotWarning": ("warnings", "UltraPlotWarning"),
}


def _pop_rc(src, *, ignore_conflicts=True):
    """
    Pop the rc setting names and mode for a `~Configurator.context` block.
    """
    from . import rcsetup

    # NOTE: Must ignore deprected or conflicting rc params
    # NOTE: rc_mode == 2 applies only the updated params. A power user
    # could use ax.format(rc_mode=0) to re-apply all the current settings
    conflict_params = (
        "alpha",
        "color",
        "facecolor",
        "edgecolor",
        "linewidth",
        "basemap",
        "backend",
        "share",
        "span",
        "tight",
        "span",
    )

    kw = src.pop("rc_kw", None) or {}
    if "mode" in src:
        src["rc_mode"] = src.pop("mode")
        warnings._warn_ultraplot(
            "Keyword 'mode' was deprecated in v0.6. Please use 'rc_mode' instead."
        )
    mode = src.pop("rc_mode", None)
    mode = _not_none(mode, 2)  # only apply updated params by default
    for key, value in tuple(src.items()):
        name = rcsetup._rc_nodots.get(key, None)
        if ignore_conflicts and name in conflict_params:
            name = None  # former renamed settings
        if name is not None:
            kw[name] = src.pop(key)
    return kw, mode


def _translate_loc(loc, mode, *, default=None, **kwargs):
    """
    Translate the location string `loc` into a standardized form. The `mode`
    must be a string for which there is a :rcraw:`mode.loc` setting. Additional
    options can be added with keyword arguments.
    """
    from . import rcsetup

    # Create specific options dictionary
    # NOTE: This is not inside validators.py because it is also used to
    # validate various user-input locations.
    if mode == "align":
        loc_dict = rcsetup.ALIGN_LOCS
    elif mode == "panel":
        loc_dict = rcsetup.PANEL_LOCS
    elif mode == "legend":
        loc_dict = rcsetup.LEGEND_LOCS
    elif mode == "colorbar":
        loc_dict = rcsetup.COLORBAR_LOCS
    elif mode == "text":
        loc_dict = rcsetup.TEXT_LOCS
    else:
        raise ValueError(f"Invalid mode {mode!r}.")
    loc_dict = loc_dict.copy()
    loc_dict.update(kwargs)

    # Translate location
    if loc in (None, True):
        loc = default
    elif isinstance(loc, (str, Integral)):
        try:
            loc = loc_dict[loc]
        except KeyError:
            raise KeyError(
                f"Invalid {mode} location {loc!r}. Options are: "
                + ", ".join(map(repr, loc_dict))
                + "."
            )
    elif (
        mode == "legend"
        and np.iterable(loc)
        and len(loc) == 2
        and all(isinstance(l, Real) for l in loc)
    ):
        loc = tuple(loc)
    else:
        raise KeyError(f"Invalid {mode} location {loc!r}.")

    # Kludge / white lie
    # TODO: Implement 'best' colorbar location
    if mode == "colorbar" and loc == "best":
        loc = "lower right"

    return loc


def _translate_grid(b, key):
    """
    Translate an instruction to turn either major or minor gridlines on or off into a
    boolean and string applied to :rcraw:`axes.grid` and :rcraw:`axes.grid.which`.
    """
    rc_matplotlib = _get_rc_matplotlib()
    ob = rc_matplotlib["axes.grid"]
    owhich = rc_matplotlib["axes.grid.which"]

    # Instruction is to turn off gridlines
    if not b:
        # Gridlines are already off, or they are on for the particular
        # ones that we want to turn off. Instruct to turn both off.
        if (
            not ob
            or key == "grid"
            and owhich == "major"
            or key == "gridminor"
            and owhich == "minor"
        ):
            which = "both"  # disable both sides
        # Gridlines are currently on for major and minor ticks, so we
        # instruct to turn on gridlines for the one we *don't* want off
        elif owhich == "both":  # and ob is True, as already tested
            # if gridminor=False, enable major, and vice versa
            b = True
            which = "major" if key == "gridminor" else "minor"
        # Gridlines are on for the ones that we *didn't* instruct to
        # turn off, and off for the ones we do want to turn off. This
        # just re-asserts the ones that are already on.
        else:
            b = True
            which = owhich

    # Instruction is to turn on gridlines
    else:
        # Gridlines are already both on, or they are off only for the
        # ones that we want to turn on. Turn on gridlines for both.
        if (
            owhich == "both"
            or key == "grid"
            and owhich == "minor"
            or key == "gridminor"
            and owhich == "major"
        ):
            which = "both"
        # Gridlines are off for both, or off for the ones that we
        # don't want to turn on. We can just turn on these ones.
        else:
            which = owhich

    return b, which


def _resolve_lazy(name):
    module_name, attr = _LAZY_ATTRS[name]
    module = import_module(f".{module_name}", __name__)
    value = module if attr is None else getattr(module, attr)
    globals()[name] = value
    return value


def __getattr__(name):
    if name in _LAZY_ATTRS:
        return _resolve_lazy(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    names = set(globals())
    names.update(_LAZY_ATTRS)
    return sorted(names)
