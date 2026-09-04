#!/usr/bin/env python
"""
An axes used to jointly format Cartesian and polar axes.
"""

# NOTE: We could define these in base.py but idea is projection-specific formatters
# should never be defined on the base class. Might add to this class later anyway.
import functools

import numpy as np

from ..config import rc
from .._sharing import (
    AXIS_LABEL_FORMAT_KEYS,
    axis_supports_format_key,
    get_axis_sharing_format_keys,
    restore_axis_sharing,
    snapshot_axis_sharing,
    update_sharing_for_format_keys,
    validate_axis_format_values,
)
from ..internals import ic  # noqa: F401
from ..internals import _pop_kwargs
from ..utils import _fontsize_to_pt, _not_none, units
from ..axes import Axes

try:
    # From python 3.12
    from typing import override
except ImportError:
    # From Python 3.5
    from typing_extensions import override


def _format_wrapper(method=None, *, exclude=(), capture_explicit=False):
    """Decorate a public format method with transactional sharing updates."""
    if method is None:
        return lambda method: _format_wrapper(
            method,
            exclude=exclude,
            capture_explicit=capture_explicit,
        )

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if capture_explicit:
            kwargs.setdefault("_explicit_format_keys", set(kwargs))
        validate_axis_format_values(kwargs)
        keys = {
            key
            for key in get_axis_sharing_format_keys(kwargs, exclude=exclude)
            if axis_supports_format_key(self, key)
        }
        if kwargs.get("skip_figure", False):
            keys.clear()
        figure = self.figure
        state = snapshot_axis_sharing(figure) if figure is not None and keys else None
        try:
            self._update_format_sharing(keys)
            return method(self, *args, **kwargs)
        except Exception:
            if state is not None:
                restore_axis_sharing(figure, state)
            raise

    return wrapper


