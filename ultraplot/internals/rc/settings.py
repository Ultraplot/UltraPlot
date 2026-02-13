#!/usr/bin/env python3
"""
Single-source rc setting table with section headers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .registry import merge_rc_tables
from .validators import build_validator_aliases

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]

_PLOT_PREFIXES = ("curved_quiver.", "sankey.", "ribbon.")
_TEXT_PREFIXES = (
    "abc.",
    "text.",
    "title.",
    "suptitle.",
    "leftlabel.",
    "rightlabel.",
    "toplabel.",
    "bottomlabel.",
    "font.",
)
_SUBPLOT_PREFIX = "subplots."


@dataclass(frozen=True)
class Spec:
    """Declarative rc setting specification."""

    default: Any
    validator: RcValidator
    description: str

    def as_entry(self) -> RcEntry:
        return (self.default, self.validator, self.description)


def _coerce_spec(value: Spec | RcEntry) -> Spec:
    if isinstance(value, Spec):
        return value
    default, validator, description = value
    return Spec(default=default, validator=validator, description=description)


def _section_entries(
    raw_settings: Mapping[str, Spec | RcEntry],
    predicate,
) -> dict[str, RcEntry]:
    return {
        key: _coerce_spec(value).as_entry()
        for key, value in raw_settings.items()
        if predicate(key)
    }


def build_settings_rc_table(ns: Mapping[str, Any]) -> RcTable:
    """Build the rc setting table from a single declarative settings map."""
    g = ns.__getitem__
    v = build_validator_aliases(ns)

    raw_settings: dict[str, Spec | RcEntry] = {
        # Plot-type settings
        # Curved quiver settings
        "curved_quiver.arrowsize": (
            1.0,
            v["float"],
            "Default size scaling for arrows in curved quiver plots.",
        ),
        "curved_quiver.arrowstyle": (
            "-|>",
            v["string"],
            "Default arrow style for curved quiver plots.",
        ),
        "curved_quiver.scale": (
            1.0,
            v["float"],
            "Default scale factor for curved quiver plots.",
        ),
        "curved_quiver.grains": (
            15,
            v["int"],
            "Default number of grains (segments) for curved quiver arrows.",
        ),
        "curved_quiver.density": (
            10,
            v["int"],
            "Default density of arrows for curved quiver plots.",
        ),
        "curved_quiver.arrows_at_end": (
            True,
            v["bool"],
            "Whether to draw arrows at the end of curved quiver lines by default.",
        ),
        # Sankey settings
        "sankey.nodepad": (
            0.02,
            v["float"],
            "Vertical padding between nodes in layered sankey diagrams.",
        ),
        "sankey.nodewidth": (
            0.03,
            v["float"],
            "Node width for layered sankey diagrams (axes-relative units).",
        ),
        "sankey.margin": (
            0.05,
            v["float"],
            "Margin around layered sankey diagrams (axes-relative units).",
        ),
        "sankey.flow.alpha": (
            0.75,
            v["float"],
            "Flow transparency for layered sankey diagrams.",
        ),
        "sankey.flow.curvature": (
            0.5,
            v["float"],
            "Flow curvature for layered sankey diagrams.",
        ),
        "sankey.node.facecolor": (
            "0.75",
            v["color"],
            "Default node facecolor for layered sankey diagrams.",
        ),
        # Ribbon settings
        "ribbon.xmargin": (
            0.12,
            v["float"],
            "Horizontal margin around ribbon diagrams (axes-relative units).",
        ),
        "ribbon.ymargin": (
            0.08,
            v["float"],
            "Vertical margin around ribbon diagrams (axes-relative units).",
        ),
        "ribbon.rowheightratio": (
            2.2,
            v["float"],
            "Height scale factor controlling ribbon row occupancy.",
        ),
        "ribbon.nodewidth": (
            0.018,
            v["float"],
            "Node width for ribbon diagrams (axes-relative units).",
        ),
        "ribbon.flow.curvature": (
            0.45,
            v["float"],
            "Flow curvature for ribbon diagrams.",
        ),
        "ribbon.flow.alpha": (
            0.58,
            v["float"],
            "Flow transparency for ribbon diagrams.",
        ),
        "ribbon.topic_labels": (
            True,
            v["bool"],
            "Whether to draw topic labels on the right side of ribbon diagrams.",
        ),
        "ribbon.topic_label_offset": (
            0.028,
            v["float"],
            "Offset for right-side ribbon topic labels.",
        ),
        "ribbon.topic_label_size": (
            7.4,
            v["float"],
            "Font size for ribbon topic labels.",
        ),
        "ribbon.topic_label_box": (
            True,
            v["bool"],
            "Whether to draw backing boxes behind ribbon topic labels.",
        ),
        "external.shrink": (
            0.9,
            g("_validate_float"),
            "Default shrink factor for external axes containers.",
        ),
        # Stylesheet
        "style": (
            None,
            g("_validate_or_none")(g("_validate_string")),
            "The default matplotlib `stylesheet "
            "<https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html>`__ "  # noqa: E501
            "name. If ``None``, a custom ultraplot style is used. "
            "If ``'default'``, the default matplotlib style is used.",
        ),
        # A-b-c labels
        "abc": (
            False,
            g("_validate_abc"),
            "If ``False`` then a-b-c labels are disabled. If ``True`` the default label "
            "style `a` is used. If string this indicates the style and must contain the "
            "character `a` or ``A``, for example ``'a.'`` or ``'(A)'``.",
        ),
        "abc.border": (
            True,
            g("_validate_bool"),
            "Whether to draw a white border around a-b-c labels "
            "when :rcraw:`abc.loc` is inside the axes.",
        ),
        "abc.borderwidth": (
            1.5,
            g("_validate_pt"),
            "Width of the white border around a-b-c labels.",
        ),
        "text.borderstyle": (
            "bevel",
            g("_validate_joinstyle"),
            "Join style for text border strokes. Must be one of "
            "``'miter'``, ``'round'``, or ``'bevel'``.",
        ),
        "text.curved.upright": (
            True,
            g("_validate_bool"),
            "Whether curved text is flipped to remain upright by default.",
        ),
        "text.curved.ellipsis": (
            False,
            g("_validate_bool"),
            "Whether to show ellipses when curved text exceeds path length.",
        ),
        "text.curved.avoid_overlap": (
            True,
            g("_validate_bool"),
            "Whether curved text hides overlapping glyphs by default.",
        ),
        "text.curved.overlap_tol": (
            0.1,
            g("_validate_float"),
            "Overlap threshold used when hiding curved-text glyphs.",
        ),
        "text.curved.curvature_pad": (
            2.0,
            g("_validate_float"),
            "Extra curved-text glyph spacing per radian of local curvature.",
        ),
        "text.curved.min_advance": (
            1.0,
            g("_validate_float"),
            "Minimum extra curved-text glyph spacing in pixels.",
        ),
        "abc.bbox": (
            False,
            g("_validate_bool"),
            "Whether to draw semi-transparent bounding boxes around a-b-c labels "
            "when :rcraw:`abc.loc` is inside the axes.",
        ),
        "abc.bboxcolor": (g("WHITE"), g("_validate_color"), "a-b-c label bounding box color."),
        "abc.bboxstyle": (
            "square",
            g("_validate_boxstyle"),
            "a-b-c label bounding box style.",
        ),
        "abc.bboxalpha": (0.5, g("_validate_float"), "a-b-c label bounding box opacity."),
        "abc.bboxpad": (
            None,
            g("_validate_or_none")(g("_validate_pt")),
            "Padding for the a-b-c label bounding box. By default this is scaled "
            "to make the box flush against the subplot edge." + g("_addendum_pt"),
        ),
        "abc.color": (g("BLACK"), g("_validate_color"), "a-b-c label color."),
        "abc.loc": (
            "left",  # left side above the axes
            g("_validate_belongs")(*g("TEXT_LOCS")),
            "a-b-c label position. "
            "For options see the :ref:`location table <title_table>`.",
        ),
        "abc.size": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "a-b-c label font size." + g("_addendum_font"),
        ),
        "abc.titlepad": (
            g("LABELPAD"),
            g("_validate_pt"),
            "Padding separating the title and a-b-c label when in the same location."
            + g("_addendum_pt"),
        ),
        "abc.weight": ("bold", g("_validate_fontweight"), "a-b-c label font weight."),
        # Autoformatting
        "autoformat": (
            True,
            g("_validate_bool"),
            "Whether to automatically apply labels from `pandas.Series`, "
            "`pandas.DataFrame`, and `xarray.DataArray` objects passed to "
            "plotting functions. See also :rcraw:`unitformat`.",
        ),
        # Axes additions
        "axes.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity of the background axes patch.",
        ),
        "axes.inbounds": (
            True,
            g("_validate_bool"),
            "Whether to exclude out-of-bounds data when determining the default *y* (*x*) "
            "axis limits and the *x* (*y*) axis limits have been locked.",
        ),
        "axes.margin": (
            g("MARGIN"),
            g("_validate_float"),
            "The fractional *x* and *y* axis margins when limits are unset.",
        ),
        "bar.bar_labels": (
            False,
            g("_validate_bool"),
            "Add value of the bars to the bar labels",
        ),
        # Country borders
        "borders": (False, g("_validate_bool"), "Toggles country border lines on and off."),
        "borders.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity for country border lines.",
        ),
        "borders.color": (
            g("BLACK"),
            g("_validate_color"),
            "Line color for country border lines.",
        ),
        "borders.linewidth": (
            g("LINEWIDTH"),
            g("_validate_pt"),
            "Line width for country border lines.",
        ),
        "borders.zorder": (
            g("ZLINES"),
            g("_validate_float"),
            "Z-order for country border lines.",
        ),
        "borders.rasterized": (
            False,
            g("_validate_bool"),
            "Toggles rasterization on or off for border feature in GeoAxes.",
        ),
        # Bottom subplot labels
        "bottomlabel.color": (
            g("BLACK"),
            g("_validate_color"),
            "Font color for column labels on the bottom of the figure.",
        ),
        "bottomlabel.pad": (
            g("TITLEPAD"),
            g("_validate_pt"),
            "Padding between axes content and column labels on the bottom of the figure."
            + g("_addendum_pt"),
        ),
        "bottomlabel.rotation": (
            "horizontal",
            g("_validate_rotation"),
            "Rotation for column labels at the bottom of the figure."
            + g("_addendum_rotation"),
        ),
        "bottomlabel.size": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Font size for column labels on the bottom of the figure." + g("_addendum_font"),
        ),
        "bottomlabel.weight": (
            "bold",
            g("_validate_fontweight"),
            "Font weight for column labels on the bottom of the figure.",
        ),
        "cftime.time_unit": (
            "days since 2000-01-01",
            g("_validate_string"),
            "Time unit for non-Gregorian calendars.",
        ),
        "cftime.resolution": (
            "DAILY",
            g("_validate_cftime_resolution"),
            "Default time resolution for non-Gregorian calendars.",
        ),
        "cftime.time_resolution_format": (
            {
                "SECONDLY": "%S",
                "MINUTELY": "%M",
                "HOURLY": "%H",
                "DAILY": "%d",
                "MONTHLY": "%m",
                "YEARLY": "%Y",
            },
            g("_validate_cftime_resolution_format"),
            "Dict used for formatting non-Gregorian calendars.",
        ),
        "cftime.max_display_ticks": (
            7,
            g("_validate_int"),
            "Number of ticks to display for cftime units.",
        ),
        # Coastlines
        "coast": (False, g("_validate_bool"), "Toggles coastline lines on and off."),
        "coast.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity for coast lines",
        ),
        "coast.color": (g("BLACK"), g("_validate_color"), "Line color for coast lines."),
        "coast.linewidth": (g("LINEWIDTH"), g("_validate_pt"), "Line width for coast lines."),
        "coast.zorder": (g("ZLINES"), g("_validate_float"), "Z-order for coast lines."),
        "coast.rasterized": (
            False,
            g("_validate_bool"),
            "Toggles the rasterization of the coastlines feature for GeoAxes.",
        ),
        # Colorbars
        "colorbar.center_levels": (
            False,
            g("_validate_bool"),
            "Center the ticks in the center of each segment.",
        ),
        "colorbar.edgecolor": (
            g("BLACK"),
            g("_validate_color"),
            "Color for the inset colorbar frame edge.",
        ),
        "colorbar.extend": (
            1.3,
            g("_validate_em"),
            'Length of rectangular or triangular "extensions" for panel colorbars.'
            + g("_addendum_em"),
        ),
        "colorbar.outline": (
            True,
            g("_validate_bool"),
            "Whether to draw a frame around the colorbar.",
        ),
        "colorbar.labelrotation": (
            "auto",
            g("_validate_float_or_auto"),
            "Rotation of colorbar labels.",
        ),
        "colorbar.fancybox": (
            False,
            g("_validate_bool"),
            'Whether to use a "fancy" round bounding box for inset colorbar frames.',
        ),
        "colorbar.framealpha": (
            g("FRAMEALPHA"),
            g("_validate_float"),
            "Opacity for inset colorbar frames.",
        ),
        "colorbar.facecolor": (
            g("WHITE"),
            g("_validate_color"),
            "Color for the inset colorbar frame.",
        ),
        "colorbar.frameon": (
            True,
            g("_validate_bool"),
            "Whether to draw a frame behind inset colorbars.",
        ),
        "colorbar.grid": (
            False,
            g("_validate_bool"),
            "Whether to draw borders between each level of the colorbar.",
        ),
        "colorbar.insetextend": (
            0.9,
            g("_validate_em"),
            'Length of rectangular or triangular "extensions" for inset colorbars.'
            + g("_addendum_em"),
        ),
        "colorbar.insetlength": (
            8,
            g("_validate_em"),
            "Length of inset colorbars." + g("_addendum_em"),
        ),
        "colorbar.insetpad": (
            0.7,
            g("_validate_em"),
            "Padding between axes edge and inset colorbars." + g("_addendum_em"),
        ),
        "colorbar.insetwidth": (
            1.2,
            g("_validate_em"),
            "Width of inset colorbars." + g("_addendum_em"),
        ),
        "colorbar.length": (1, g("_validate_em"), "Length of outer colorbars."),
        "colorbar.loc": (
            "right",
            g("_validate_belongs")(*g("COLORBAR_LOCS")),
            "Inset colorbar location. "
            "For options see the :ref:`location table <colorbar_table>`.",
        ),
        "colorbar.width": (
            0.2,
            g("_validate_in"),
            "Width of outer colorbars." + g("_addendum_in"),
        ),
        "colorbar.rasterized": (
            False,
            g("_validate_bool"),
            "Whether to use rasterization for colorbar solids.",
        ),
        "colorbar.shadow": (
            False,
            g("_validate_bool"),
            "Whether to add a shadow underneath inset colorbar frames.",
        ),
        # Color cycle additions
        "cycle": (
            g("CYCLE"),
            g("_validate_cmap")("discrete", cycle=True),
            "Name of the color cycle assigned to :rcraw:`axes.prop_cycle`.",
        ),
        # Colormap additions
        "cmap": (
            g("CMAPSEQ"),
            g("_validate_cmap")("continuous"),
            "Alias for :rcraw:`cmap.sequential` and :rcraw:`image.cmap`.",
        ),
        "cmap.autodiverging": (
            True,
            g("_validate_bool"),
            "Whether to automatically apply a diverging colormap and "
            "normalizer based on the data.",
        ),
        "cmap.qualitative": (
            g("CMAPCAT"),
            g("_validate_cmap")("discrete"),
            "Default colormap for qualitative datasets.",
        ),
        "cmap.cyclic": (
            g("CMAPCYC"),
            g("_validate_cmap")("continuous"),
            "Default colormap for cyclic datasets.",
        ),
        "cmap.discrete": (
            None,
            g("_validate_or_none")(g("_validate_bool")),
            "If ``True``, `~ultraplot.colors.DiscreteNorm` is used for every colormap plot. "
            "If ``False``, it is never used. If ``None``, it is used for all plot types "
            "except `imshow`, `matshow`, `spy`, `hexbin`, and `hist2d`.",
        ),
        "cmap.diverging": (
            g("CMAPDIV"),
            g("_validate_cmap")("continuous"),
            "Default colormap for diverging datasets.",
        ),
        "cmap.inbounds": (
            True,
            g("_validate_bool"),
            "If ``True`` and the *x* and *y* axis limits are fixed, only in-bounds data "
            "is considered when determining the default colormap `vmin` and `vmax`.",
        ),
        "cmap.levels": (
            11,
            g("_validate_int"),
            "Default number of `~ultraplot.colors.DiscreteNorm` levels for plotting "
            "commands that use colormaps.",
        ),
        "cmap.listedthresh": (
            64,
            g("_validate_int"),
            "Native `~matplotlib.colors.ListedColormap`\\ s with more colors than "
            "this are converted to :class:`~ultraplot.colors.ContinuousColormap` rather than "
            ":class:`~ultraplot.colors.DiscreteColormap`. This helps translate continuous "
            "colormaps from external projects.",
        ),
        "cmap.lut": (
            256,
            g("_validate_int"),
            "Number of colors in the colormap lookup table. "
            "Alias for :rcraw:`image.lut`.",
        ),
        "cmap.robust": (
            False,
            g("_validate_bool"),
            "If ``True``, the default colormap `vmin` and `vmax` are chosen using the "
            "2nd to 98th percentiles rather than the minimum and maximum.",
        ),
        "cmap.sequential": (
            g("CMAPSEQ"),
            g("_validate_cmap")("continuous"),
            "Default colormap for sequential datasets. Alias for :rcraw:`image.cmap`.",
        ),
        # Special setting
        "edgefix": (
            True,
            g("_validate_bool"),
            'Whether to fix issues with "white lines" appearing between patches '
            "in saved vector graphics and with vector graphic backends. Applies "
            "to colorbar levels and bar, area, pcolor, and contour plots.",
        ),
        # Font settings
        "font.name": (g("FONTNAME"), g("_validate_fontname"), "Alias for :rcraw:`font.family`."),
        "font.small": (
            g("SMALLSIZE"),
            g("_validate_fontsize"),
            "Alias for :rcraw:`font.smallsize`.",
        ),
        "font.smallsize": (
            g("SMALLSIZE"),
            g("_validate_fontsize"),
            "Meta setting that changes the label-like sizes ``axes.labelsize``, "
            "``legend.fontsize``, ``tick.labelsize``, and ``grid.labelsize``. Default is "
            "``'medium'`` (equivalent to :rcraw:`font.size`)." + g("_addendum_font"),
        ),
        "font.large": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Alias for :rcraw:`font.largesize`.",
        ),
        "font.largesize": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Meta setting that changes the title-like sizes ``abc.size``, ``title.size``, "
            "``suptitle.size``, ``leftlabel.size``, ``rightlabel.size``, etc. Default is "
            "``'med-large'`` (i.e. 1.1 times :rcraw:`font.size`)." + g("_addendum_font"),
        ),
        # Formatter settings
        "formatter.timerotation": (
            "vertical",
            g("_validate_rotation"),
            "Rotation for *x* axis datetime tick labels." + g("_addendum_rotation"),
        ),
        "formatter.zerotrim": (
            True,
            g("_validate_bool"),
            "Whether to trim trailing decimal zeros on tick labels.",
        ),
        "formatter.log": (
            False,
            g("_validate_bool"),
            "Whether to use log formatting (e.g., $10^{4}$) for "
            "logarithmically scaled axis tick labels.",
        ),
        "formatter.limits": (
            [-5, 6],  # must be list or else validated
            g("_validate")["axes.formatter.limits"],
            "Alias for :rcraw:`axes.formatter.limits`.",
        ),
        "formatter.min_exponent": (
            0,
            g("_validate")["axes.formatter.min_exponent"],
            "Alias for :rcraw:`axes.formatter.min_exponent`.",
        ),
        "formatter.offset_threshold": (
            4,
            g("_validate")["axes.formatter.offset_threshold"],
            "Alias for :rcraw:`axes.formatter.offset_threshold`.",
        ),
        "formatter.use_locale": (
            False,
            g("_validate_bool"),
            "Alias for :rcraw:`axes.formatter.use_locale`.",
        ),
        "formatter.use_mathtext": (
            g("MATHTEXT"),
            g("_validate_bool"),
            "Alias for :rcraw:`axes.formatter.use_mathtext`.",
        ),
        "formatter.use_offset": (
            True,
            g("_validate_bool"),
            "Alias for :rcraw:`axes.formatter.useOffset`.",
        ),
        # Geographic axes settings
        "geo.backend": (
            "cartopy",
            g("_validate_belongs")("cartopy", "basemap"),
            "The backend used for `~ultraplot.axes.GeoAxes`. Must be "
            "either 'cartopy' or 'basemap'.",
        ),
        "geo.extent": (
            "globe",
            g("_validate_belongs")("globe", "auto"),
            "If ``'globe'``, the extent of cartopy `~ultraplot.axes.GeoAxes` is always "
            "global. If ``'auto'``, the extent is automatically adjusted based on "
            "plotted content. Default is ``'globe'``.",
        ),
        "geo.round": (
            True,
            g("_validate_bool"),
            "If ``True`` (the default), polar `~ultraplot.axes.GeoAxes` like ``'npstere'`` "
            "and ``'spstere'`` are bounded with circles rather than squares.",
        ),
        # Graphs
        "graph.draw_nodes": (
            True,
            g("_validate_bool_or_iterable"),
            "If ``True`` draws the nodes for all the nodes, otherwise only the nodes that are in the iterable.",
        ),
        "graph.draw_edges": (
            True,
            g("_validate_bool_or_iterable"),
            "If ``True`` draws the edges for all the edges, otherwise only the edges that are in the iterable.",
        ),
        "graph.draw_labels": (
            False,
            g("_validate_bool_or_iterable"),
            "If ``True`` draws the labels for all the nodes, otherwise only the nodes that are in the iterable.",
        ),
        "graph.draw_grid": (
            False,
            g("_validate_bool"),
            "If ``True`` draws the grid for all the edges, otherwise only the edges that are in the iterable.",
        ),
        "graph.aspect": (
            "equal",
            g("_validate_belongs")("equal", "auto"),
            "The aspect ratio of the graph.",
        ),
        "graph.facecolor": ("none", g("_validate_color"), "The facecolor of the graph."),
        "graph.draw_spines": (
            False,
            g("_validate_bool_or_iterable"),
            "If ``True`` draws the spines for all the edges, otherwise only the edges that are in the iterable.",
        ),
        "graph.rescale": (
            True,
            g("_validate_bool"),
            "If ``True`` rescales the graph to fit the data.",
        ),
        # Gridlines
        # NOTE: Here 'grid' and 'gridminor' or *not* aliases for native 'axes.grid' and
        # invented 'axes.gridminor' because native 'axes.grid' controls both major *and*
        # minor gridlines. Must handle it independently from these settings.
        "grid": (True, g("_validate_bool"), "Toggle major gridlines on and off."),
        "grid.below": (
            g("GRIDBELOW"),  # like axes.axisbelow
            g("_validate_belongs")(False, "line", True),
            "Alias for :rcraw:`axes.axisbelow`. If ``True``, draw gridlines below "
            "everything. If ``True``, draw them above everything. If ``'line'``, "
            "draw them above patches but below lines and markers.",
        ),
        "grid.checkoverlap": (
            True,
            g("_validate_bool"),
            "Whether to have cartopy automatically check for and remove overlapping "
            "`~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.dmslabels": (
            True,
            g("_validate_bool"),
            "Whether to use degrees-minutes-seconds rather than decimals for "
            "cartopy `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.geolabels": (
            True,
            g("_validate_bool"),
            "Whether to include the ``'geo'`` spine in cartopy >= 0.20 when otherwise "
            "toggling left, right, bottom, or top `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.inlinelabels": (
            False,
            g("_validate_bool"),
            "Whether to add inline labels for cartopy `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.labels": (
            False,
            g("_validate_bool"),
            "Whether to add outer labels for `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.labelcolor": (
            g("BLACK"),
            g("_validate_color"),
            "Font color for `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.labelpad": (
            g("GRIDPAD"),
            g("_validate_pt"),
            "Padding between the map boundary and cartopy `~ultraplot.axes.GeoAxes` "
            "gridline labels." + g("_addendum_pt"),
        ),
        "grid.labelsize": (
            g("SMALLSIZE"),
            g("_validate_fontsize"),
            "Font size for `~ultraplot.axes.GeoAxes` gridline labels." + g("_addendum_font"),
        ),
        "grid.labelweight": (
            "normal",
            g("_validate_fontweight"),
            "Font weight for `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.nsteps": (
            250,
            g("_validate_int"),
            "Number of points used to draw cartopy `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.pad": (g("GRIDPAD"), g("_validate_pt"), "Alias for :rcraw:`grid.labelpad`."),
        "grid.rotatelabels": (
            False,  # False limits projections where labels are available
            g("_validate_bool"),
            "Whether to rotate cartopy `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.style": (
            "-",
            g("_validate_linestyle"),
            "Major gridline style. Alias for :rcraw:`grid.linestyle`.",
        ),
        "grid.width": (
            g("LINEWIDTH"),
            g("_validate_pt"),
            "Major gridline width. Alias for :rcraw:`grid.linewidth`.",
        ),
        "grid.widthratio": (
            g("GRIDRATIO"),
            g("_validate_float"),
            "Ratio of minor gridline width to major gridline width.",
        ),
        # Minor gridlines
        "gridminor": (False, g("_validate_bool"), "Toggle minor gridlines on and off."),
        "gridminor.alpha": (g("GRIDALPHA"), g("_validate_float"), "Minor gridline opacity."),
        "gridminor.color": (g("BLACK"), g("_validate_color"), "Minor gridline color."),
        "gridminor.linestyle": (
            g("GRIDSTYLE"),
            g("_validate_linestyle"),
            "Minor gridline style.",
        ),
        "gridminor.linewidth": (
            g("GRIDRATIO") * g("LINEWIDTH"),
            g("_validate_pt"),
            "Minor gridline width.",
        ),
        "gridminor.style": (
            g("GRIDSTYLE"),
            g("_validate_linestyle"),
            "Minor gridline style. Alias for :rcraw:`gridminor.linestyle`.",
        ),
        "gridminor.width": (
            g("GRIDRATIO") * g("LINEWIDTH"),
            g("_validate_pt"),
            "Minor gridline width. Alias for :rcraw:`gridminor.linewidth`.",
        ),
        # Backend stuff
        "inlineformat": (
            "retina",
            g("_validate_belongs")("svg", "pdf", "retina", "png", "jpeg"),
            "The inline backend figure format. Valid formats include "
            "``'svg'``, ``'pdf'``, ``'retina'``, ``'png'``, and ``jpeg``.",
        ),
        # Inner borders
        "innerborders": (
            False,
            g("_validate_bool"),
            "Toggles internal political border lines (e.g. states and provinces) "
            "on and off.",
        ),
        "innerborders.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity for internal political border lines",
        ),
        "innerborders.color": (
            g("BLACK"),
            g("_validate_color"),
            "Line color for internal political border lines.",
        ),
        "innerborders.linewidth": (
            g("LINEWIDTH"),
            g("_validate_pt"),
            "Line width for internal political border lines.",
        ),
        "innerborders.zorder": (
            g("ZLINES"),
            g("_validate_float"),
            "Z-order for internal political border lines.",
        ),
        # Axis label settings
        "label.color": (g("BLACK"), g("_validate_color"), "Alias for :rcraw:`axes.labelcolor`."),
        "label.pad": (
            g("LABELPAD"),
            g("_validate_pt"),
            "Alias for :rcraw:`axes.labelpad`." + g("_addendum_pt"),
        ),
        "label.size": (
            g("SMALLSIZE"),
            g("_validate_fontsize"),
            "Alias for :rcraw:`axes.labelsize`." + g("_addendum_font"),
        ),
        "label.weight": (
            "normal",
            g("_validate_fontweight"),
            "Alias for :rcraw:`axes.labelweight`.",
        ),
        # Lake patches
        "lakes": (False, g("_validate_bool"), "Toggles lake patches on and off."),
        "lakes.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity for lake patches",
        ),
        "lakes.color": (g("WHITE"), g("_validate_color"), "Face color for lake patches."),
        "lakes.zorder": (g("ZPATCHES"), g("_validate_float"), "Z-order for lake patches."),
        "lakes.rasterized": (
            False,
            g("_validate_bool"),
            "Toggles rasterization on or off for lake feature",
        ),
        # Land patches
        "land": (False, g("_validate_bool"), "Toggles land patches on and off."),
        "land.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity for land patches",
        ),
        "land.color": (g("BLACK"), g("_validate_color"), "Face color for land patches."),
        "land.zorder": (g("ZPATCHES"), g("_validate_float"), "Z-order for land patches."),
        "land.rasterized": (
            False,
            g("_validate_bool"),
            "Toggles the rasterization of the land feature.",
        ),
        # Left subplot labels
        "leftlabel.color": (
            g("BLACK"),
            g("_validate_color"),
            "Font color for row labels on the left-hand side.",
        ),
        "leftlabel.pad": (
            g("TITLEPAD"),
            g("_validate_pt"),
            "Padding between axes content and row labels on the left-hand side."
            + g("_addendum_pt"),
        ),
        "leftlabel.rotation": (
            "vertical",
            g("_validate_rotation"),
            "Rotation for row labels on the left-hand side." + g("_addendum_rotation"),
        ),
        "leftlabel.size": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Font size for row labels on the left-hand side." + g("_addendum_font"),
        ),
        "lollipop.markersize": (
            36,
            g("_validate_float"),
            "Size of lollipops in the lollipop plot.",
        ),
        "lollipop.stemcolor": (
            g("BLACK"),
            g("_validate_color"),
            "Color of lollipop lines.",
        ),
        "lollipop.stemwidth": (
            g("LINEWIDTH"),
            g("_validate_pt"),
            "Width of the stem",
        ),
        "lollipop.stemlinestyle": (
            "-",
            g("_validate_linestyle"),
            "Line style of lollipop lines.",
        ),
        "leftlabel.weight": (
            "bold",
            g("_validate_fontweight"),
            "Font weight for row labels on the left-hand side.",
        ),
        # Meta settings
        "margin": (
            g("MARGIN"),
            g("_validate_float"),
            "The fractional *x* and *y* axis data margins when limits are unset. "
            "Alias for :rcraw:`axes.margin`.",
        ),
        "meta.edgecolor": (
            g("BLACK"),
            g("_validate_color"),
            "Color of axis spines, tick marks, tick labels, and labels.",
        ),
        "meta.color": (
            g("BLACK"),
            g("_validate_color"),
            "Color of axis spines, tick marks, tick labels, and labels. "
            "Alias for :rcraw:`meta.edgecolor`.",
        ),
        "meta.linewidth": (
            g("LINEWIDTH"),
            g("_validate_pt"),
            "Thickness of axis spines and major tick lines.",
        ),
        "meta.width": (
            g("LINEWIDTH"),
            g("_validate_pt"),
            "Thickness of axis spines and major tick lines. "
            "Alias for :rcraw:`meta.linewidth`.",
        ),
        # For negative positive patches
        "negcolor": (
            "blue7",
            g("_validate_color"),
            "Color for negative bars and shaded areas when using ``negpos=True``. "
            "See also :rcraw:`poscolor`.",
        ),
        "poscolor": (
            "red7",
            g("_validate_color"),
            "Color for positive bars and shaded areas when using ``negpos=True``. "
            "See also :rcraw:`negcolor`.",
        ),
        # Ocean patches
        "ocean": (False, g("_validate_bool"), "Toggles ocean patches on and off."),
        "ocean.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity for ocean patches",
        ),
        "ocean.color": (g("WHITE"), g("_validate_color"), "Face color for ocean patches."),
        "ocean.zorder": (g("ZPATCHES"), g("_validate_float"), "Z-order for ocean patches."),
        "ocean.rasterized": (
            False,
            g("_validate_bool"),
            "Turns rasterization on or off for the oceans feature for GeoAxes.",
        ),
        # Geographic resolution
        "reso": (
            "lo",
            g("_validate_belongs")("lo", "med", "hi", "x-hi", "xx-hi"),
            "Resolution for `~ultraplot.axes.GeoAxes` geographic features. "
            "Must be one of ``'lo'``, ``'med'``, ``'hi'``, ``'x-hi'``, or ``'xx-hi'``.",
        ),
        # Right subplot labels
        "rightlabel.color": (
            g("BLACK"),
            g("_validate_color"),
            "Font color for row labels on the right-hand side.",
        ),
        "rightlabel.pad": (
            g("TITLEPAD"),
            g("_validate_pt"),
            "Padding between axes content and row labels on the right-hand side."
            + g("_addendum_pt"),
        ),
        "rightlabel.rotation": (
            "vertical",
            g("_validate_rotation"),
            "Rotation for row labels on the right-hand side." + g("_addendum_rotation"),
        ),
        "rightlabel.size": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Font size for row labels on the right-hand side." + g("_addendum_font"),
        ),
        "rightlabel.weight": (
            "bold",
            g("_validate_fontweight"),
            "Font weight for row labels on the right-hand side.",
        ),
        # River lines
        "rivers": (False, g("_validate_bool"), "Toggles river lines on and off."),
        "rivers.alpha": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Opacity for river lines.",
        ),
        "rivers.color": (g("BLACK"), g("_validate_color"), "Line color for river lines."),
        "rivers.linewidth": (g("LINEWIDTH"), g("_validate_pt"), "Line width for river lines."),
        "rivers.zorder": (g("ZLINES"), g("_validate_float"), "Z-order for river lines."),
        "rivers.rasterized": (
            False,
            g("_validate_bool"),
            "Toggles rasterization on or off for rivers feature for GeoAxes.",
        ),
        # Circlize settings
        "chord.start": (
            0.0,
            g("_validate_float"),
            "Start angle for chord diagrams.",
        ),
        "chord.end": (
            360.0,
            g("_validate_float"),
            "End angle for chord diagrams.",
        ),
        "chord.space": (
            0.0,
            g("_validate_float_or_iterable"),
            "Inter-sector spacing for chord diagrams.",
        ),
        "chord.endspace": (
            True,
            g("_validate_bool"),
            "Whether to add an ending space gap for chord diagrams.",
        ),
        "chord.r_lim": (
            (97.0, 100.0),
            g("_validate_tuple_float_2"),
            "Radial limits for chord diagrams.",
        ),
        "chord.ticks_interval": (
            None,
            g("_validate_or_none")(g("_validate_int")),
            "Tick interval for chord diagrams.",
        ),
        "chord.order": (
            None,
            g("_validate_or_none")(g("_validate_string_or_iterable")),
            "Ordering of sectors for chord diagrams.",
        ),
        "radar.r_lim": (
            (0.0, 100.0),
            g("_validate_tuple_float_2"),
            "Radial limits for radar charts.",
        ),
        "radar.vmin": (
            0.0,
            g("_validate_float"),
            "Minimum value for radar charts.",
        ),
        "radar.vmax": (
            100.0,
            g("_validate_float"),
            "Maximum value for radar charts.",
        ),
        "radar.fill": (
            True,
            g("_validate_bool"),
            "Whether to fill radar chart polygons.",
        ),
        "radar.marker_size": (
            0,
            g("_validate_int"),
            "Marker size for radar charts.",
        ),
        "radar.bg_color": (
            "#eeeeee80",
            g("_validate_or_none")(g("_validate_color")),
            "Background color for radar charts.",
        ),
        "radar.circular": (
            False,
            g("_validate_bool"),
            "Whether to use circular radar charts.",
        ),
        "radar.show_grid_label": (
            True,
            g("_validate_bool"),
            "Whether to show grid labels on radar charts.",
        ),
        "radar.grid_interval_ratio": (
            0.2,
            g("_validate_or_none")(g("_validate_float")),
            "Grid interval ratio for radar charts.",
        ),
        "phylogeny.start": (
            0.0,
            g("_validate_float"),
            "Start angle for phylogeny plots.",
        ),
        "phylogeny.end": (
            360.0,
            g("_validate_float"),
            "End angle for phylogeny plots.",
        ),
        "phylogeny.r_lim": (
            (50.0, 100.0),
            g("_validate_tuple_float_2"),
            "Radial limits for phylogeny plots.",
        ),
        "phylogeny.format": (
            "newick",
            g("_validate_string"),
            "Input format for phylogeny plots.",
        ),
        "phylogeny.outer": (
            True,
            g("_validate_bool"),
            "Whether to place phylogeny leaves on the outer edge.",
        ),
        "phylogeny.align_leaf_label": (
            True,
            g("_validate_bool"),
            "Whether to align phylogeny leaf labels.",
        ),
        "phylogeny.ignore_branch_length": (
            False,
            g("_validate_bool"),
            "Whether to ignore branch lengths in phylogeny plots.",
        ),
        "phylogeny.leaf_label_size": (
            None,
            g("_validate_or_none")(g("_validate_float")),
            "Leaf label font size for phylogeny plots.",
        ),
        "phylogeny.leaf_label_rmargin": (
            2.0,
            g("_validate_float"),
            "Radial margin for phylogeny leaf labels.",
        ),
        "phylogeny.reverse": (
            False,
            g("_validate_bool"),
            "Whether to reverse phylogeny orientation.",
        ),
        "phylogeny.ladderize": (
            False,
            g("_validate_bool"),
            "Whether to ladderize phylogeny branches.",
        ),
        # Sankey diagrams
        "sankey.align": (
            "center",
            g("_validate_belongs")("center", "left", "right", "justify"),
            "Horizontal alignment of nodes.",
        ),
        "sankey.connect": (
            (0, 0),
            g("_validate_tuple_int_2"),
            "Connection path for Sankey diagram.",
        ),
        "sankey.flow_labels": (
            False,
            g("_validate_bool"),
            "Whether to draw flow labels.",
        ),
        "sankey.flow_label_pos": (
            0.5,
            g("_validate_float"),
            "Position of flow labels along the flow.",
        ),
        "sankey.flow_sort": (
            True,
            g("_validate_bool"),
            "Whether to sort flows.",
        ),
        "sankey.node_labels": (
            True,
            g("_validate_bool"),
            "Whether to draw node labels.",
        ),
        "sankey.node_label_offset": (
            0.01,
            g("_validate_float"),
            "Offset for node labels.",
        ),
        "sankey.node_label_outside": (
            "auto",
            g("_validate_bool_or_string"),
            "Position of node labels relative to the node.",
        ),
        "sankey.other_label": (
            "Other",
            g("_validate_string"),
            "Label for 'other' category in Sankey diagram.",
        ),
        "sankey.pathlabel": (
            "",
            g("_validate_string"),
            "Label for the patch.",
        ),
        "sankey.pathlengths": (
            0.25,
            g("_validate_float"),
            "Path lengths for Sankey diagram.",
        ),
        "sankey.rotation": (
            0.0,
            g("_validate_float"),
            "Rotation of the Sankey diagram.",
        ),
        "sankey.trunklength": (
            1.0,
            g("_validate_float"),
            "Trunk length for Sankey diagram.",
        ),
        # Subplots settings
        "subplots.align": (
            False,
            g("_validate_bool"),
            "Whether to align axis labels during draw. See `aligning labels "
            "<https://matplotlib.org/stable/gallery/subplots_axes_and_figures/align_labels_demo.html>`__.",  # noqa: E501
        ),
        "subplots.equalspace": (
            False,
            g("_validate_bool"),
            "Whether to make the tight layout algorithm assign the same space for "
            "every row and the same space for every column.",
        ),
        "subplots.groupspace": (
            True,
            g("_validate_bool"),
            "Whether to make the tight layout algorithm consider space between only "
            'adjacent subplot "groups" rather than every subplot in the row or column.',
        ),
        "subplots.innerpad": (
            1,
            g("_validate_em"),
            "Padding between adjacent subplots." + g("_addendum_em"),
        ),
        "subplots.outerpad": (
            0.5,
            g("_validate_em"),
            "Padding around figure edge." + g("_addendum_em"),
        ),
        "subplots.panelpad": (
            0.5,
            g("_validate_em"),
            "Padding between subplots and panels, and between stacked panels."
            + g("_addendum_em"),
        ),
        "subplots.panelwidth": (
            0.5,
            g("_validate_in"),
            "Width of side panels." + g("_addendum_in"),
        ),
        "subplots.refwidth": (
            2.5,
            g("_validate_in"),
            "Default width of the reference subplot." + g("_addendum_in"),
        ),
        "subplots.share": (
            "auto",
            g("_validate_belongs")(
                0, 1, 2, 3, 4, False, "labels", "limits", True, "all", "auto"
            ),
            "The axis sharing level, one of ``0``, ``1``, ``2``, or ``3``, or the "
            "more intuitive aliases ``False``, ``'labels'``, ``'limits'``, ``True``, "
            "or ``'auto'``. See `~ultraplot.figure.Figure` for details.",
        ),
        "subplots.span": (
            True,
            g("_validate_bool"),
            "Toggles spanning axis labels. See `~ultraplot.ui.subplots` for details.",
        ),
        "subplots.tight": (
            True,
            g("_validate_bool"),
            "Whether to auto-adjust the subplot spaces and figure margins.",
        ),
        "subplots.pixelsnap": (
            False,
            g("_validate_bool"),
            "Whether to snap subplot bounds to the renderer pixel grid during draw.",
        ),
        # Super title settings
        "suptitle.color": (g("BLACK"), g("_validate_color"), "Figure title color."),
        "suptitle.pad": (
            g("TITLEPAD"),
            g("_validate_pt"),
            "Padding between axes content and the figure super title." + g("_addendum_pt"),
        ),
        "suptitle.size": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Figure title font size." + g("_addendum_font"),
        ),
        "suptitle.weight": ("bold", g("_validate_fontweight"), "Figure title font weight."),
        # Tick settings
        "tick.color": (g("BLACK"), g("_validate_color"), "Major and minor tick color."),
        "tick.dir": (
            g("TICKDIR"),
            g("_validate_belongs")("in", "out", "inout"),
            "Major and minor tick direction. Must be one of "
            "``'out'``, ``'in'``, or ``'inout'``.",
        ),
        "tick.labelcolor": (g("BLACK"), g("_validate_color"), "Axis tick label color."),
        "tick.labelpad": (
            g("TICKPAD"),
            g("_validate_pt"),
            "Padding between ticks and tick labels." + g("_addendum_pt"),
        ),
        "tick.labelsize": (
            g("SMALLSIZE"),
            g("_validate_fontsize"),
            "Axis tick label font size." + g("_addendum_font"),
        ),
        "tick.labelweight": (
            "normal",
            g("_validate_fontweight"),
            "Axis tick label font weight.",
        ),
        "tick.len": (g("TICKLEN"), g("_validate_pt"), "Length of major ticks in points."),
        "tick.lenratio": (
            g("TICKLENRATIO"),
            g("_validate_float"),
            "Ratio of minor tickline length to major tickline length.",
        ),
        "tick.linewidth": (g("LINEWIDTH"), g("_validate_pt"), "Major tickline width."),
        "tick.minor": (
            g("TICKMINOR"),
            g("_validate_bool"),
            "Toggles minor ticks on and off.",
        ),
        "tick.pad": (g("TICKPAD"), g("_validate_pt"), "Alias for :rcraw:`tick.labelpad`."),
        "tick.width": (
            g("LINEWIDTH"),
            g("_validate_pt"),
            "Major tickline width. Alias for :rcraw:`tick.linewidth`.",
        ),
        "tick.widthratio": (
            g("TICKWIDTHRATIO"),
            g("_validate_float"),
            "Ratio of minor tickline width to major tickline width.",
        ),
        # Title settings
        "title.above": (
            True,
            g("_validate_belongs")(False, True, "panels"),
            "Whether to move outer titles and a-b-c labels above panels, colorbars, or "
            "legends that are above the axes. If the string 'panels' then text is only "
            "redirected above axes panels. Otherwise should be boolean.",
        ),
        "title.border": (
            True,
            g("_validate_bool"),
            "Whether to draw a white border around titles "
            "when :rcraw:`title.loc` is inside the axes.",
        ),
        "title.borderwidth": (1.5, g("_validate_pt"), "Width of the border around titles."),
        "title.bbox": (
            False,
            g("_validate_bool"),
            "Whether to draw semi-transparent bounding boxes around titles "
            "when :rcraw:`title.loc` is inside the axes.",
        ),
        "title.bboxcolor": (g("WHITE"), g("_validate_color"), "Axes title bounding box color."),
        "title.bboxstyle": (
            "square",
            g("_validate_boxstyle"),
            "Axes title bounding box style.",
        ),
        "title.bboxalpha": (0.5, g("_validate_float"), "Axes title bounding box opacity."),
        "title.bboxpad": (
            None,
            g("_validate_or_none")(g("_validate_pt")),
            "Padding for the title bounding box. By default this is scaled "
            "to make the box flush against the axes edge." + g("_addendum_pt"),
        ),
        "title.color": (
            g("BLACK"),
            g("_validate_color"),
            "Axes title color. Alias for :rcraw:`axes.titlecolor`.",
        ),
        "title.loc": (
            "center",
            g("_validate_belongs")(*g("TEXT_LOCS")),
            "Title position. For options see the :ref:`location table <title_table>`.",
        ),
        "title.pad": (
            g("TITLEPAD"),
            g("_validate_pt"),
            "Padding between the axes edge and the inner and outer titles and "
            "a-b-c labels. Alias for :rcraw:`axes.titlepad`." + g("_addendum_pt"),
        ),
        "title.size": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Axes title font size. Alias for :rcraw:`axes.titlesize`." + g("_addendum_font"),
        ),
        "title.weight": (
            "normal",
            g("_validate_fontweight"),
            "Axes title font weight. Alias for :rcraw:`axes.titleweight`.",
        ),
        # Top subplot label settings
        "toplabel.color": (
            g("BLACK"),
            g("_validate_color"),
            "Font color for column labels on the top of the figure.",
        ),
        "toplabel.pad": (
            g("TITLEPAD"),
            g("_validate_pt"),
            "Padding between axes content and column labels on the top of the figure."
            + g("_addendum_pt"),
        ),
        "toplabel.rotation": (
            "horizontal",
            g("_validate_rotation"),
            "Rotation for column labels at the top of the figure." + g("_addendum_rotation"),
        ),
        "toplabel.size": (
            g("LARGESIZE"),
            g("_validate_fontsize"),
            "Font size for column labels on the top of the figure." + g("_addendum_font"),
        ),
        "toplabel.weight": (
            "bold",
            g("_validate_fontweight"),
            "Font weight for column labels on the top of the figure.",
        ),
        # Unit formatting
        "unitformat": (
            "L",
            g("_validate_string"),
            "The format string used to format `pint.Quantity` default unit labels "
            "using ``format(units, unitformat)``. See also :rcraw:`autoformat`.",
        ),
        "ultraplot.check_for_latest_version": (
            False,
            g("_validate_bool"),
            "Whether to check for the latest version of UltraPlot on PyPI when importing",
        ),
        "ultraplot.eager_import": (
            False,
            g("_validate_bool"),
            "Whether to import the full public API during setup instead of lazily.",
        ),
    }

    plot_entries = _section_entries(
        raw_settings,
        lambda key: key.startswith(_PLOT_PREFIXES),
    )
    text_entries = _section_entries(
        raw_settings,
        lambda key: key.startswith(_TEXT_PREFIXES),
    )
    subplot_entries = _section_entries(
        raw_settings,
        lambda key: key.startswith(_SUBPLOT_PREFIX),
    )
    misc_entries = _section_entries(
        raw_settings,
        lambda key: (
            not key.startswith(_PLOT_PREFIXES)
            and not key.startswith(_TEXT_PREFIXES)
            and not key.startswith(_SUBPLOT_PREFIX)
        ),
    )

    return merge_rc_tables(plot_entries, text_entries, subplot_entries, misc_entries)
