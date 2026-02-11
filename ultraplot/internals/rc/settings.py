#!/usr/bin/env python3
"""
Single-source rc setting table with section headers.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .validators import build_validator_aliases

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]

def build_settings_rc_table(ns: Mapping[str, Any]) -> RcTable:
    """Build the core ultraplot rc table from rcsetup namespace symbols."""
    BLACK = ns["BLACK"]
    CMAPCAT = ns["CMAPCAT"]
    CMAPCYC = ns["CMAPCYC"]
    CMAPDIV = ns["CMAPDIV"]
    CMAPSEQ = ns["CMAPSEQ"]
    COLORBAR_LOCS = ns["COLORBAR_LOCS"]
    CYCLE = ns["CYCLE"]
    FONTNAME = ns["FONTNAME"]
    FRAMEALPHA = ns["FRAMEALPHA"]
    GRIDALPHA = ns["GRIDALPHA"]
    GRIDBELOW = ns["GRIDBELOW"]
    GRIDPAD = ns["GRIDPAD"]
    GRIDRATIO = ns["GRIDRATIO"]
    GRIDSTYLE = ns["GRIDSTYLE"]
    LABELPAD = ns["LABELPAD"]
    LARGESIZE = ns["LARGESIZE"]
    LINEWIDTH = ns["LINEWIDTH"]
    MARGIN = ns["MARGIN"]
    MATHTEXT = ns["MATHTEXT"]
    SMALLSIZE = ns["SMALLSIZE"]
    TEXT_LOCS = ns["TEXT_LOCS"]
    TICKDIR = ns["TICKDIR"]
    TICKLEN = ns["TICKLEN"]
    TICKLENRATIO = ns["TICKLENRATIO"]
    TICKMINOR = ns["TICKMINOR"]
    TICKPAD = ns["TICKPAD"]
    TICKWIDTHRATIO = ns["TICKWIDTHRATIO"]
    TITLEPAD = ns["TITLEPAD"]
    WHITE = ns["WHITE"]
    ZLINES = ns["ZLINES"]
    ZPATCHES = ns["ZPATCHES"]
    _addendum_em = ns["_addendum_em"]
    _addendum_font = ns["_addendum_font"]
    _addendum_in = ns["_addendum_in"]
    _addendum_pt = ns["_addendum_pt"]
    _addendum_rotation = ns["_addendum_rotation"]
    _validate = ns["_validate"]
    _validate_abc = ns["_validate_abc"]
    _validate_belongs = ns["_validate_belongs"]
    _validate_bool = ns["_validate_bool"]
    _validate_bool_or_iterable = ns["_validate_bool_or_iterable"]
    _validate_bool_or_string = ns["_validate_bool_or_string"]
    _validate_boxstyle = ns["_validate_boxstyle"]
    _validate_cftime_resolution = ns["_validate_cftime_resolution"]
    _validate_cftime_resolution_format = ns["_validate_cftime_resolution_format"]
    _validate_cmap = ns["_validate_cmap"]
    _validate_color = ns["_validate_color"]
    _validate_em = ns["_validate_em"]
    _validate_float = ns["_validate_float"]
    _validate_float_or_auto = ns["_validate_float_or_auto"]
    _validate_float_or_iterable = ns["_validate_float_or_iterable"]
    _validate_fontname = ns["_validate_fontname"]
    _validate_fontsize = ns["_validate_fontsize"]
    _validate_fontweight = ns["_validate_fontweight"]
    _validate_in = ns["_validate_in"]
    _validate_int = ns["_validate_int"]
    _validate_joinstyle = ns["_validate_joinstyle"]
    _validate_linestyle = ns["_validate_linestyle"]
    _validate_or_none = ns["_validate_or_none"]
    _validate_pt = ns["_validate_pt"]
    _validate_rotation = ns["_validate_rotation"]
    _validate_string = ns["_validate_string"]
    _validate_string_or_iterable = ns["_validate_string_or_iterable"]
    _validate_tuple_float_2 = ns["_validate_tuple_float_2"]
    _validate_tuple_int_2 = ns["_validate_tuple_int_2"]

    validators = build_validator_aliases(ns)
    validate_bool = validators["bool"]
    validate_color = validators["color"]
    validate_float = validators["float"]
    validate_int = validators["int"]
    validate_string = validators["string"]

    return {
        # Plot-type settings
        # Curved quiver settings
        "curved_quiver.arrowsize": (
            1.0,
            validate_float,
            "Default size scaling for arrows in curved quiver plots.",
        ),
        "curved_quiver.arrowstyle": (
            "-|>",
            validate_string,
            "Default arrow style for curved quiver plots.",
        ),
        "curved_quiver.scale": (
            1.0,
            validate_float,
            "Default scale factor for curved quiver plots.",
        ),
        "curved_quiver.grains": (
            15,
            validate_int,
            "Default number of grains (segments) for curved quiver arrows.",
        ),
        "curved_quiver.density": (
            10,
            validate_int,
            "Default density of arrows for curved quiver plots.",
        ),
        "curved_quiver.arrows_at_end": (
            True,
            validate_bool,
            "Whether to draw arrows at the end of curved quiver lines by default.",
        ),
        # Sankey settings
        "sankey.nodepad": (
            0.02,
            validate_float,
            "Vertical padding between nodes in layered sankey diagrams.",
        ),
        "sankey.nodewidth": (
            0.03,
            validate_float,
            "Node width for layered sankey diagrams (axes-relative units).",
        ),
        "sankey.margin": (
            0.05,
            validate_float,
            "Margin around layered sankey diagrams (axes-relative units).",
        ),
        "sankey.flow.alpha": (
            0.75,
            validate_float,
            "Flow transparency for layered sankey diagrams.",
        ),
        "sankey.flow.curvature": (
            0.5,
            validate_float,
            "Flow curvature for layered sankey diagrams.",
        ),
        "sankey.node.facecolor": (
            "0.75",
            validate_color,
            "Default node facecolor for layered sankey diagrams.",
        ),
        "external.shrink": (
            0.9,
            _validate_float,
            "Default shrink factor for external axes containers.",
        ),
        # Stylesheet
        "style": (
            None,
            _validate_or_none(_validate_string),
            "The default matplotlib `stylesheet "
            "<https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html>`__ "  # noqa: E501
            "name. If ``None``, a custom ultraplot style is used. "
            "If ``'default'``, the default matplotlib style is used.",
        ),
        # A-b-c labels
        "abc": (
            False,
            _validate_abc,
            "If ``False`` then a-b-c labels are disabled. If ``True`` the default label "
            "style `a` is used. If string this indicates the style and must contain the "
            "character `a` or ``A``, for example ``'a.'`` or ``'(A)'``.",
        ),
        "abc.border": (
            True,
            _validate_bool,
            "Whether to draw a white border around a-b-c labels "
            "when :rcraw:`abc.loc` is inside the axes.",
        ),
        "abc.borderwidth": (
            1.5,
            _validate_pt,
            "Width of the white border around a-b-c labels.",
        ),
        "text.borderstyle": (
            "bevel",
            _validate_joinstyle,
            "Join style for text border strokes. Must be one of "
            "``'miter'``, ``'round'``, or ``'bevel'``.",
        ),
        "text.curved.upright": (
            True,
            _validate_bool,
            "Whether curved text is flipped to remain upright by default.",
        ),
        "text.curved.ellipsis": (
            False,
            _validate_bool,
            "Whether to show ellipses when curved text exceeds path length.",
        ),
        "text.curved.avoid_overlap": (
            True,
            _validate_bool,
            "Whether curved text hides overlapping glyphs by default.",
        ),
        "text.curved.overlap_tol": (
            0.1,
            _validate_float,
            "Overlap threshold used when hiding curved-text glyphs.",
        ),
        "text.curved.curvature_pad": (
            2.0,
            _validate_float,
            "Extra curved-text glyph spacing per radian of local curvature.",
        ),
        "text.curved.min_advance": (
            1.0,
            _validate_float,
            "Minimum extra curved-text glyph spacing in pixels.",
        ),
        "abc.bbox": (
            False,
            _validate_bool,
            "Whether to draw semi-transparent bounding boxes around a-b-c labels "
            "when :rcraw:`abc.loc` is inside the axes.",
        ),
        "abc.bboxcolor": (WHITE, _validate_color, "a-b-c label bounding box color."),
        "abc.bboxstyle": (
            "square",
            _validate_boxstyle,
            "a-b-c label bounding box style.",
        ),
        "abc.bboxalpha": (0.5, _validate_float, "a-b-c label bounding box opacity."),
        "abc.bboxpad": (
            None,
            _validate_or_none(_validate_pt),
            "Padding for the a-b-c label bounding box. By default this is scaled "
            "to make the box flush against the subplot edge." + _addendum_pt,
        ),
        "abc.color": (BLACK, _validate_color, "a-b-c label color."),
        "abc.loc": (
            "left",  # left side above the axes
            _validate_belongs(*TEXT_LOCS),
            "a-b-c label position. "
            "For options see the :ref:`location table <title_table>`.",
        ),
        "abc.size": (
            LARGESIZE,
            _validate_fontsize,
            "a-b-c label font size." + _addendum_font,
        ),
        "abc.titlepad": (
            LABELPAD,
            _validate_pt,
            "Padding separating the title and a-b-c label when in the same location."
            + _addendum_pt,
        ),
        "abc.weight": ("bold", _validate_fontweight, "a-b-c label font weight."),
        # Autoformatting
        "autoformat": (
            True,
            _validate_bool,
            "Whether to automatically apply labels from `pandas.Series`, "
            "`pandas.DataFrame`, and `xarray.DataArray` objects passed to "
            "plotting functions. See also :rcraw:`unitformat`.",
        ),
        # Axes additions
        "axes.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity of the background axes patch.",
        ),
        "axes.inbounds": (
            True,
            _validate_bool,
            "Whether to exclude out-of-bounds data when determining the default *y* (*x*) "
            "axis limits and the *x* (*y*) axis limits have been locked.",
        ),
        "axes.margin": (
            MARGIN,
            _validate_float,
            "The fractional *x* and *y* axis margins when limits are unset.",
        ),
        "bar.bar_labels": (
            False,
            _validate_bool,
            "Add value of the bars to the bar labels",
        ),
        # Country borders
        "borders": (False, _validate_bool, "Toggles country border lines on and off."),
        "borders.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity for country border lines.",
        ),
        "borders.color": (
            BLACK,
            _validate_color,
            "Line color for country border lines.",
        ),
        "borders.linewidth": (
            LINEWIDTH,
            _validate_pt,
            "Line width for country border lines.",
        ),
        "borders.zorder": (
            ZLINES,
            _validate_float,
            "Z-order for country border lines.",
        ),
        "borders.rasterized": (
            False,
            _validate_bool,
            "Toggles rasterization on or off for border feature in GeoAxes.",
        ),
        # Bottom subplot labels
        "bottomlabel.color": (
            BLACK,
            _validate_color,
            "Font color for column labels on the bottom of the figure.",
        ),
        "bottomlabel.pad": (
            TITLEPAD,
            _validate_pt,
            "Padding between axes content and column labels on the bottom of the figure."
            + _addendum_pt,
        ),
        "bottomlabel.rotation": (
            "horizontal",
            _validate_rotation,
            "Rotation for column labels at the bottom of the figure."
            + _addendum_rotation,
        ),
        "bottomlabel.size": (
            LARGESIZE,
            _validate_fontsize,
            "Font size for column labels on the bottom of the figure." + _addendum_font,
        ),
        "bottomlabel.weight": (
            "bold",
            _validate_fontweight,
            "Font weight for column labels on the bottom of the figure.",
        ),
        "cftime.time_unit": (
            "days since 2000-01-01",
            _validate_string,
            "Time unit for non-Gregorian calendars.",
        ),
        "cftime.resolution": (
            "DAILY",
            _validate_cftime_resolution,
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
            _validate_cftime_resolution_format,
            "Dict used for formatting non-Gregorian calendars.",
        ),
        "cftime.max_display_ticks": (
            7,
            _validate_int,
            "Number of ticks to display for cftime units.",
        ),
        # Coastlines
        "coast": (False, _validate_bool, "Toggles coastline lines on and off."),
        "coast.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity for coast lines",
        ),
        "coast.color": (BLACK, _validate_color, "Line color for coast lines."),
        "coast.linewidth": (LINEWIDTH, _validate_pt, "Line width for coast lines."),
        "coast.zorder": (ZLINES, _validate_float, "Z-order for coast lines."),
        "coast.rasterized": (
            False,
            _validate_bool,
            "Toggles the rasterization of the coastlines feature for GeoAxes.",
        ),
        # Colorbars
        "colorbar.center_levels": (
            False,
            _validate_bool,
            "Center the ticks in the center of each segment.",
        ),
        "colorbar.edgecolor": (
            BLACK,
            _validate_color,
            "Color for the inset colorbar frame edge.",
        ),
        "colorbar.extend": (
            1.3,
            _validate_em,
            'Length of rectangular or triangular "extensions" for panel colorbars.'
            + _addendum_em,
        ),
        "colorbar.outline": (
            True,
            _validate_bool,
            "Whether to draw a frame around the colorbar.",
        ),
        "colorbar.labelrotation": (
            "auto",
            _validate_float_or_auto,
            "Rotation of colorbar labels.",
        ),
        "colorbar.fancybox": (
            False,
            _validate_bool,
            'Whether to use a "fancy" round bounding box for inset colorbar frames.',
        ),
        "colorbar.framealpha": (
            FRAMEALPHA,
            _validate_float,
            "Opacity for inset colorbar frames.",
        ),
        "colorbar.facecolor": (
            WHITE,
            _validate_color,
            "Color for the inset colorbar frame.",
        ),
        "colorbar.frameon": (
            True,
            _validate_bool,
            "Whether to draw a frame behind inset colorbars.",
        ),
        "colorbar.grid": (
            False,
            _validate_bool,
            "Whether to draw borders between each level of the colorbar.",
        ),
        "colorbar.insetextend": (
            0.9,
            _validate_em,
            'Length of rectangular or triangular "extensions" for inset colorbars.'
            + _addendum_em,
        ),
        "colorbar.insetlength": (
            8,
            _validate_em,
            "Length of inset colorbars." + _addendum_em,
        ),
        "colorbar.insetpad": (
            0.7,
            _validate_em,
            "Padding between axes edge and inset colorbars." + _addendum_em,
        ),
        "colorbar.insetwidth": (
            1.2,
            _validate_em,
            "Width of inset colorbars." + _addendum_em,
        ),
        "colorbar.length": (1, _validate_em, "Length of outer colorbars."),
        "colorbar.loc": (
            "right",
            _validate_belongs(*COLORBAR_LOCS),
            "Inset colorbar location. "
            "For options see the :ref:`location table <colorbar_table>`.",
        ),
        "colorbar.width": (
            0.2,
            _validate_in,
            "Width of outer colorbars." + _addendum_in,
        ),
        "colorbar.rasterized": (
            False,
            _validate_bool,
            "Whether to use rasterization for colorbar solids.",
        ),
        "colorbar.shadow": (
            False,
            _validate_bool,
            "Whether to add a shadow underneath inset colorbar frames.",
        ),
        # Color cycle additions
        "cycle": (
            CYCLE,
            _validate_cmap("discrete", cycle=True),
            "Name of the color cycle assigned to :rcraw:`axes.prop_cycle`.",
        ),
        # Colormap additions
        "cmap": (
            CMAPSEQ,
            _validate_cmap("continuous"),
            "Alias for :rcraw:`cmap.sequential` and :rcraw:`image.cmap`.",
        ),
        "cmap.autodiverging": (
            True,
            _validate_bool,
            "Whether to automatically apply a diverging colormap and "
            "normalizer based on the data.",
        ),
        "cmap.qualitative": (
            CMAPCAT,
            _validate_cmap("discrete"),
            "Default colormap for qualitative datasets.",
        ),
        "cmap.cyclic": (
            CMAPCYC,
            _validate_cmap("continuous"),
            "Default colormap for cyclic datasets.",
        ),
        "cmap.discrete": (
            None,
            _validate_or_none(_validate_bool),
            "If ``True``, `~ultraplot.colors.DiscreteNorm` is used for every colormap plot. "
            "If ``False``, it is never used. If ``None``, it is used for all plot types "
            "except `imshow`, `matshow`, `spy`, `hexbin`, and `hist2d`.",
        ),
        "cmap.diverging": (
            CMAPDIV,
            _validate_cmap("continuous"),
            "Default colormap for diverging datasets.",
        ),
        "cmap.inbounds": (
            True,
            _validate_bool,
            "If ``True`` and the *x* and *y* axis limits are fixed, only in-bounds data "
            "is considered when determining the default colormap `vmin` and `vmax`.",
        ),
        "cmap.levels": (
            11,
            _validate_int,
            "Default number of `~ultraplot.colors.DiscreteNorm` levels for plotting "
            "commands that use colormaps.",
        ),
        "cmap.listedthresh": (
            64,
            _validate_int,
            "Native `~matplotlib.colors.ListedColormap`\\ s with more colors than "
            "this are converted to :class:`~ultraplot.colors.ContinuousColormap` rather than "
            ":class:`~ultraplot.colors.DiscreteColormap`. This helps translate continuous "
            "colormaps from external projects.",
        ),
        "cmap.lut": (
            256,
            _validate_int,
            "Number of colors in the colormap lookup table. "
            "Alias for :rcraw:`image.lut`.",
        ),
        "cmap.robust": (
            False,
            _validate_bool,
            "If ``True``, the default colormap `vmin` and `vmax` are chosen using the "
            "2nd to 98th percentiles rather than the minimum and maximum.",
        ),
        "cmap.sequential": (
            CMAPSEQ,
            _validate_cmap("continuous"),
            "Default colormap for sequential datasets. Alias for :rcraw:`image.cmap`.",
        ),
        # Special setting
        "edgefix": (
            True,
            _validate_bool,
            'Whether to fix issues with "white lines" appearing between patches '
            "in saved vector graphics and with vector graphic backends. Applies "
            "to colorbar levels and bar, area, pcolor, and contour plots.",
        ),
        # Font settings
        "font.name": (FONTNAME, _validate_fontname, "Alias for :rcraw:`font.family`."),
        "font.small": (
            SMALLSIZE,
            _validate_fontsize,
            "Alias for :rcraw:`font.smallsize`.",
        ),
        "font.smallsize": (
            SMALLSIZE,
            _validate_fontsize,
            "Meta setting that changes the label-like sizes ``axes.labelsize``, "
            "``legend.fontsize``, ``tick.labelsize``, and ``grid.labelsize``. Default is "
            "``'medium'`` (equivalent to :rcraw:`font.size`)." + _addendum_font,
        ),
        "font.large": (
            LARGESIZE,
            _validate_fontsize,
            "Alias for :rcraw:`font.largesize`.",
        ),
        "font.largesize": (
            LARGESIZE,
            _validate_fontsize,
            "Meta setting that changes the title-like sizes ``abc.size``, ``title.size``, "
            "``suptitle.size``, ``leftlabel.size``, ``rightlabel.size``, etc. Default is "
            "``'med-large'`` (i.e. 1.1 times :rcraw:`font.size`)." + _addendum_font,
        ),
        # Formatter settings
        "formatter.timerotation": (
            "vertical",
            _validate_rotation,
            "Rotation for *x* axis datetime tick labels." + _addendum_rotation,
        ),
        "formatter.zerotrim": (
            True,
            _validate_bool,
            "Whether to trim trailing decimal zeros on tick labels.",
        ),
        "formatter.log": (
            False,
            _validate_bool,
            "Whether to use log formatting (e.g., $10^{4}$) for "
            "logarithmically scaled axis tick labels.",
        ),
        "formatter.limits": (
            [-5, 6],  # must be list or else validated
            _validate["axes.formatter.limits"],
            "Alias for :rcraw:`axes.formatter.limits`.",
        ),
        "formatter.min_exponent": (
            0,
            _validate["axes.formatter.min_exponent"],
            "Alias for :rcraw:`axes.formatter.min_exponent`.",
        ),
        "formatter.offset_threshold": (
            4,
            _validate["axes.formatter.offset_threshold"],
            "Alias for :rcraw:`axes.formatter.offset_threshold`.",
        ),
        "formatter.use_locale": (
            False,
            _validate_bool,
            "Alias for :rcraw:`axes.formatter.use_locale`.",
        ),
        "formatter.use_mathtext": (
            MATHTEXT,
            _validate_bool,
            "Alias for :rcraw:`axes.formatter.use_mathtext`.",
        ),
        "formatter.use_offset": (
            True,
            _validate_bool,
            "Alias for :rcraw:`axes.formatter.useOffset`.",
        ),
        # Geographic axes settings
        "geo.backend": (
            "cartopy",
            _validate_belongs("cartopy", "basemap"),
            "The backend used for `~ultraplot.axes.GeoAxes`. Must be "
            "either 'cartopy' or 'basemap'.",
        ),
        "geo.extent": (
            "globe",
            _validate_belongs("globe", "auto"),
            "If ``'globe'``, the extent of cartopy `~ultraplot.axes.GeoAxes` is always "
            "global. If ``'auto'``, the extent is automatically adjusted based on "
            "plotted content. Default is ``'globe'``.",
        ),
        "geo.round": (
            True,
            _validate_bool,
            "If ``True`` (the default), polar `~ultraplot.axes.GeoAxes` like ``'npstere'`` "
            "and ``'spstere'`` are bounded with circles rather than squares.",
        ),
        # Graphs
        "graph.draw_nodes": (
            True,
            _validate_bool_or_iterable,
            "If ``True`` draws the nodes for all the nodes, otherwise only the nodes that are in the iterable.",
        ),
        "graph.draw_edges": (
            True,
            _validate_bool_or_iterable,
            "If ``True`` draws the edges for all the edges, otherwise only the edges that are in the iterable.",
        ),
        "graph.draw_labels": (
            False,
            _validate_bool_or_iterable,
            "If ``True`` draws the labels for all the nodes, otherwise only the nodes that are in the iterable.",
        ),
        "graph.draw_grid": (
            False,
            _validate_bool,
            "If ``True`` draws the grid for all the edges, otherwise only the edges that are in the iterable.",
        ),
        "graph.aspect": (
            "equal",
            _validate_belongs("equal", "auto"),
            "The aspect ratio of the graph.",
        ),
        "graph.facecolor": ("none", _validate_color, "The facecolor of the graph."),
        "graph.draw_spines": (
            False,
            _validate_bool_or_iterable,
            "If ``True`` draws the spines for all the edges, otherwise only the edges that are in the iterable.",
        ),
        "graph.rescale": (
            True,
            _validate_bool,
            "If ``True`` rescales the graph to fit the data.",
        ),
        # Gridlines
        # NOTE: Here 'grid' and 'gridminor' or *not* aliases for native 'axes.grid' and
        # invented 'axes.gridminor' because native 'axes.grid' controls both major *and*
        # minor gridlines. Must handle it independently from these settings.
        "grid": (True, _validate_bool, "Toggle major gridlines on and off."),
        "grid.below": (
            GRIDBELOW,  # like axes.axisbelow
            _validate_belongs(False, "line", True),
            "Alias for :rcraw:`axes.axisbelow`. If ``True``, draw gridlines below "
            "everything. If ``True``, draw them above everything. If ``'line'``, "
            "draw them above patches but below lines and markers.",
        ),
        "grid.checkoverlap": (
            True,
            _validate_bool,
            "Whether to have cartopy automatically check for and remove overlapping "
            "`~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.dmslabels": (
            True,
            _validate_bool,
            "Whether to use degrees-minutes-seconds rather than decimals for "
            "cartopy `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.geolabels": (
            True,
            _validate_bool,
            "Whether to include the ``'geo'`` spine in cartopy >= 0.20 when otherwise "
            "toggling left, right, bottom, or top `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.inlinelabels": (
            False,
            _validate_bool,
            "Whether to add inline labels for cartopy `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.labels": (
            False,
            _validate_bool,
            "Whether to add outer labels for `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.labelcolor": (
            BLACK,
            _validate_color,
            "Font color for `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.labelpad": (
            GRIDPAD,
            _validate_pt,
            "Padding between the map boundary and cartopy `~ultraplot.axes.GeoAxes` "
            "gridline labels." + _addendum_pt,
        ),
        "grid.labelsize": (
            SMALLSIZE,
            _validate_fontsize,
            "Font size for `~ultraplot.axes.GeoAxes` gridline labels." + _addendum_font,
        ),
        "grid.labelweight": (
            "normal",
            _validate_fontweight,
            "Font weight for `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.nsteps": (
            250,
            _validate_int,
            "Number of points used to draw cartopy `~ultraplot.axes.GeoAxes` gridlines.",
        ),
        "grid.pad": (GRIDPAD, _validate_pt, "Alias for :rcraw:`grid.labelpad`."),
        "grid.rotatelabels": (
            False,  # False limits projections where labels are available
            _validate_bool,
            "Whether to rotate cartopy `~ultraplot.axes.GeoAxes` gridline labels.",
        ),
        "grid.style": (
            "-",
            _validate_linestyle,
            "Major gridline style. Alias for :rcraw:`grid.linestyle`.",
        ),
        "grid.width": (
            LINEWIDTH,
            _validate_pt,
            "Major gridline width. Alias for :rcraw:`grid.linewidth`.",
        ),
        "grid.widthratio": (
            GRIDRATIO,
            _validate_float,
            "Ratio of minor gridline width to major gridline width.",
        ),
        # Minor gridlines
        "gridminor": (False, _validate_bool, "Toggle minor gridlines on and off."),
        "gridminor.alpha": (GRIDALPHA, _validate_float, "Minor gridline opacity."),
        "gridminor.color": (BLACK, _validate_color, "Minor gridline color."),
        "gridminor.linestyle": (
            GRIDSTYLE,
            _validate_linestyle,
            "Minor gridline style.",
        ),
        "gridminor.linewidth": (
            GRIDRATIO * LINEWIDTH,
            _validate_pt,
            "Minor gridline width.",
        ),
        "gridminor.style": (
            GRIDSTYLE,
            _validate_linestyle,
            "Minor gridline style. Alias for :rcraw:`gridminor.linestyle`.",
        ),
        "gridminor.width": (
            GRIDRATIO * LINEWIDTH,
            _validate_pt,
            "Minor gridline width. Alias for :rcraw:`gridminor.linewidth`.",
        ),
        # Backend stuff
        "inlineformat": (
            "retina",
            _validate_belongs("svg", "pdf", "retina", "png", "jpeg"),
            "The inline backend figure format. Valid formats include "
            "``'svg'``, ``'pdf'``, ``'retina'``, ``'png'``, and ``jpeg``.",
        ),
        # Inner borders
        "innerborders": (
            False,
            _validate_bool,
            "Toggles internal political border lines (e.g. states and provinces) "
            "on and off.",
        ),
        "innerborders.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity for internal political border lines",
        ),
        "innerborders.color": (
            BLACK,
            _validate_color,
            "Line color for internal political border lines.",
        ),
        "innerborders.linewidth": (
            LINEWIDTH,
            _validate_pt,
            "Line width for internal political border lines.",
        ),
        "innerborders.zorder": (
            ZLINES,
            _validate_float,
            "Z-order for internal political border lines.",
        ),
        # Axis label settings
        "label.color": (BLACK, _validate_color, "Alias for :rcraw:`axes.labelcolor`."),
        "label.pad": (
            LABELPAD,
            _validate_pt,
            "Alias for :rcraw:`axes.labelpad`." + _addendum_pt,
        ),
        "label.size": (
            SMALLSIZE,
            _validate_fontsize,
            "Alias for :rcraw:`axes.labelsize`." + _addendum_font,
        ),
        "label.weight": (
            "normal",
            _validate_fontweight,
            "Alias for :rcraw:`axes.labelweight`.",
        ),
        # Lake patches
        "lakes": (False, _validate_bool, "Toggles lake patches on and off."),
        "lakes.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity for lake patches",
        ),
        "lakes.color": (WHITE, _validate_color, "Face color for lake patches."),
        "lakes.zorder": (ZPATCHES, _validate_float, "Z-order for lake patches."),
        "lakes.rasterized": (
            False,
            _validate_bool,
            "Toggles rasterization on or off for lake feature",
        ),
        # Land patches
        "land": (False, _validate_bool, "Toggles land patches on and off."),
        "land.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity for land patches",
        ),
        "land.color": (BLACK, _validate_color, "Face color for land patches."),
        "land.zorder": (ZPATCHES, _validate_float, "Z-order for land patches."),
        "land.rasterized": (
            False,
            _validate_bool,
            "Toggles the rasterization of the land feature.",
        ),
        # Left subplot labels
        "leftlabel.color": (
            BLACK,
            _validate_color,
            "Font color for row labels on the left-hand side.",
        ),
        "leftlabel.pad": (
            TITLEPAD,
            _validate_pt,
            "Padding between axes content and row labels on the left-hand side."
            + _addendum_pt,
        ),
        "leftlabel.rotation": (
            "vertical",
            _validate_rotation,
            "Rotation for row labels on the left-hand side." + _addendum_rotation,
        ),
        "leftlabel.size": (
            LARGESIZE,
            _validate_fontsize,
            "Font size for row labels on the left-hand side." + _addendum_font,
        ),
        "lollipop.markersize": (
            36,
            _validate_float,
            "Size of lollipops in the lollipop plot.",
        ),
        "lollipop.stemcolor": (
            BLACK,
            _validate_color,
            "Color of lollipop lines.",
        ),
        "lollipop.stemwidth": (
            LINEWIDTH,
            _validate_pt,
            "Width of the stem",
        ),
        "lollipop.stemlinestyle": (
            "-",
            _validate_linestyle,
            "Line style of lollipop lines.",
        ),
        "leftlabel.weight": (
            "bold",
            _validate_fontweight,
            "Font weight for row labels on the left-hand side.",
        ),
        # Meta settings
        "margin": (
            MARGIN,
            _validate_float,
            "The fractional *x* and *y* axis data margins when limits are unset. "
            "Alias for :rcraw:`axes.margin`.",
        ),
        "meta.edgecolor": (
            BLACK,
            _validate_color,
            "Color of axis spines, tick marks, tick labels, and labels.",
        ),
        "meta.color": (
            BLACK,
            _validate_color,
            "Color of axis spines, tick marks, tick labels, and labels. "
            "Alias for :rcraw:`meta.edgecolor`.",
        ),
        "meta.linewidth": (
            LINEWIDTH,
            _validate_pt,
            "Thickness of axis spines and major tick lines.",
        ),
        "meta.width": (
            LINEWIDTH,
            _validate_pt,
            "Thickness of axis spines and major tick lines. "
            "Alias for :rcraw:`meta.linewidth`.",
        ),
        # For negative positive patches
        "negcolor": (
            "blue7",
            _validate_color,
            "Color for negative bars and shaded areas when using ``negpos=True``. "
            "See also :rcraw:`poscolor`.",
        ),
        "poscolor": (
            "red7",
            _validate_color,
            "Color for positive bars and shaded areas when using ``negpos=True``. "
            "See also :rcraw:`negcolor`.",
        ),
        # Ocean patches
        "ocean": (False, _validate_bool, "Toggles ocean patches on and off."),
        "ocean.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity for ocean patches",
        ),
        "ocean.color": (WHITE, _validate_color, "Face color for ocean patches."),
        "ocean.zorder": (ZPATCHES, _validate_float, "Z-order for ocean patches."),
        "ocean.rasterized": (
            False,
            _validate_bool,
            "Turns rasterization on or off for the oceans feature for GeoAxes.",
        ),
        # Geographic resolution
        "reso": (
            "lo",
            _validate_belongs("lo", "med", "hi", "x-hi", "xx-hi"),
            "Resolution for `~ultraplot.axes.GeoAxes` geographic features. "
            "Must be one of ``'lo'``, ``'med'``, ``'hi'``, ``'x-hi'``, or ``'xx-hi'``.",
        ),
        # Right subplot labels
        "rightlabel.color": (
            BLACK,
            _validate_color,
            "Font color for row labels on the right-hand side.",
        ),
        "rightlabel.pad": (
            TITLEPAD,
            _validate_pt,
            "Padding between axes content and row labels on the right-hand side."
            + _addendum_pt,
        ),
        "rightlabel.rotation": (
            "vertical",
            _validate_rotation,
            "Rotation for row labels on the right-hand side." + _addendum_rotation,
        ),
        "rightlabel.size": (
            LARGESIZE,
            _validate_fontsize,
            "Font size for row labels on the right-hand side." + _addendum_font,
        ),
        "rightlabel.weight": (
            "bold",
            _validate_fontweight,
            "Font weight for row labels on the right-hand side.",
        ),
        # River lines
        "rivers": (False, _validate_bool, "Toggles river lines on and off."),
        "rivers.alpha": (
            None,
            _validate_or_none(_validate_float),
            "Opacity for river lines.",
        ),
        "rivers.color": (BLACK, _validate_color, "Line color for river lines."),
        "rivers.linewidth": (LINEWIDTH, _validate_pt, "Line width for river lines."),
        "rivers.zorder": (ZLINES, _validate_float, "Z-order for river lines."),
        "rivers.rasterized": (
            False,
            _validate_bool,
            "Toggles rasterization on or off for rivers feature for GeoAxes.",
        ),
        # Circlize settings
        "chord.start": (
            0.0,
            _validate_float,
            "Start angle for chord diagrams.",
        ),
        "chord.end": (
            360.0,
            _validate_float,
            "End angle for chord diagrams.",
        ),
        "chord.space": (
            0.0,
            _validate_float_or_iterable,
            "Inter-sector spacing for chord diagrams.",
        ),
        "chord.endspace": (
            True,
            _validate_bool,
            "Whether to add an ending space gap for chord diagrams.",
        ),
        "chord.r_lim": (
            (97.0, 100.0),
            _validate_tuple_float_2,
            "Radial limits for chord diagrams.",
        ),
        "chord.ticks_interval": (
            None,
            _validate_or_none(_validate_int),
            "Tick interval for chord diagrams.",
        ),
        "chord.order": (
            None,
            _validate_or_none(_validate_string_or_iterable),
            "Ordering of sectors for chord diagrams.",
        ),
        "radar.r_lim": (
            (0.0, 100.0),
            _validate_tuple_float_2,
            "Radial limits for radar charts.",
        ),
        "radar.vmin": (
            0.0,
            _validate_float,
            "Minimum value for radar charts.",
        ),
        "radar.vmax": (
            100.0,
            _validate_float,
            "Maximum value for radar charts.",
        ),
        "radar.fill": (
            True,
            _validate_bool,
            "Whether to fill radar chart polygons.",
        ),
        "radar.marker_size": (
            0,
            _validate_int,
            "Marker size for radar charts.",
        ),
        "radar.bg_color": (
            "#eeeeee80",
            _validate_or_none(_validate_color),
            "Background color for radar charts.",
        ),
        "radar.circular": (
            False,
            _validate_bool,
            "Whether to use circular radar charts.",
        ),
        "radar.show_grid_label": (
            True,
            _validate_bool,
            "Whether to show grid labels on radar charts.",
        ),
        "radar.grid_interval_ratio": (
            0.2,
            _validate_or_none(_validate_float),
            "Grid interval ratio for radar charts.",
        ),
        "phylogeny.start": (
            0.0,
            _validate_float,
            "Start angle for phylogeny plots.",
        ),
        "phylogeny.end": (
            360.0,
            _validate_float,
            "End angle for phylogeny plots.",
        ),
        "phylogeny.r_lim": (
            (50.0, 100.0),
            _validate_tuple_float_2,
            "Radial limits for phylogeny plots.",
        ),
        "phylogeny.format": (
            "newick",
            _validate_string,
            "Input format for phylogeny plots.",
        ),
        "phylogeny.outer": (
            True,
            _validate_bool,
            "Whether to place phylogeny leaves on the outer edge.",
        ),
        "phylogeny.align_leaf_label": (
            True,
            _validate_bool,
            "Whether to align phylogeny leaf labels.",
        ),
        "phylogeny.ignore_branch_length": (
            False,
            _validate_bool,
            "Whether to ignore branch lengths in phylogeny plots.",
        ),
        "phylogeny.leaf_label_size": (
            None,
            _validate_or_none(_validate_float),
            "Leaf label font size for phylogeny plots.",
        ),
        "phylogeny.leaf_label_rmargin": (
            2.0,
            _validate_float,
            "Radial margin for phylogeny leaf labels.",
        ),
        "phylogeny.reverse": (
            False,
            _validate_bool,
            "Whether to reverse phylogeny orientation.",
        ),
        "phylogeny.ladderize": (
            False,
            _validate_bool,
            "Whether to ladderize phylogeny branches.",
        ),
        # Sankey diagrams
        "sankey.align": (
            "center",
            _validate_belongs("center", "left", "right", "justify"),
            "Horizontal alignment of nodes.",
        ),
        "sankey.connect": (
            (0, 0),
            _validate_tuple_int_2,
            "Connection path for Sankey diagram.",
        ),
        "sankey.flow_labels": (
            False,
            _validate_bool,
            "Whether to draw flow labels.",
        ),
        "sankey.flow_label_pos": (
            0.5,
            _validate_float,
            "Position of flow labels along the flow.",
        ),
        "sankey.flow_sort": (
            True,
            _validate_bool,
            "Whether to sort flows.",
        ),
        "sankey.node_labels": (
            True,
            _validate_bool,
            "Whether to draw node labels.",
        ),
        "sankey.node_label_offset": (
            0.01,
            _validate_float,
            "Offset for node labels.",
        ),
        "sankey.node_label_outside": (
            "auto",
            _validate_bool_or_string,
            "Position of node labels relative to the node.",
        ),
        "sankey.other_label": (
            "Other",
            _validate_string,
            "Label for 'other' category in Sankey diagram.",
        ),
        "sankey.pathlabel": (
            "",
            _validate_string,
            "Label for the patch.",
        ),
        "sankey.pathlengths": (
            0.25,
            _validate_float,
            "Path lengths for Sankey diagram.",
        ),
        "sankey.rotation": (
            0.0,
            _validate_float,
            "Rotation of the Sankey diagram.",
        ),
        "sankey.trunklength": (
            1.0,
            _validate_float,
            "Trunk length for Sankey diagram.",
        ),
        # Subplots settings
        "subplots.align": (
            False,
            _validate_bool,
            "Whether to align axis labels during draw. See `aligning labels "
            "<https://matplotlib.org/stable/gallery/subplots_axes_and_figures/align_labels_demo.html>`__.",  # noqa: E501
        ),
        "subplots.equalspace": (
            False,
            _validate_bool,
            "Whether to make the tight layout algorithm assign the same space for "
            "every row and the same space for every column.",
        ),
        "subplots.groupspace": (
            True,
            _validate_bool,
            "Whether to make the tight layout algorithm consider space between only "
            'adjacent subplot "groups" rather than every subplot in the row or column.',
        ),
        "subplots.innerpad": (
            1,
            _validate_em,
            "Padding between adjacent subplots." + _addendum_em,
        ),
        "subplots.outerpad": (
            0.5,
            _validate_em,
            "Padding around figure edge." + _addendum_em,
        ),
        "subplots.panelpad": (
            0.5,
            _validate_em,
            "Padding between subplots and panels, and between stacked panels."
            + _addendum_em,
        ),
        "subplots.panelwidth": (
            0.5,
            _validate_in,
            "Width of side panels." + _addendum_in,
        ),
        "subplots.refwidth": (
            2.5,
            _validate_in,
            "Default width of the reference subplot." + _addendum_in,
        ),
        "subplots.share": (
            "auto",
            _validate_belongs(
                0, 1, 2, 3, 4, False, "labels", "limits", True, "all", "auto"
            ),
            "The axis sharing level, one of ``0``, ``1``, ``2``, or ``3``, or the "
            "more intuitive aliases ``False``, ``'labels'``, ``'limits'``, ``True``, "
            "or ``'auto'``. See `~ultraplot.figure.Figure` for details.",
        ),
        "subplots.span": (
            True,
            _validate_bool,
            "Toggles spanning axis labels. See `~ultraplot.ui.subplots` for details.",
        ),
        "subplots.tight": (
            True,
            _validate_bool,
            "Whether to auto-adjust the subplot spaces and figure margins.",
        ),
        "subplots.pixelsnap": (
            False,
            _validate_bool,
            "Whether to snap subplot bounds to the renderer pixel grid during draw.",
        ),
        # Super title settings
        "suptitle.color": (BLACK, _validate_color, "Figure title color."),
        "suptitle.pad": (
            TITLEPAD,
            _validate_pt,
            "Padding between axes content and the figure super title." + _addendum_pt,
        ),
        "suptitle.size": (
            LARGESIZE,
            _validate_fontsize,
            "Figure title font size." + _addendum_font,
        ),
        "suptitle.weight": ("bold", _validate_fontweight, "Figure title font weight."),
        # Tick settings
        "tick.color": (BLACK, _validate_color, "Major and minor tick color."),
        "tick.dir": (
            TICKDIR,
            _validate_belongs("in", "out", "inout"),
            "Major and minor tick direction. Must be one of "
            "``'out'``, ``'in'``, or ``'inout'``.",
        ),
        "tick.labelcolor": (BLACK, _validate_color, "Axis tick label color."),
        "tick.labelpad": (
            TICKPAD,
            _validate_pt,
            "Padding between ticks and tick labels." + _addendum_pt,
        ),
        "tick.labelsize": (
            SMALLSIZE,
            _validate_fontsize,
            "Axis tick label font size." + _addendum_font,
        ),
        "tick.labelweight": (
            "normal",
            _validate_fontweight,
            "Axis tick label font weight.",
        ),
        "tick.len": (TICKLEN, _validate_pt, "Length of major ticks in points."),
        "tick.lenratio": (
            TICKLENRATIO,
            _validate_float,
            "Ratio of minor tickline length to major tickline length.",
        ),
        "tick.linewidth": (LINEWIDTH, _validate_pt, "Major tickline width."),
        "tick.minor": (
            TICKMINOR,
            _validate_bool,
            "Toggles minor ticks on and off.",
        ),
        "tick.pad": (TICKPAD, _validate_pt, "Alias for :rcraw:`tick.labelpad`."),
        "tick.width": (
            LINEWIDTH,
            _validate_pt,
            "Major tickline width. Alias for :rcraw:`tick.linewidth`.",
        ),
        "tick.widthratio": (
            TICKWIDTHRATIO,
            _validate_float,
            "Ratio of minor tickline width to major tickline width.",
        ),
        # Title settings
        "title.above": (
            True,
            _validate_belongs(False, True, "panels"),
            "Whether to move outer titles and a-b-c labels above panels, colorbars, or "
            "legends that are above the axes. If the string 'panels' then text is only "
            "redirected above axes panels. Otherwise should be boolean.",
        ),
        "title.border": (
            True,
            _validate_bool,
            "Whether to draw a white border around titles "
            "when :rcraw:`title.loc` is inside the axes.",
        ),
        "title.borderwidth": (1.5, _validate_pt, "Width of the border around titles."),
        "title.bbox": (
            False,
            _validate_bool,
            "Whether to draw semi-transparent bounding boxes around titles "
            "when :rcraw:`title.loc` is inside the axes.",
        ),
        "title.bboxcolor": (WHITE, _validate_color, "Axes title bounding box color."),
        "title.bboxstyle": (
            "square",
            _validate_boxstyle,
            "Axes title bounding box style.",
        ),
        "title.bboxalpha": (0.5, _validate_float, "Axes title bounding box opacity."),
        "title.bboxpad": (
            None,
            _validate_or_none(_validate_pt),
            "Padding for the title bounding box. By default this is scaled "
            "to make the box flush against the axes edge." + _addendum_pt,
        ),
        "title.color": (
            BLACK,
            _validate_color,
            "Axes title color. Alias for :rcraw:`axes.titlecolor`.",
        ),
        "title.loc": (
            "center",
            _validate_belongs(*TEXT_LOCS),
            "Title position. For options see the :ref:`location table <title_table>`.",
        ),
        "title.pad": (
            TITLEPAD,
            _validate_pt,
            "Padding between the axes edge and the inner and outer titles and "
            "a-b-c labels. Alias for :rcraw:`axes.titlepad`." + _addendum_pt,
        ),
        "title.size": (
            LARGESIZE,
            _validate_fontsize,
            "Axes title font size. Alias for :rcraw:`axes.titlesize`." + _addendum_font,
        ),
        "title.weight": (
            "normal",
            _validate_fontweight,
            "Axes title font weight. Alias for :rcraw:`axes.titleweight`.",
        ),
        # Top subplot label settings
        "toplabel.color": (
            BLACK,
            _validate_color,
            "Font color for column labels on the top of the figure.",
        ),
        "toplabel.pad": (
            TITLEPAD,
            _validate_pt,
            "Padding between axes content and column labels on the top of the figure."
            + _addendum_pt,
        ),
        "toplabel.rotation": (
            "horizontal",
            _validate_rotation,
            "Rotation for column labels at the top of the figure." + _addendum_rotation,
        ),
        "toplabel.size": (
            LARGESIZE,
            _validate_fontsize,
            "Font size for column labels on the top of the figure." + _addendum_font,
        ),
        "toplabel.weight": (
            "bold",
            _validate_fontweight,
            "Font weight for column labels on the top of the figure.",
        ),
        # Unit formatting
        "unitformat": (
            "L",
            _validate_string,
            "The format string used to format `pint.Quantity` default unit labels "
            "using ``format(units, unitformat)``. See also :rcraw:`autoformat`.",
        ),
        "ultraplot.check_for_latest_version": (
            False,
            _validate_bool,
            "Whether to check for the latest version of UltraPlot on PyPI when importing",
        ),
        "ultraplot.eager_import": (
            False,
            _validate_bool,
            "Whether to import the full public API during setup instead of lazily.",
        ),
    }
