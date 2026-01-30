#!/usr/bin/env python3
"""
Helpers for pyCirclize-backed circular plots.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Union

from matplotlib.projections.polar import PolarAxes as MplPolarAxes

from ... import constructor
from ...config import rc


def _import_pycirclize():
    try:
        import pycirclize
    except ImportError as exc:
        base = Path(__file__).resolve().parents[3] / "pyCirclize" / "src"
        if base.is_dir() and str(base) not in sys.path:
            sys.path.insert(0, str(base))
            try:
                import pycirclize
            except ImportError as exc2:
                raise ImportError(
                    "pycirclize is required for circos plots. Install it with "
                    "`pip install 'ultraplot[circos]'` or ensure "
                    "`pyCirclize/src` is on PYTHONPATH."
                ) from exc2
        else:
            raise ImportError(
                "pycirclize is required for circos plots. Install it with "
                "`pip install 'ultraplot[circos]'` or ensure "
                "`pyCirclize/src` is on PYTHONPATH."
            ) from exc
    return pycirclize


def _unwrap_axes(ax, label: str):
    if ax.__class__.__name__ == "SubplotGrid":
        if len(ax) != 1:
            raise ValueError(f"{label} expects a single axes, got {len(ax)}.")
        ax = ax[0]
    return ax


def _ensure_polar(ax, label: str):
    ax = _unwrap_axes(ax, label)
    if not isinstance(ax, MplPolarAxes):
        raise ValueError(f"{label} requires a polar axes (proj='polar').")
    if getattr(ax, "_sharex", None) is not None:
        ax._unshare(which="x")
    if getattr(ax, "_sharey", None) is not None:
        ax._unshare(which="y")
    ax._ultraplot_axis_type = ("circos", type(ax))
    return ax


def _cycle_colors(n: int) -> list[str]:
    cycle = constructor.Cycle(rc["cycle"])
    colors = list(cycle.by_key().get("color", []))
    if not colors:
        colors = ["0.2"]
    if len(colors) >= n:
        return colors[:n]
    return [color for _, color in zip(range(n), itertools.cycle(colors))]


def _resolve_chord_defaults(matrix: Any, cmap: Any):
    pycirclize = _import_pycirclize()
    from pycirclize.parser.matrix import Matrix

    if isinstance(matrix, Matrix):
        matrix_obj = matrix
    else:
        matrix_obj = Matrix(matrix)

    if cmap is None:
        names = matrix_obj.all_names
        cmap = dict(zip(names, _cycle_colors(len(names)), strict=True))
    return pycirclize, matrix_obj, cmap


def _resolve_radar_defaults(table: Any, cmap: Any):
    pycirclize = _import_pycirclize()
    from pycirclize.parser.table import RadarTable

    if isinstance(table, RadarTable):
        table_obj = table
    else:
        table_obj = RadarTable(table)

    if cmap is None:
        names = table_obj.row_names
        cmap = dict(zip(names, _cycle_colors(len(names)), strict=True))
    return pycirclize, table_obj, cmap


def circos(
    ax,
    sectors: Mapping[str, Any],
    *,
    start: float = 0,
    end: float = 360,
    space: float | Sequence[float] = 0,
    endspace: bool = True,
    sector2clockwise: Mapping[str, bool] | None = None,
    show_axis_for_debug: bool = False,
    plot: bool = False,
    tooltip: bool = False,
):
    """
    Create a pyCirclize Circos instance (optionally plot immediately).
    """
    ax = _ensure_polar(ax, "circos")
    pycirclize = _import_pycirclize()
    circos_obj = pycirclize.Circos(
        sectors,
        start=start,
        end=end,
        space=space,
        endspace=endspace,
        sector2clockwise=sector2clockwise,
        show_axis_for_debug=show_axis_for_debug,
    )
    if plot:
        circos_obj.plotfig(ax=ax, tooltip=tooltip)
    return circos_obj


def chord_diagram(
    ax,
    matrix: Any,
    *,
    start: Optional[float] = None,
    end: Optional[float] = None,
    space: Optional[Union[float, Sequence[float]]] = None,
    endspace: Optional[bool] = None,
    r_lim: Optional[tuple[float, float]] = None,
    cmap: Any = None,
    link_cmap: Optional[list[tuple[str, str, str]]] = None,
    ticks_interval: Optional[int] = None,
    order: Optional[Union[str, list[str]]] = None,
    label_kw: Optional[Mapping[str, Any]] = None,
    ticks_kw: Optional[Mapping[str, Any]] = None,
    link_kw: Optional[Mapping[str, Any]] = None,
    link_kw_handler=None,
    tooltip: bool = False,
):
    """
    Render a chord diagram using pyCirclize on the provided polar axes.
    """
    ax = _ensure_polar(ax, "chord_diagram")

    start = rc["chord.start"] if start is None else start
    end = rc["chord.end"] if end is None else end
    space = rc["chord.space"] if space is None else space
    endspace = rc["chord.endspace"] if endspace is None else endspace
    r_lim = rc["chord.r_lim"] if r_lim is None else r_lim
    ticks_interval = (
        rc["chord.ticks_interval"] if ticks_interval is None else ticks_interval
    )
    order = rc["chord.order"] if order is None else order

    pycirclize, matrix_obj, cmap = _resolve_chord_defaults(matrix, cmap)
    label_kw = {} if label_kw is None else dict(label_kw)
    ticks_kw = {} if ticks_kw is None else dict(ticks_kw)

    label_kw.setdefault("size", rc["font.size"])
    label_kw.setdefault("color", rc["meta.color"])
    ticks_kw.setdefault("label_size", rc["font.size"])
    text_kw = ticks_kw.get("text_kw")
    if text_kw is None:
        ticks_kw["text_kws"] = {"color": rc["meta.color"]}
    else:
        text_kw = dict(text_kws)
        text_kw.setdefault("color", rc["meta.color"])
        ticks_kw["text_kws"] = text_kw

    circos = pycirclize.Circos.chord_diagram(
        matrix_obj,
        start=start,
        end=end,
        space=space,
        endspace=endspace,
        r_lim=r_lim,
        cmap=cmap,
        link_cmap=link_cmap,
        ticks_interval=ticks_interval,
        order=order,
        label_kws=label_kw,
        ticks_kws=ticks_kw,
        link_kws=link_kw,
        link_kws_handler=link_kw_handler,
    )
    circos.plotfig(ax=ax, tooltip=tooltip)
    return circos


def radar_chart(
    ax,
    table: Any,
    *,
    r_lim: Optional[tuple[float, float]] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    fill: Optional[bool] = None,
    marker_size: Optional[int] = None,
    bg_color: Optional[str] = None,
    circular: Optional[bool] = None,
    cmap: Any = None,
    show_grid_label: Optional[bool] = None,
    grid_interval_ratio: Optional[float] = None,
    grid_line_kw: Optional[Mapping[str, Any]] = None,
    grid_label_kw: Optional[Mapping[str, Any]] = None,
    grid_label_formatter=None,
    label_kw_handler=None,
    line_kw_handler=None,
    marker_kw_handler=None,
):
    """
    Render a radar chart using pyCirclize on the provided polar axes.
    """
    ax = _ensure_polar(ax, "radar_chart")

    r_lim = rc["radar.r_lim"] if r_lim is None else r_lim
    vmin = rc["radar.vmin"] if vmin is None else vmin
    vmax = rc["radar.vmax"] if vmax is None else vmax
    fill = rc["radar.fill"] if fill is None else fill
    marker_size = rc["radar.marker_size"] if marker_size is None else marker_size
    bg_color = rc["radar.bg_color"] if bg_color is None else bg_color
    circular = rc["radar.circular"] if circular is None else circular
    show_grid_label = (
        rc["radar.show_grid_label"] if show_grid_label is None else show_grid_label
    )
    grid_interval_ratio = (
        rc["radar.grid_interval_ratio"]
        if grid_interval_ratio is None
        else grid_interval_ratio
    )

    pycirclize, table_obj, cmap = _resolve_radar_defaults(table, cmap)
    grid_line_kw = {} if grid_line_kw is None else dict(grid_line_kw)
    grid_label_kw = {} if grid_label_kw is None else dict(grid_label_kw)

    grid_line_kw.setdefault("color", rc["grid.color"])
    grid_label_kw.setdefault("size", rc["font.size"])
    grid_label_kw.setdefault("color", rc["meta.color"])

    circos = pycirclize.Circos.radar_chart(
        table_obj,
        r_lim=r_lim,
        vmin=vmin,
        vmax=vmax,
        fill=fill,
        marker_size=marker_size,
        bg_color=bg_color,
        circular=circular,
        cmap=cmap,
        show_grid_label=show_grid_label,
        grid_interval_ratio=grid_interval_ratio,
        grid_line_kws=grid_line_kw,
        grid_label_kws=grid_label_kw,
        grid_label_formatter=grid_label_formatter,
        label_kws_handler=label_kw_handler,
        line_kws_handler=line_kw_handler,
        marker_kws_handler=marker_kw_handler,
    )
    circos.plotfig(ax=ax)
    return circos


def phylogeny(
    ax,
    tree_data: Any,
    *,
    start: Optional[float] = None,
    end: Optional[float] = None,
    r_lim: Optional[tuple[float, float]] = None,
    format: Optional[str] = None,
    outer: Optional[bool] = None,
    align_leaf_label: Optional[bool] = None,
    ignore_branch_length: Optional[bool] = None,
    leaf_label_size: Optional[float] = None,
    leaf_label_rmargin: Optional[float] = None,
    reverse: Optional[bool] = None,
    ladderize: Optional[bool] = None,
    line_kw: Optional[Mapping[str, Any]] = None,
    label_formatter=None,
    align_line_kw: Optional[Mapping[str, Any]] = None,
    tooltip: bool = False,
):
    """
    Render a phylogenetic tree using pyCirclize on the provided polar axes.
    """
    ax = _ensure_polar(ax, "phylogeny")
    start = rc["phylogeny.start"] if start is None else start
    end = rc["phylogeny.end"] if end is None else end
    r_lim = rc["phylogeny.r_lim"] if r_lim is None else r_lim
    format = rc["phylogeny.format"] if format is None else format
    outer = rc["phylogeny.outer"] if outer is None else outer
    align_leaf_label = (
        rc["phylogeny.align_leaf_label"]
        if align_leaf_label is None
        else align_leaf_label
    )
    ignore_branch_length = (
        rc["phylogeny.ignore_branch_length"]
        if ignore_branch_length is None
        else ignore_branch_length
    )
    leaf_label_size = (
        rc["phylogeny.leaf_label_size"] if leaf_label_size is None else leaf_label_size
    )
    if leaf_label_size is None:
        leaf_label_size = rc["font.size"]
    leaf_label_rmargin = (
        rc["phylogeny.leaf_label_rmargin"]
        if leaf_label_rmargin is None
        else leaf_label_rmargin
    )
    reverse = rc["phylogeny.reverse"] if reverse is None else reverse
    ladderize = rc["phylogeny.ladderize"] if ladderize is None else ladderize

    pycirclize = _import_pycirclize()
    circos_obj, treeviz = pycirclize.Circos.initialize_from_tree(
        tree_data,
        start=start,
        end=end,
        r_lim=r_lim,
        format=format,
        outer=outer,
        align_leaf_label=align_leaf_label,
        ignore_branch_length=ignore_branch_length,
        leaf_label_size=leaf_label_size,
        leaf_label_rmargin=leaf_label_rmargin,
        reverse=reverse,
        ladderize=ladderize,
        line_kws=None if line_kw is None else dict(line_kw),
        label_formatter=label_formatter,
        align_line_kws=None if align_line_kw is None else dict(align_line_kw),
    )
    circos_obj.plotfig(ax=ax, tooltip=tooltip)
    return circos_obj, treeviz


def circos_bed(
    ax,
    bed_file: Any,
    *,
    start: float = 0,
    end: float = 360,
    space: float | Sequence[float] = 0,
    endspace: bool = True,
    sector2clockwise: Mapping[str, bool] | None = None,
    plot: bool = False,
    tooltip: bool = False,
):
    """
    Create a Circos instance from a BED file (optionally plot immediately).
    """
    ax = _ensure_polar(ax, "circos_bed")
    pycirclize = _import_pycirclize()
    circos_obj = pycirclize.Circos.initialize_from_bed(
        bed_file,
        start=start,
        end=end,
        space=space,
        endspace=endspace,
        sector2clockwise=sector2clockwise,
    )
    if plot:
        circos_obj.plotfig(ax=ax, tooltip=tooltip)
    return circos_obj
