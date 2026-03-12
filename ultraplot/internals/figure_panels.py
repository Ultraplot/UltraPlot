#!/usr/bin/env python3
"""
Panel creation helpers used by Figure.
"""

from dataclasses import dataclass

import matplotlib.axes as maxes

from .. import axes as paxes
from .. import constructor
from . import _not_none, _pop_params, _translate_loc, warnings


@dataclass(frozen=True)
class PanelRequest:
    parent_axes: object
    side: str
    slot_kwargs: dict
    subplot_kwargs: dict


class FigurePanels:
    """
    Panel creation and label policy for figure-attached axes.
    """

    def __init__(self, figure):
        self.figure = figure

    def add_axes_panel(
        self,
        ax,
        *,
        side=None,
        span=None,
        row=None,
        col=None,
        rows=None,
        cols=None,
        **kwargs,
    ):
        figure = self.figure
        ax, side = self._normalize_parent_axes(ax, side)
        gs = figure.gridspec
        if not gs:
            raise RuntimeError("The gridspec must be active.")

        request = self._build_request(
            gs,
            ax,
            side,
            span=span,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            subplot_kwargs=kwargs,
        )
        ss, share = gs._insert_panel_slot(side, ax, **request.slot_kwargs)
        share = self._normalize_geo_share(ax, share)

        subplot_kwargs = dict(request.subplot_kwargs)
        subplot_kwargs["autoshare"] = False
        subplot_kwargs.setdefault("number", False)
        pax = figure.add_subplot(ss, **subplot_kwargs)
        self._attach_panel(pax, ax, side, share)
        self._configure_panel_axis(pax, side)
        self._sync_geo_panel(ax, pax, side, share)
        self._configure_label_visibility(
            ax,
            pax,
            side,
            share,
            filled=request.slot_kwargs.get("filled", False),
        )
        return pax

    def _normalize_parent_axes(self, ax, side):
        ax = ax._altx_parent or ax
        ax = ax._alty_parent or ax
        if not isinstance(ax, paxes.Axes):
            raise RuntimeError("Cannot add panels to non-ultraplot axes.")
        if not isinstance(ax, maxes.SubplotBase):
            raise RuntimeError("Cannot add panels to non-subplot axes.")

        orig = ax._panel_side
        if orig is None:
            pass
        elif side is None or side == orig:
            ax, side = ax._panel_parent, orig
        else:
            raise RuntimeError(f"Cannot add {side!r} panel to existing {orig!r} panel.")
        side = _translate_loc(side, "panel", default=_not_none(orig, "right"))
        return ax, side

    def _build_request(
        self,
        gs,
        ax,
        side,
        *,
        span=None,
        row=None,
        col=None,
        rows=None,
        cols=None,
        subplot_kwargs=None,
    ):
        subplot_kwargs = dict(subplot_kwargs or {})
        slot_kwargs = _pop_params(subplot_kwargs, gs._insert_panel_slot)
        span_override = self._resolve_span_override(
            side,
            span=span,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
        )
        if span_override is not None:
            slot_kwargs["span_override"] = span_override
        return PanelRequest(
            parent_axes=ax,
            side=side,
            slot_kwargs=slot_kwargs,
            subplot_kwargs=subplot_kwargs,
        )

    def _resolve_span_override(
        self, side, *, span=None, row=None, col=None, rows=None, cols=None
    ):
        if side in ("left", "right"):
            if _not_none(cols, col) is not None and _not_none(rows, row) is None:
                raise ValueError(
                    f"For {side!r} panels (vertical), use 'rows=' or 'row=' "
                    "to specify span, not 'cols=' or 'col='."
                )
            if span is not None and _not_none(rows, row) is None:
                warnings._warn_ultraplot(
                    f"For {side!r} panels (vertical), prefer 'rows=' over 'span=' "
                    "for clarity. Using 'span' as rows."
                )
            return _not_none(rows, row, span)
        if _not_none(rows, row) is not None and _not_none(cols, col, span) is None:
            raise ValueError(
                f"For {side!r} panels (horizontal), use 'cols=' or 'span=' "
                "to specify span, not 'rows=' or 'row='."
            )
        return _not_none(cols, col, span)

    def _normalize_geo_share(self, ax, share):
        if isinstance(ax, paxes.GeoAxes) and not ax._is_rectilinear():
            if share:
                warnings._warn_ultraplot(
                    "Panel sharing disabled for non-rectilinear GeoAxes projections."
                )
            return False
        return share

    def _attach_panel(self, pax, ax, side, share):
        pax._panel_side = side
        pax._panel_share = share
        pax._panel_parent = ax
        ax._panel_dict[side].append(pax)
        ax._apply_auto_share()

    def _configure_panel_axis(self, pax, side):
        axis = pax.yaxis if side in ("left", "right") else pax.xaxis
        getattr(axis, "tick_" + side)()
        axis.set_label_position(side)

    def _sync_geo_panel(self, ax, pax, side, share):
        if not (share and isinstance(ax, paxes.GeoAxes)):
            return
        axis = pax.yaxis if side in ("left", "right") else pax.xaxis
        fmt_key = "deglat" if side in ("left", "right") else "deglon"
        axis.set_major_formatter(constructor.Formatter(fmt_key))
        getter = "get_y" if side in ("left", "right") else "get_x"
        axis._set_lim(*getattr(ax, f"{getter}lim")(), auto=True)

    def _configure_label_visibility(self, ax, pax, side, share, *, filled=False):
        if share and not filled:
            self._hide_parent_labels(ax, side)
        if side == "top":
            self._configure_top_panel_labels(ax, pax, share)
        elif side == "right":
            self._configure_right_panel_labels(ax, pax, share)

    def _hide_parent_labels(self, ax, side):
        if isinstance(ax, paxes.GeoAxes):
            ax._toggle_gridliner_labels(**{f"label{side}": False})
            return
        if side in ("top", "bottom"):
            ax.xaxis.set_tick_params(**{ax._label_key(f"label{side}"): False})
        else:
            ax.yaxis.set_tick_params(**{ax._label_key(f"label{side}"): False})

    def _configure_top_panel_labels(self, ax, pax, share):
        if not share:
            pax.xaxis.set_tick_params(
                **{
                    pax._label_key("labeltop"): True,
                    pax._label_key("labelbottom"): False,
                }
            )
            return
        on = ax.xaxis.get_tick_params()[ax._label_key("labeltop")]
        pax.xaxis.set_tick_params(**{pax._label_key("labeltop"): on})
        ax.yaxis.set_tick_params(labeltop=False)

    def _configure_right_panel_labels(self, ax, pax, share):
        if not share:
            pax.yaxis.set_tick_params(
                **{
                    pax._label_key("labelright"): True,
                    pax._label_key("labelleft"): False,
                }
            )
            return
        on = ax.yaxis.get_tick_params()[ax._label_key("labelright")]
        pax.yaxis.set_tick_params(**{pax._label_key("labelright"): on})
        ax.yaxis.set_tick_params(**{ax._label_key("labelright"): False})
