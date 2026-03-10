#!/usr/bin/env python3
"""
Astropy WCS axes integration.
"""

import inspect
import numbers
from collections.abc import Iterable

from ..config import rc
from ..utils import _not_none
from . import base
from .cartesian import CartesianAxes

try:
    from astropy.visualization.wcsaxes.core import WCSAxes
    from astropy.wcs.wcsapi import BaseHighLevelWCS, BaseLowLevelWCS
except ImportError:  # pragma: no cover
    WCSAxes = None
    ASTROPY_WCS_TYPES = ()
else:
    ASTROPY_WCS_TYPES = (BaseLowLevelWCS, BaseHighLevelWCS)


if WCSAxes is not None:

    class AstroAxes(base.Axes, WCSAxes):
        """
        Native UltraPlot wrapper for Astropy WCS axes.
        """

        _name = "astro"
        _name_aliases = ("astropy", "wcs")

        def _update_background(self, **kwargs):
            kw_face, kw_edge = rc._get_background_props(**kwargs)
            self.patch.update(kw_face)
            self.patch.update(kw_edge)

        def _get_coord_helper(self, axis):
            index = {"x": 0, "y": 1}[axis]
            try:
                return self.coords[index]
            except IndexError:
                return None

        def _share_coord_signature(self, axis):
            coord = self._get_coord_helper(axis)
            if coord is None:
                return None
            unit = getattr(coord, "coord_unit", None)
            if unit is not None and hasattr(unit, "to_string"):
                unit = unit.to_string()
            return (
                getattr(coord, "coord_type", None),
                unit,
                getattr(coord, "default_label", None),
            )

        def _update_coord_locator(self, axis, locator):
            coord = self._get_coord_helper(axis)
            if coord is None or locator is None:
                return
            if isinstance(locator, numbers.Real) and not isinstance(locator, bool):
                coord.set_ticks(number=locator)
                return
            if isinstance(locator, Iterable) and not isinstance(locator, (str, bytes)):
                coord.set_ticks(values=locator)
                return
            raise TypeError(
                "AstroAxes.format only supports numeric or iterable tick locators. "
                f"Received {locator!r}. Use ax.coords[...] for advanced locator setup."
            )

        def _update_coord_formatter(self, axis, formatter):
            coord = self._get_coord_helper(axis)
            if coord is None or formatter is None:
                return
            if isinstance(formatter, str) or callable(formatter):
                coord.set_major_formatter(formatter)
                return
            raise TypeError(
                "AstroAxes.format only supports string or callable tick formatters. "
                f"Received {formatter!r}. Use ax.coords[...] for advanced formatter setup."
            )

        def _update_coord_ticks(
            self,
            axis,
            *,
            grid=None,
            gridcolor=None,
            tickcolor=None,
            ticklen=None,
            tickwidth=None,
            tickdir=None,
            ticklabelpad=None,
            ticklabelcolor=None,
            ticklabelsize=None,
            ticklabelweight=None,
            tickminor=None,
        ):
            coord = self._get_coord_helper(axis)
            if coord is None:
                return
            if tickminor is not None:
                coord.display_minor_ticks(bool(tickminor))
            major = {}
            if ticklen is not None:
                major["length"] = ticklen
            if tickwidth is not None:
                major["width"] = tickwidth
            if tickcolor is not None:
                major["color"] = tickcolor
            if tickdir is not None:
                major["direction"] = tickdir
            if ticklabelpad is not None:
                major["pad"] = ticklabelpad
            if ticklabelcolor is not None:
                major["labelcolor"] = ticklabelcolor
            if ticklabelsize is not None:
                major["labelsize"] = ticklabelsize
            if major:
                coord.tick_params(**major)
            if ticklabelweight is not None:
                coord.set_ticklabel(weight=ticklabelweight)
            if grid is not None or gridcolor is not None:
                kw = {}
                if gridcolor is not None:
                    kw["color"] = gridcolor
                coord.grid(draw_grid=grid, **kw)

        def _update_axis_label(
            self,
            axis,
            *,
            label=None,
            labelpad=None,
            labelcolor=None,
            labelsize=None,
            labelweight=None,
            label_kw=None,
        ):
            coord = self._get_coord_helper(axis)
            if coord is None:
                return
            if label is None and not any(
                value is not None for value in (labelpad, labelcolor, labelsize, labelweight)
            ):
                return
            setter = getattr(self, f"set_{axis}label")
            getter = getattr(self, f"get_{axis}label")
            kw = dict(label_kw or {})
            if labelcolor is not None:
                kw["color"] = labelcolor
            if labelsize is not None:
                kw["size"] = labelsize
            if labelweight is not None:
                kw["weight"] = labelweight
            if labelpad is not None:
                kw["labelpad"] = labelpad
            setter(getter() if label is None else label, **kw)

        def _update_limits(self, axis, *, lim=None, min_=None, max_=None, reverse=None):
            lo = hi = None
            if lim is not None:
                lo, hi = lim
            lo = _not_none(min_=min_, lim_0=lo)
            hi = _not_none(max_=max_, lim_1=hi)
            if lo is not None or hi is not None:
                get_lim = getattr(self, f"get_{axis}lim")
                set_lim = getattr(self, f"set_{axis}lim")
                cur_lo, cur_hi = get_lim()
                set_lim((_not_none(lo, cur_lo), _not_none(hi, cur_hi)))
            if reverse is not None:
                inverted = getattr(self, f"{axis}axis_inverted")()
                if bool(reverse) != bool(inverted):
                    getattr(self, f"invert_{axis}axis")()

        def _share_axis_limits(self, other, which):
            self._shared_axes[which].join(self, other)
            axis = getattr(self, f"{which}axis")
            other_axis = getattr(other, f"{which}axis")
            setattr(self, f"_share{which}", other)
            axis.major = other_axis.major
            axis.minor = other_axis.minor
            get_lim = getattr(other, f"get_{which}lim")
            set_lim = getattr(self, f"set_{which}lim")
            get_auto = getattr(other, f"get_autoscale{which}_on")
            set_lim(*get_lim(), emit=False, auto=get_auto())
            axis._scale = other_axis._scale

        def _sharex_setup(self, sharex, *, labels=True, limits=True):
            super()._sharex_setup(sharex)
            level = (
                3
                if self._panel_sharex_group and self._is_panel_group_member(sharex)
                else self.figure._sharex
            )
            if level not in range(5):
                raise ValueError(f"Invalid sharing level sharex={level!r}.")
            if sharex in (None, self) or not isinstance(sharex, AstroAxes):
                return
            if level > 0 and labels:
                self._sharex = sharex
            if level > 1 and limits:
                self._share_axis_limits(sharex, "x")

        def _sharey_setup(self, sharey, *, labels=True, limits=True):
            super()._sharey_setup(sharey)
            level = (
                3
                if self._panel_sharey_group and self._is_panel_group_member(sharey)
                else self.figure._sharey
            )
            if level not in range(5):
                raise ValueError(f"Invalid sharing level sharey={level!r}.")
            if sharey in (None, self) or not isinstance(sharey, AstroAxes):
                return
            if level > 0 and labels:
                self._sharey = sharey
            if level > 1 and limits:
                self._share_axis_limits(sharey, "y")

        def _is_ticklabel_on(self, side: str) -> bool:
            axis = "x" if side in ("labelbottom", "labeltop") else "y"
            coord = self._get_coord_helper(axis)
            if coord is None or not coord.get_ticklabel_visible():
                return False
            positions = coord.get_ticklabel_position()
            tokens = {
                "labelbottom": "b",
                "labeltop": "t",
                "labelleft": "l",
                "labelright": "r",
                "bottom": "b",
                "top": "t",
                "left": "l",
                "right": "r",
            }
            token = tokens.get(side, side)
            if token in positions:
                return True
            if "#" in positions:
                return token == ("b" if axis == "x" else "l")
            return False

        def _get_ticklabel_state(self, axis: str) -> dict[str, bool]:
            sides = ("top", "bottom") if axis == "x" else ("left", "right")
            return {
                f"label{side}": self._is_ticklabel_on(f"label{side}")
                for side in sides
            }

        def _set_ticklabel_state(self, axis: str, state: dict):
            coord = self._get_coord_helper(axis)
            if coord is None:
                return
            positions = []
            for side in ("bottom", "top") if axis == "x" else ("left", "right"):
                if state.get(f"label{side}", False):
                    positions.append(side[0])
            position = "".join(positions)
            coord.set_ticklabel_position(position)
            coord.set_axislabel_position(position)
            coord.set_ticklabel_visible(bool(positions))

        def _apply_ticklabel_state(self, axis: str, state: dict):
            self._set_ticklabel_state(axis, state)

        def format(
            self,
            *,
            aspect=None,
            xreverse=None,
            yreverse=None,
            xlim=None,
            ylim=None,
            xmin=None,
            ymin=None,
            xmax=None,
            ymax=None,
            xformatter=None,
            yformatter=None,
            xlocator=None,
            ylocator=None,
            xtickminor=None,
            ytickminor=None,
            xtickcolor=None,
            ytickcolor=None,
            xticklen=None,
            yticklen=None,
            xtickwidth=None,
            ytickwidth=None,
            xtickdir=None,
            ytickdir=None,
            xticklabelpad=None,
            yticklabelpad=None,
            xticklabelcolor=None,
            yticklabelcolor=None,
            xticklabelsize=None,
            yticklabelsize=None,
            xticklabelweight=None,
            yticklabelweight=None,
            xlabel=None,
            ylabel=None,
            xlabelpad=None,
            ylabelpad=None,
            xlabelcolor=None,
            ylabelcolor=None,
            xlabelsize=None,
            ylabelsize=None,
            xlabelweight=None,
            ylabelweight=None,
            xgrid=None,
            ygrid=None,
            xgridcolor=None,
            ygridcolor=None,
            xlabel_kw=None,
            ylabel_kw=None,
            **kwargs,
        ):
            if aspect is not None:
                self.set_aspect(aspect)
            self._update_limits("x", lim=xlim, min_=xmin, max_=xmax, reverse=xreverse)
            self._update_limits("y", lim=ylim, min_=ymin, max_=ymax, reverse=yreverse)
            self._update_coord_locator("x", xlocator)
            self._update_coord_locator("y", ylocator)
            self._update_coord_formatter("x", xformatter)
            self._update_coord_formatter("y", yformatter)
            self._update_coord_ticks(
                "x",
                grid=xgrid,
                gridcolor=xgridcolor,
                tickcolor=xtickcolor,
                ticklen=xticklen,
                tickwidth=xtickwidth,
                tickdir=xtickdir,
                ticklabelpad=xticklabelpad,
                ticklabelcolor=xticklabelcolor,
                ticklabelsize=xticklabelsize,
                ticklabelweight=xticklabelweight,
                tickminor=xtickminor,
            )
            self._update_coord_ticks(
                "y",
                grid=ygrid,
                gridcolor=ygridcolor,
                tickcolor=ytickcolor,
                ticklen=yticklen,
                tickwidth=ytickwidth,
                tickdir=ytickdir,
                ticklabelpad=yticklabelpad,
                ticklabelcolor=yticklabelcolor,
                ticklabelsize=yticklabelsize,
                ticklabelweight=yticklabelweight,
                tickminor=ytickminor,
            )
            self._update_axis_label(
                "x",
                label=xlabel,
                labelpad=xlabelpad,
                labelcolor=xlabelcolor,
                labelsize=xlabelsize,
                labelweight=xlabelweight,
                label_kw=xlabel_kw,
            )
            self._update_axis_label(
                "y",
                label=ylabel,
                labelpad=ylabelpad,
                labelcolor=ylabelcolor,
                labelsize=ylabelsize,
                labelweight=ylabelweight,
                label_kw=ylabel_kw,
            )
            return base.Axes.format(self, **kwargs)


    AstroAxes._format_signatures[AstroAxes] = inspect.signature(CartesianAxes.format)
else:  # pragma: no cover
    AstroAxes = None