class _SharedAxes(object):
    """
    Mix-in class with methods shared between `~ultraplot.axes.CartesianAxes`
    and :class:`~ultraplot.axes.PolarAxes`.
    """

    def _update_format_sharing(self, format_keys):
        """Apply sharing effects for one explicit axes-level format call."""
        if self.figure is None or not format_keys:
            return
        main_subplots = tuple(self.figure._iter_subplots())
        if len(main_subplots) < 2 or not any(self is ax for ax in main_subplots):
            return
        update_sharing_for_format_keys(self.figure, format_keys, axes=(self,))
        for which in "xy":
            if format_keys & AXIS_LABEL_FORMAT_KEYS[which]:
                getattr(self, f"{which}axis").label.set_visible(True)

    @staticmethod
    def _min_max_lim(key, min_=None, max_=None, lim=None):
        """
        Translate and standardize minimum, maximum, and limit keyword arguments.
        """
        if lim is None:
            lim = (None, None)
        if not np.iterable(lim) or not len(lim) == 2:
            raise ValueError(f"Invalid {key}{lim!r}. Must be 2-tuple of values.")
        min_ = _not_none(**{f"{key}min": min_, f"{key}lim_0": lim[0]})
        max_ = _not_none(**{f"{key}max": max_, f"{key}lim_1": lim[1]})
        return min_, max_

    def _update_background(self, **kwargs):
        """
        Update the background patch.
        """
        kw_face, kw_edge = rc._get_background_props(**kwargs)
        self.patch.update(kw_face)
        return kw_face, kw_edge

    def _update_frame(
        self,
        x,
        *,
        edgecolor=None,
        linewidth=None,
        tickcolor=None,
        tickwidth=None,
        tickwidthratio=None,
    ):
        """
        Update the axis frame, including spines and tick line appearance.
        """
        opts = (
            ("bottom", "top", "inner", "polar")
            if x == "x"
            else (
                "left",
                "right",
                "start",
                "end",
            )
        )
        kw_edge = {"capstyle": "projecting"}
        if edgecolor is not None:
            kw_edge["edgecolor"] = edgecolor
        if linewidth is not None:
            kw_edge["linewidth"] = linewidth
        if len(kw_edge) > 1:
            for opt in opts:
                self.spines.get(opt, {}).update(kw_edge)

        obj = getattr(self, x + "axis")
        if tickcolor is None:
            tickcolor = edgecolor
        if tickcolor is not None:
            self.tick_params(axis=x, which="both", color=tickcolor)

        # Update the tick widths
        kwmajor = getattr(obj, "_major_tick_kw", {})  # graceful fallback if API changes
        kwminor = getattr(obj, "_minor_tick_kw", {})
        tickwidth_prev = kwmajor.get("width", rc[x + "tick.major.width"])
        if tickwidth_prev == 0:
            tickwidthratio_prev = rc["tick.widthratio"]  # no other way of knowing
        else:
            tickwidthratio_prev = (
                kwminor.get("width", rc[x + "tick.minor.width"]) / tickwidth_prev
            )  # noqa: E501
        for which in ("major", "minor"):
            kwticks = {}
            if tickwidth is not None or tickwidthratio is not None:
                tickwidth = _not_none(tickwidth, tickwidth_prev)
                kwticks["width"] = tickwidth = units(tickwidth, "pt")
                if tickwidth == 0:  # avoid unnecessary padding
                    kwticks["size"] = 0
                elif which == "minor":
                    tickwidthratio = _not_none(tickwidthratio, tickwidthratio_prev)
                    kwticks["width"] *= tickwidthratio
            self.tick_params(axis=x, which=which, **kwticks)

    def _update_ticks(
        self,
        x,
        *,
        grid=None,
        gridminor=None,
        gridpad=None,
        gridcolor=None,
        ticklen=None,
        ticklenratio=None,
        tickdir=None,
        tickcolor=None,
        labeldir=None,
        labelpad=None,
        labelcolor=None,
        labelsize=None,
        labelweight=None,
    ):
        """
        Update the gridlines and labels. Set `gridpad` to ``True`` to use grid padding.
        """
        # Filter out text properties
        axis = "both" if x is None else x
        kwtext = rc._get_ticklabel_props(axis)
        kwtext_extra = _pop_kwargs(kwtext, "weight", "family")
        kwtext = {"label" + key: value for key, value in kwtext.items()}
        if labelcolor is not None:
            kwtext["labelcolor"] = labelcolor
        if labelsize is not None:
            kwtext["labelsize"] = labelsize
        if labelweight is not None:
            kwtext_extra["weight"] = labelweight

        # Apply tick settings with tick_params when possible
        x = _not_none(x, "x")
        obj = getattr(self, x + "axis")
        kwmajor = getattr(obj, "_major_tick_kw", {})  # graceful fallback if API changes
        kwminor = getattr(obj, "_minor_tick_kw", {})
        ticklen_prev = kwmajor.get("size", rc[x + "tick.major.size"])
        if ticklen_prev == 0:
            ticklenratio_prev = rc["tick.lenratio"]  # no other way of knowing
        else:
            ticklenratio_prev = (
                kwminor.get("size", rc[x + "tick.minor.size"]) / ticklen_prev
            )  # noqa: E501
        for b, which in zip((grid, gridminor), ("major", "minor")):
            # Tick properties
            # NOTE: Must make 'tickcolor' overwrite 'labelcolor' or else 'color'
            # passed to __init__ will not apply correctly. Annoying but unavoidable
            kwticks = rc._get_tickline_props(axis, which=which)
            if labelpad is not None:
                kwticks["pad"] = labelpad
            if tickcolor is not None:
                kwticks["color"] = tickcolor
            if ticklen is not None or ticklenratio is not None:
                ticklen = _not_none(ticklen, ticklen_prev)
                kwticks["size"] = ticklen = units(ticklen, "pt")
                if ticklen > 0 and which == "minor":
                    ticklenratio = _not_none(ticklenratio, ticklenratio_prev)
                    kwticks["size"] *= ticklenratio
            if gridpad:  # use grid.labelpad instead of tick.labelpad
                kwticks.pop("pad", None)
                pad = rc.find("grid.labelpad", context=True)
                if pad is not None:
                    kwticks["pad"] = units(pad, "pt")

            # Tick direction properties
            # NOTE: These have no x and y-specific versions but apply here anyway
            if labeldir == "in":  # put tick labels inside the plot
                tickdir = "in"
                kwticks.setdefault(
                    "pad",
                    -rc[f"{axis}tick.major.size"]
                    - _not_none(labelpad, rc[f"{axis}tick.major.pad"])
                    - _fontsize_to_pt(rc[f"{axis}tick.labelsize"]),
                )
            if tickdir is not None:
                kwticks["direction"] = tickdir

            # Gridline properties
            # NOTE: Internally ax.grid() passes gridOn to ax.tick_params() but this
            # is undocumented and might have weird side effects. Just use ax.grid()
            b = rc._get_gridline_bool(b, axis=axis, which=which)
            if b is not None:
                self.grid(b, axis=axis, which=which)
            kwlines = rc._get_gridline_props(which=which)
            if "axisbelow" in kwlines:
                self.set_axisbelow(kwlines.pop("axisbelow"))
            if gridcolor is not None:
                kwlines["grid_color"] = gridcolor

            # Apply tick and gridline properties
            kwticks.pop("ndivs", None)  # not in mpl
            self.tick_params(axis=axis, which=which, **kwticks, **kwlines, **kwtext)

        # Apply settings that can't be controlled with tick_params
        if kwtext_extra:
            for lab in obj.get_ticklabels():
                lab.update(kwtext_extra)

    @override
    def sharex(self, other):
        return self._share_axis_with(other, which="x")

    @override
    def sharey(self, other):
        self._share_axis_with(other, which="y")

    # Ultraplot internal function to share axes
    def _share_axis_with(self, other: "Axes", *, which: str):
        if not isinstance(other, Axes):
            return TypeError(
                f"Cannot share axes with {type(other).__name__}.\n"
                f"Expected: ultraplot.base.Axes instance\n"
                f"Received: {type(other).__name__}\n"
                "Please provide a valid Axes instance to share with."
            )

        self._shared_axes[which].join(self, other)
        # Get axis objects
        this_axis = getattr(self, f"{which}axis")
        other_axis = getattr(other, f"{which}axis")

        # Set minor ticker
        this_axis.set_minor_locator(other_axis.get_minor_locator())
        this_axis.set_minor_formatter(other_axis.get_minor_formatter())

        # Get and set limits
        limits = getattr(other, f"get_{which}lim")()
        set_lim = getattr(self, f"set_{which}lim")
        get_autoscale = getattr(other, f"get_autoscale{which}_on")

        lim0, lim1 = limits
        set_lim(lim0, lim1, emit=False, auto=get_autoscale())  # Set scale

        # Override scale
        this_axis._scale = other_axis._scale
