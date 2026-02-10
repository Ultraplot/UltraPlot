---
title: "ultraplot.axes.plot_types.circlize"
description: "Helpers for pyCirclize-backed circular plots."
source: "ultraplot/axes/plot_types/circlize.py"
---

`ultraplot.axes.plot_types.circlize`

Helpers for pyCirclize-backed circular plots.

## Public Functions

### `circos(ax, sectors: Mapping[str, Any], *, start: float=0, end: float=360, space: float | Sequence[float]=0, endspace: bool=True, sector2clockwise: Mapping[str, bool] | None=None, show_axis_for_debug: bool=False, plot: bool=False, tooltip: bool=False)`

Create a pyCirclize Circos instance (optionally plot immediately).

### `chord_diagram(ax, matrix: Any, *, start: Optional[float]=None, end: Optional[float]=None, space: Optional[Union[float, Sequence[float]]]=None, endspace: Optional[bool]=None, r_lim: Optional[tuple[float, float]]=None, cmap: Any=None, link_cmap: Optional[list[tuple[str, str, str]]]=None, ticks_interval: Optional[int]=None, order: Optional[Union[str, list[str]]]=None, label_kw: Optional[Mapping[str, Any]]=None, ticks_kw: Optional[Mapping[str, Any]]=None, link_kw: Optional[Mapping[str, Any]]=None, link_kw_handler=None, tooltip: bool=False)`

Render a chord diagram using pyCirclize on the provided polar axes.

### `radar_chart(ax, table: Any, *, r_lim: Optional[tuple[float, float]]=None, vmin: Optional[float]=None, vmax: Optional[float]=None, fill: Optional[bool]=None, marker_size: Optional[int]=None, bg_color: Optional[str]=None, circular: Optional[bool]=None, cmap: Any=None, show_grid_label: Optional[bool]=None, grid_interval_ratio: Optional[float]=None, grid_line_kw: Optional[Mapping[str, Any]]=None, grid_label_kw: Optional[Mapping[str, Any]]=None, grid_label_formatter=None, label_kw_handler=None, line_kw_handler=None, marker_kw_handler=None)`

Render a radar chart using pyCirclize on the provided polar axes.

### `phylogeny(ax, tree_data: Any, *, start: Optional[float]=None, end: Optional[float]=None, r_lim: Optional[tuple[float, float]]=None, format: Optional[str]=None, outer: Optional[bool]=None, align_leaf_label: Optional[bool]=None, ignore_branch_length: Optional[bool]=None, leaf_label_size: Optional[float]=None, leaf_label_rmargin: Optional[float]=None, reverse: Optional[bool]=None, ladderize: Optional[bool]=None, line_kw: Optional[Mapping[str, Any]]=None, label_formatter=None, align_line_kw: Optional[Mapping[str, Any]]=None, tooltip: bool=False)`

Render a phylogenetic tree using pyCirclize on the provided polar axes.

### `circos_bed(ax, bed_file: Any, *, start: float=0, end: float=360, space: float | Sequence[float]=0, endspace: bool=True, sector2clockwise: Mapping[str, bool] | None=None, plot: bool=False, tooltip: bool=False)`

Create a Circos instance from a BED file (optionally plot immediately).
