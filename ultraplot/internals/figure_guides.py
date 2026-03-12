#!/usr/bin/env python3
"""
Shared guide-placement helpers for figure-level legends and colorbars.
"""

from dataclasses import dataclass

import matplotlib.axes as maxes
import numpy as np

from .. import gridspec as pgridspec
from ..config import rc
from . import _not_none, _translate_loc, context, warnings


@dataclass(frozen=True)
class GuidePlacement:
    """
    Resolved axes anchor and span metadata for a figure-level guide.
    """

    anchor_axes: object
    span: object = None
    row: object = None
    col: object = None
    rows: object = None
    cols: object = None
    has_span: bool = False


def _is_axes_sequence(obj):
    return np.iterable(obj) and not isinstance(obj, (str, maxes.Axes))


def _guide_side(loc, guide, default_loc):
    loc = _translate_loc(loc, guide, default=default_loc)
    return loc if loc in ("left", "right", "top", "bottom") else None


def _iter_axes_spans(axes):
    for ax in axes:
        if not hasattr(ax, "get_subplotspec"):
            continue
        ss = ax.get_subplotspec()
        if ss is None:
            continue
        ss = ss.get_topmost_subplotspec()
        r1, r2, c1, c2 = ss._get_rows_columns()
        gs = ss.get_gridspec()
        if gs is not None:
            try:
                r1, r2 = gs._decode_indices(r1, r2, which="h")
                c1, c2 = gs._decode_indices(c1, c2, which="w")
            except ValueError:
                # Panel and nested gridspec decoding is not always available.
                pass
        yield ax, (r1, r2, c1, c2)


def _infer_span_from_axes(records, side):
    r_min, r_max = float("inf"), float("-inf")
    c_min, c_max = float("inf"), float("-inf")
    for _, (r1, r2, c1, c2) in records:
        r_min = min(r_min, r1)
        r_max = max(r_max, r2)
        c_min = min(c_min, c1)
        c_max = max(c_max, c2)
    if side in ("left", "right"):
        return {"rows": (r_min + 1, r_max + 1)}
    return {"cols": (c_min + 1, c_max + 1)}


def _pick_anchor_axes(records, side, fallback):
    best_ax = None
    best_coord = float("-inf")
    if side:
        for ax, (r1, r2, c1, c2) in records:
            if side == "right":
                coord = c2
            elif side == "left":
                coord = -c1
            elif side == "bottom":
                coord = r2
            else:  # side == "top"
                coord = -r1
            if coord > best_coord:
                best_coord = coord
                best_ax = ax
    if best_ax is not None:
        return best_ax
    try:
        return next(iter(fallback))
    except (TypeError, StopIteration):
        return fallback


def _normalize_anchor_axes(anchor_axes, *, guide, has_span):
    if guide != "legend" or has_span or not isinstance(anchor_axes, list):
        return anchor_axes
    try:
        return pgridspec.SubplotGrid(anchor_axes)
    except ValueError:
        return anchor_axes[0]


def resolve_guide_placement(
    loc_ax,
    *,
    loc=None,
    guide=None,
    default_loc=None,
    span=None,
    row=None,
    col=None,
    rows=None,
    cols=None,
):
    """
    Resolve the anchor axes and span metadata for a figure-level guide.
    """
    has_span = _not_none(span, row, col, rows, cols) is not None
    side = _guide_side(loc, guide, default_loc)
    anchor_axes = loc_ax
    if _is_axes_sequence(loc_ax):
        records = list(_iter_axes_spans(loc_ax))
        if records and not has_span and side:
            inferred = _infer_span_from_axes(records, side)
            rows = _not_none(rows, inferred.get("rows"))
            cols = _not_none(cols, inferred.get("cols"))
            has_span = True
        if has_span:
            anchor_axes = _pick_anchor_axes(records, side, loc_ax)
    anchor_axes = _normalize_anchor_axes(
        anchor_axes,
        guide=guide,
        has_span=has_span,
    )
    return GuidePlacement(
        anchor_axes=anchor_axes,
        span=span,
        row=row,
        col=col,
        rows=rows,
        cols=cols,
        has_span=has_span,
    )


