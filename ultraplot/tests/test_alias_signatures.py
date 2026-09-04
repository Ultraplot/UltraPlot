"""Regression tests for canonical public call signatures."""

import inspect

from ultraplot.axes.base import Axes
from ultraplot.axes.cartesian import CartesianAxes
from ultraplot.axes.geo import GeoAxes
from ultraplot.axes.plot import PlotAxes
from ultraplot.axes.polar import PolarAxes
from ultraplot.axes.taylor import TaylorAxes
from ultraplot._subplots import SubplotManager
from ultraplot.colorbar import UltraColorbar
from ultraplot.constructor import Cycle, Proj
from ultraplot.figure import Figure
from ultraplot.gridspec import GridSpec
from ultraplot.legend import UltraLegend
from ultraplot.ultralayout import (
    UltraLayoutSolver,
    compute_ultra_positions,
    get_grid_positions_ultra,
)


def _parameter_names(signature):
    return {
        name
        for name, parameter in signature.parameters.items()
        if name != "self"
        and parameter.kind not in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)
    }


def test_format_signatures_contain_only_canonical_names() -> None:
    aliases = {
        Axes: {"ltitle", "ctitle", "rtitle"},
        CartesianAxes: {"xloc", "xticks", "xticklabels", "xminorticks"},
        GeoAxes: {"lonlines", "latlines", "lonlines_kw", "latlines_kw"},
        PolarAxes: {"thetalines", "rlines", "thetalabels", "rlabels"},
        TaylorAxes: {"corrlines", "corrticks"},
    }
    for cls, legacy_names in aliases.items():
        names = _parameter_names(Axes._format_signatures[cls])
        assert names.isdisjoint(legacy_names)

    names = _parameter_names(Figure._format_signature)
    assert names.isdisjoint({"figtitle", "llabels", "rowlabels", "collabels"})


def test_largest_migrated_signature_has_thirteen_fewer_parameters() -> None:
    names = _parameter_names(inspect.signature(UltraColorbar.add))
    assert len(names) == 47
    assert names.isdisjoint(
        {
            "length",
            "title",
            "grid",
            "edges",
            "locator",
            "formatter",
            "ticklabels",
            "minorlocator",
            "tickdir",
            "labelloc",
            "c",
            "lw",
            "frame",
        }
    )


def test_figure_init_signature_contains_only_canonical_names() -> None:
    names = _parameter_names(inspect.signature(inspect.unwrap(Figure.__init__)))
    assert len(names) == 36
    assert names.isdisjoint({"ref", "aspect", "axwidth", "axheight", "width", "height"})


def test_layout_and_projection_signatures_contain_only_canonical_names() -> None:
    cases = (
        (SubplotManager.parse_proj, {"proj", "proj_kw"}),
        (SubplotManager.add_subplots, {"proj", "proj_kw"}),
        (GridSpec._update_params, {"wratios", "hratios"}),
        (UltraLayoutSolver.__init__, {"wratios", "hratios"}),
        (compute_ultra_positions, {"wratios", "hratios"}),
        (get_grid_positions_ultra, {"wratios", "hratios"}),
        (Cycle.__init__, {"N"}),
        (Proj, {"lon_0", "lat_0"}),
        (Axes._add_inset_axes, {"proj"}),
    )
    for function, legacy_names in cases:
        names = _parameter_names(inspect.signature(function))
        assert names.isdisjoint(legacy_names)


def test_guide_signatures_contain_only_canonical_names() -> None:
    cases = (
        (Axes.colorbar, {"location"}),
        (Axes.legend, {"location"}),
        (Figure.colorbar, {"location"}),
        (Figure.legend, {"location"}),
        (Axes._add_legend, {"ncol", "frame"}),
        (UltraLegend.add, {"location", "ncol", "frame"}),
        (UltraLegend._resolve_inputs, {"ncol", "frame"}),
    )
    for function, legacy_names in cases:
        signature = inspect.signature(inspect.unwrap(function))
        assert _parameter_names(signature).isdisjoint(legacy_names)


def test_plotting_helper_signatures_contain_only_canonical_names() -> None:
    cases = (
        (PlotAxes._add_auto_labels, {"fmt"}),
        (PlotAxes._add_quadmesh_labels, {"c", "colors", "size"}),
        (PlotAxes._add_collection_labels, {"c", "colors", "size"}),
        (PlotAxes._add_contour_labels, {"c", "color", "size"}),
        (
            PlotAxes._add_error_bars,
            {"bars", "barstd", "barpctile", "boxes", "boxstd", "boxpctile"},
        ),
        (
            PlotAxes._add_error_shading,
            {"shade", "shadestd", "shadepctile", "fade", "fadestd", "fadepctile"},
        ),
        (PlotAxes._parse_cmap, {"c", "color"}),
        (PlotAxes._parse_level_vals, {"N"}),
        (PlotAxes._apply_lines, {"stack"}),
        (PlotAxes._apply_fill, {"stack"}),
        (PlotAxes._apply_bar, {"stack"}),
        (PlotAxes._apply_boxplot, {"mean", "showmeans", "filled"}),
        (
            PlotAxes._apply_violinplot,
            {"mean", "median", "showmeans", "showmedians"},
        ),
        (PlotAxes._apply_hist, {"width", "stack", "filled"}),
        (inspect.unwrap(PlotAxes.pie), {"labelpad"}),
    )
    for function, legacy_names in cases:
        names = _parameter_names(inspect.signature(function))
        assert names.isdisjoint(legacy_names)
