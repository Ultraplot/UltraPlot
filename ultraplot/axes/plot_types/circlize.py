#!/usr/bin/env python3
"""
Helpers for pyCirclize-backed circular plots.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

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


def _ensure_polar(ax, label: str) -> None:
    if not isinstance(ax, MplPolarAxes):
        raise ValueError(f"{label} requires a polar axes (proj='polar').")


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
    _ensure_polar(ax, "circos")
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
    start: float = 0,
    end: float = 360,
    space: float | Sequence[float] = 0,
    endspace: bool = True,
    r_lim: tuple[float, float] = (97, 100),
    cmap: Any = None,
    link_cmap: list[tuple[str, str, str]] | None = None,
    ticks_interval: int | None = None,
    order: str | list[str] | None = None,
    label_kws: Mapping[str, Any] | None = None,
    ticks_kws: Mapping[str, Any] | None = None,
    link_kws: Mapping[str, Any] | None = None,
    link_kws_handler=None,
    tooltip: bool = False,
):
    """
    Render a chord diagram using pyCirclize on the provided polar axes.
    """
    _ensure_polar(ax, "chord_diagram")

    pycirclize, matrix_obj, cmap = _resolve_chord_defaults(matrix, cmap)
    label_kws = {} if label_kws is None else dict(label_kws)
    ticks_kws = {} if ticks_kws is None else dict(ticks_kws)

    label_kws.setdefault("size", rc["font.size"])
    label_kws.setdefault("color", rc["meta.color"])
    ticks_kws.setdefault("label_size", rc["font.size"])
    text_kws = ticks_kws.get("text_kws")
    if text_kws is None:
        ticks_kws["text_kws"] = {"color": rc["meta.color"]}
    else:
        text_kws = dict(text_kws)
        text_kws.setdefault("color", rc["meta.color"])
        ticks_kws["text_kws"] = text_kws

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
        label_kws=label_kws,
        ticks_kws=ticks_kws,
        link_kws=link_kws,
        link_kws_handler=link_kws_handler,
    )
    circos.plotfig(ax=ax, tooltip=tooltip)
    return circos


def radar_chart(
    ax,
    table: Any,
    *,
    r_lim: tuple[float, float] = (0, 100),
    vmin: float = 0,
    vmax: float = 100,
    fill: bool = True,
    marker_size: int = 0,
    bg_color: str | None = "#eeeeee80",
    circular: bool = False,
    cmap: Any = None,
    show_grid_label: bool = True,
    grid_interval_ratio: float | None = 0.2,
    grid_line_kws: Mapping[str, Any] | None = None,
    grid_label_kws: Mapping[str, Any] | None = None,
    grid_label_formatter=None,
    label_kws_handler=None,
    line_kws_handler=None,
    marker_kws_handler=None,
):
    """
    Render a radar chart using pyCirclize on the provided polar axes.
    """
    _ensure_polar(ax, "radar_chart")

    pycirclize, table_obj, cmap = _resolve_radar_defaults(table, cmap)
    grid_line_kws = {} if grid_line_kws is None else dict(grid_line_kws)
    grid_label_kws = {} if grid_label_kws is None else dict(grid_label_kws)

    grid_line_kws.setdefault("color", rc["grid.color"])
    grid_label_kws.setdefault("size", rc["font.size"])
    grid_label_kws.setdefault("color", rc["meta.color"])

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
        grid_line_kws=grid_line_kws,
        grid_label_kws=grid_label_kws,
        grid_label_formatter=grid_label_formatter,
        label_kws_handler=label_kws_handler,
        line_kws_handler=line_kws_handler,
        marker_kws_handler=marker_kws_handler,
    )
    circos.plotfig(ax=ax)
    return circos


def phylogeny(
    ax,
    tree_data: Any,
    *,
    start: float = 0,
    end: float = 360,
    r_lim: tuple[float, float] = (50, 100),
    format: str = "newick",
    outer: bool = True,
    align_leaf_label: bool = True,
    ignore_branch_length: bool = False,
    leaf_label_size: float | None = None,
    leaf_label_rmargin: float = 2.0,
    reverse: bool = False,
    ladderize: bool = False,
    line_kws: Mapping[str, Any] | None = None,
    label_formatter=None,
    align_line_kws: Mapping[str, Any] | None = None,
    tooltip: bool = False,
):
    """
    Render a phylogenetic tree using pyCirclize on the provided polar axes.
    """
    _ensure_polar(ax, "phylogeny")
    pycirclize = _import_pycirclize()
    if leaf_label_size is None:
        leaf_label_size = rc["font.size"]
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
        line_kws=None if line_kws is None else dict(line_kws),
        label_formatter=label_formatter,
        align_line_kws=None if align_line_kws is None else dict(align_line_kws),
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
    _ensure_polar(ax, "circos_bed")
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