class FigureGuides:
    """
    Figure-level legend and colorbar coordination.
    """

    def __init__(self, figure):
        self.figure = figure

    def colorbar(
        self,
        mappable,
        values=None,
        *,
        loc=None,
        location=None,
        row=None,
        col=None,
        rows=None,
        cols=None,
        span=None,
        space=None,
        pad=None,
        width=None,
        **kwargs,
    ):
        figure = self.figure
        ax = kwargs.pop("ax", None)
        ref = kwargs.pop("ref", None)
        loc_ax = ref if ref is not None else ax
        cax = kwargs.pop("cax", None)
        if isinstance(values, maxes.Axes):
            cax = _not_none(cax_positional=values, cax=cax)
            values = None
        if isinstance(loc, maxes.Axes):
            ax = _not_none(ax_positional=loc, ax=ax)
            loc = None
        if kwargs.pop("use_gridspec", None) is not None:
            warnings._warn_ultraplot(
                "Ignoring the 'use_gridspec' keyword. ultraplot always allocates "
                "additional space for colorbars using the figure gridspec "
                "rather than 'stealing space' from the parent subplot."
            )
        if cax is not None:
            with context._state_context(cax, _internal_call=True):
                return super(type(figure), figure).colorbar(mappable, cax=cax, **kwargs)
        if loc_ax is not None:
            placement = self._resolve_placement(
                loc_ax,
                loc=loc,
                guide="colorbar",
                default_loc=rc["colorbar.loc"],
                span=span,
                row=row,
                col=col,
                rows=rows,
                cols=cols,
            )
            return placement.anchor_axes.colorbar(
                mappable,
                values,
                space=space,
                pad=pad,
                width=width,
                loc=loc,
                span=placement.span,
                row=placement.row,
                col=placement.col,
                rows=placement.rows,
                cols=placement.cols,
                **kwargs,
            )
        loc = _not_none(loc=loc, location=location, default="r")
        ax = figure._add_figure_panel(
            loc,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            span=span,
            width=width,
            space=space,
            pad=pad,
        )
        return ax.colorbar(mappable, values, loc="fill", **kwargs)

    def legend(
        self,
        handles=None,
        labels=None,
        *,
        loc=None,
        location=None,
        row=None,
        col=None,
        rows=None,
        cols=None,
        span=None,
        space=None,
        pad=None,
        width=None,
        **kwargs,
    ):
        figure = self.figure
        ax = kwargs.pop("ax", None)
        ref = kwargs.pop("ref", None)
        loc_ax = ref if ref is not None else ax
        if loc_ax is not None:
            content_ax = ax if ax is not None else loc_ax
            handles, labels = self._resolve_legend_inputs(
                content_ax,
                loc_ax,
                handles,
                labels,
            )
            placement = self._resolve_placement(
                loc_ax,
                loc=loc,
                guide="legend",
                default_loc=rc["legend.loc"],
                span=span,
                row=row,
                col=col,
                rows=rows,
                cols=cols,
            )
            return placement.anchor_axes.legend(
                handles,
                labels,
                loc=loc,
                space=space,
                pad=pad,
                width=width,
                span=placement.span,
                row=placement.row,
                col=placement.col,
                rows=placement.rows,
                cols=placement.cols,
                **kwargs,
            )
        loc = _not_none(loc=loc, location=location, default="r")
        ax = figure._add_figure_panel(
            loc,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            span=span,
            width=width,
            space=space,
            pad=pad,
        )
        return ax.legend(handles, labels, loc="fill", **kwargs)

    def _resolve_placement(
        self,
        loc_ax,
        *,
        loc,
        guide,
        default_loc,
        span,
        row,
        col,
        rows,
        cols,
    ):
        return resolve_guide_placement(
            loc_ax,
            loc=loc,
            guide=guide,
            default_loc=default_loc,
            span=span,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
        )

    def _resolve_legend_inputs(self, content_ax, loc_ax, handles, labels):
        if handles is not None or labels is not None:
            return handles, labels
        if not self._must_collect_legend_content(content_ax, loc_ax):
            return handles, labels
        return self._collect_legend_entries(content_ax)

    def _must_collect_legend_content(self, content_ax, loc_ax):
        return (
            np.iterable(content_ax) and not isinstance(content_ax, (str, maxes.Axes))
        ) or (content_ax is not loc_ax)

    def _collect_legend_entries(self, content_ax):
        if np.iterable(content_ax) and not isinstance(content_ax, (str, maxes.Axes)):
            handles = []
            labels = []
            for axi in content_ax:
                h, labels_local = axi.get_legend_handles_labels()
                handles.extend(h)
                labels.extend(labels_local)
            return handles, labels
        return content_ax.get_legend_handles_labels()
