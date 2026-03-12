#!/usr/bin/env python3
"""
The figure class used for all ultraplot figures.
"""

import functools
import inspect
import os

try:
    from typing import Optional, Tuple, Union
except ImportError:
    from typing_extensions import Optional, Tuple, Union

import matplotlib.figure as mfigure
import numpy as np

try:
    from typing import override
except ImportError:
    from typing_extensions import override

from . import axes as paxes
from . import gridspec as pgridspec
from .config import rc
from .internals import (
    _not_none,
    _pop_params,
    _pop_rc,
    _translate_loc,
    context,
    docstring,
    ic,  # noqa: F401
    warnings,
)
from .internals.figure_formatting import FigureFormatting
from .internals.figure_labels import FigureLabels
from .internals.figure_factory import FigureFactory
from .internals.figure_guides import FigureGuides
from .internals.figure_layout import FigureLayout
from .internals.figure_options import (
    build_gridspec_params,
    resolve_share_options,
    resolve_size_options,
    resolve_span_align_options,
    resolve_tight_active,
)
from .internals.figure_panels import FigurePanels
from .internals.figure_sharing import FigureSharing

__all__ = [
    "Figure",
]


# Preset figure widths or sizes based on academic journal recommendations
# NOTE: Please feel free to add to this!
JOURNAL_SIZES = {
    "aaas1": "5.5cm",
    "aaas2": "12cm",
    "agu1": ("95mm", "115mm"),
    "agu2": ("190mm", "115mm"),
    "agu3": ("95mm", "230mm"),
    "agu4": ("190mm", "230mm"),
    "ams1": 3.2,
    "ams2": 4.5,
    "ams3": 5.5,
    "ams4": 6.5,
    "cop1": "8.3cm",
    "cop2": "12cm",
    "nat1": "89mm",
    "nat2": "183mm",
    "pnas1": "8.7cm",
    "pnas2": "11.4cm",
    "pnas3": "17.8cm",
}


# Figure docstring
_figure_docstring = """
refnum : int, optional
    The reference subplot number. The `refwidth`, `refheight`, and `refaspect`
    keyword args are applied to this subplot, and the aspect ratio is conserved
    for this subplot in the `~Figure.auto_layout`. The default is the first
    subplot created in the figure.
refaspect : float or 2-tuple of float, optional
    The reference subplot aspect ratio. If scalar, this indicates the width
    divided by height. If 2-tuple, this indicates the (width, height). Ignored
    if both `figwidth` *and* `figheight` or both `refwidth` *and* `refheight` were
    passed. The default value is ``1`` or the "data aspect ratio" if the latter
    is explicitly fixed (as with `~ultraplot.axes.PlotAxes.imshow` plots and
    `~ultraplot.axes.Axes.GeoAxes` projections; see :func:`~matplotlib.axes.Axes.set_aspect`).
refwidth, refheight : unit-spec, default: :rc:`subplots.refwidth`
    The width, height of the reference subplot.
    %(units.in)s
    Ignored if `figwidth`, `figheight`, or `figsize` was passed. If you
    specify just one, `refaspect` will be respected.
ref, aspect, axwidth, axheight
    Aliases for `refnum`, `refaspect`, `refwidth`, `refheight`.
    *These may be deprecated in a future release.*
figwidth, figheight : unit-spec, optional
    The figure width and height. Default behavior is to use `refwidth`.
    %(units.in)s
    If you specify just one, `refaspect` will be respected.
width, height
    Aliases for `figwidth`, `figheight`.
figsize : 2-tuple, optional
    Tuple specifying the figure ``(width, height)``.
sharex, sharey, share \
: {0, False, 1, 'labels', 'labs', 2, 'limits', 'lims', 3, True, 4, 'all', 'auto'}, \
default: :rc:`subplots.share`
    The axis sharing "level" for the *x* axis, *y* axis, or both
    axes. Options are as follows:

    * ``0`` or ``False``: No axis sharing. This also sets the default `spanx`
      and `spany` values to ``False``.
    * ``1`` or ``'labels'`` or ``'labs'``: Only draw axis labels on the bottommost
      row or leftmost column of subplots. Tick labels still appear on every subplot.
    * ``2`` or ``'limits'`` or ``'lims'``: As above but force the axis limits, scales,
      and tick locations to be identical. Tick labels still appear on every subplot.
    * ``3`` or ``True``: As above but only show the tick labels on the bottommost
      row and leftmost column of subplots.
    * ``4`` or ``'all'``: As above but also share the axis limits, scales, and
      tick locations between subplots not in the same row or column.
    * ``'auto'``: Start from level ``3`` and only share axes that are compatible
      (for example, mixed cartesian and polar axes are kept unshared).

    Explicit sharing levels (``0`` to ``4`` and aliases) still force sharing
    attempts and can emit warnings for incompatible axes.

spanx, spany, span : bool or {0, 1}, default: :rc:`subplots.span`
    Whether to use "spanning" axis labels for the *x* axis, *y* axis, or both
    axes. Default is ``False`` if `sharex`, `sharey`, or `share` are ``0`` or
    ``False``. When ``True``, a single, centered axis label is used for all axes
    with bottom and left edges in the same row or column. This can considerably
    redundancy in your figure. "Spanning" labels integrate with "shared" axes. For
    example, for a 3-row, 3-column figure, with ``sharey > 1`` and ``spany == True``,
    your figure will have 1 y axis label instead of 9 y axis labels.
alignx, aligny, align : bool or {0, 1}, default: :rc:`subplots.align`
    Whether to `"align" axis labels \
<https://matplotlib.org/stable/gallery/subplots_axes_and_figures/align_labels_demo.html>`__
    for the *x* axis, *y* axis, or both axes. Aligned labels always appear in the same
    row or column. This is ignored if `spanx`, `spany`, or `span` are ``True``.
%(gridspec.shared)s
%(gridspec.scalar)s
tight : bool, default: :rc`subplots.tight`
    Whether automatic calls to `~Figure.auto_layout` should include
    :ref:`tight layout adjustments <ug_tight>`. If you manually specified a spacing
    in the call to `~ultraplot.ui.subplots`, it will be used to override the tight
    layout spacing. For example, with ``left=1``, the left margin is set to 1
    em-width, while the remaining margin widths are calculated automatically.
%(gridspec.tight)s
journal : str, optional
    String corresponding to an academic journal standard used to control the figure
    width `figwidth` and, if specified, the figure height `figheight`. See the below
    table. Feel free to add to this table by submitting a pull request.

    .. _journal_table:

    ===========  ====================  \
===============================================================================
    Key          Size description      Organization
    ===========  ====================  \
===============================================================================
    ``'aaas1'``  1-column              \
`American Association for the Advancement of Science <aaas_>`_ (e.g. *Science*)
    ``'aaas2'``  2-column              ”
    ``'agu1'``   1-column              `American Geophysical Union <agu_>`_
    ``'agu2'``   2-column              ”
    ``'agu3'``   full height 1-column  ”
    ``'agu4'``   full height 2-column  ”
    ``'ams1'``   1-column              `American Meteorological Society <ams_>`_
    ``'ams2'``   small 2-column        ”
    ``'ams3'``   medium 2-column       ”
    ``'ams4'``   full 2-column         ”
    ``'cop1'``   1-column              \
`Copernicus Publications <cop_>`_ (e.g. *The Cryosphere*, *Geoscientific Model Development*)
    ``'cop2'``   2-column              ”
    ``'nat1'``   1-column              `Nature Research <nat_>`_
    ``'nat2'``   2-column              ”
    ``'pnas1'``  1-column              \
`Proceedings of the National Academy of Sciences <pnas_>`_
    ``'pnas2'``  2-column              ”
    ``'pnas3'``  landscape page        ”
    ===========  ====================  \
===============================================================================

    .. _aaas: \
https://www.sciencemag.org/authors/instructions-preparing-initial-manuscript
    .. _agu: \
https://www.agu.org/Publish-with-AGU/Publish/Author-Resources/Graphic-Requirements
    .. _ams: \
https://www.ametsoc.org/ams/index.cfm/publications/authors/journal-and-bams-authors/figure-information-for-authors/
    .. _cop: \
https://publications.copernicus.org/for_authors/manuscript_preparation.html#figurestables
    .. _nat: \
https://www.nature.com/nature/for-authors/formatting-guide
    .. _pnas: \
https://www.pnas.org/page/authors/format
"""
docstring._snippet_manager["figure.figure"] = _figure_docstring


# Multiple subplots
_subplots_params_docstring = """
array : `ultraplot.gridspec.GridSpec` or array-like of int, optional
    The subplot grid specifier. If a :class:`~ultraplot.gridspec.GridSpec`, one subplot is
    drawn for each unique :class:`~ultraplot.gridspec.GridSpec` slot. If a 2D array of integers,
    one subplot is drawn for each unique integer in the array. Think of this array as
    a "picture" of the subplot grid -- for example, the array ``[[1, 1], [2, 3]]``
    creates one long subplot in the top row, two smaller subplots in the bottom row.
    Integers must range from 1 to the number of plots, and ``0`` indicates an
    empty space -- for example, ``[[1, 1, 1], [2, 0, 3]]`` creates one long subplot
    in the top row with two subplots in the bottom row separated by a space.
nrows, ncols : int, default: 1
    The number of rows and columns in the subplot grid. Ignored
    if `array` was passed. Use these arguments for simple subplot grids.
order : {'C', 'F'}, default: 'C'
    Whether subplots are numbered in column-major (``'C'``) or row-major (``'F'``)
    order. Analogous to `numpy.array` ordering. This controls the order that
    subplots appear in the `SubplotGrid` returned by this function, and the order
    of subplot a-b-c labels (see `~ultraplot.axes.Axes.format`).
%(axes.proj)s

    To use different projections for different subplots, you have
    two options:

    * Pass a *list* of projection specifications, one for each subplot.
      For example, ``uplt.subplots(ncols=2, proj=('cart', 'robin'))``.
    * Pass a *dictionary* of projection specifications, where the
      keys are integers or tuples of integers that indicate the projection
      to use for the corresponding subplot number(s). If a key is not
      provided, the default projection ``'cartesian'`` is used. For example,
      ``uplt.subplots(ncols=4, proj={2: 'cyl', (3, 4): 'stere'})`` creates
      a figure with a default Cartesian axes for the first subplot, a Mercator
      projection for the second subplot, and a Stereographic projection
      for the third and fourth subplots.

%(axes.proj_kw)s
    If dictionary of properties, applies globally. If list or dictionary of
    dictionaries, applies to specific subplots, as with `proj`. For example,
    ``uplt.subplots(ncols=2, proj='cyl', proj_kw=({'lon_0': 0}, {'lon_0': 180})``
    centers the projection in the left subplot on the prime meridian and in the
    right subplot on the international dateline.
%(axes.backend)s
    If string, applies to all subplots. If list or dict, applies to specific
    subplots, as with `proj`.
%(gridspec.shared)s
%(gridspec.vector)s
%(gridspec.tight)s
"""
docstring._snippet_manager["figure.subplots_params"] = _subplots_params_docstring


# Extra args docstring
_axes_params_docstring = """
**kwargs
    Passed to the ultraplot class `ultraplot.axes.CartesianAxes`, `ultraplot.axes.PolarAxes`,
    `ultraplot.axes.GeoAxes`, or `ultraplot.axes.ThreeAxes`. This can include keyword
    arguments for projection-specific ``format`` commands.
"""
docstring._snippet_manager["figure.axes_params"] = _axes_params_docstring


# Multiple subplots docstring
_subplots_docstring = """
Add an arbitrary grid of subplots to the figure.

Parameters
----------
%(figure.subplots_params)s

Other parameters
----------------
%(figure.figure)s
%(figure.axes_params)s

Returns
-------
axs : SubplotGrid
    The axes instances stored in a `SubplotGrid`.

See also
--------
ultraplot.ui.figure
ultraplot.ui.subplots
ultraplot.figure.Figure.subplot
ultraplot.figure.Figure.add_subplot
ultraplot.gridspec.SubplotGrid
ultraplot.axes.Axes
"""
docstring._snippet_manager["figure.subplots"] = _subplots_docstring


# Single subplot docstring
_subplot_docstring = """
Add a subplot axes to the figure.

Parameters
----------
*args : int, tuple, or `~matplotlib.gridspec.SubplotSpec`, optional
    The subplot location specifier. Your options are:

    * A single 3-digit integer argument specifying the number of rows,
      number of columns, and gridspec number (using row-major indexing).
    * Three positional arguments specifying the number of rows, number of
      columns, and gridspec number (int) or number range (2-tuple of int).
    * A `~matplotlib.gridspec.SubplotSpec` instance generated by indexing
      a ultraplot :class:`~ultraplot.gridspec.GridSpec`.

    For integer input, the implied geometry must be compatible with the implied
    geometry from previous calls -- for example, ``fig.add_subplot(331)`` followed
    by ``fig.add_subplot(132)`` is valid because the 1 row of the second input can
    be tiled into the 3 rows of the the first input, but ``fig.add_subplot(232)``
    will raise an error because 2 rows cannot be tiled into 3 rows. For
    `~matplotlib.gridspec.SubplotSpec` input, the `~matplotlig.gridspec.SubplotSpec`
    must be derived from the :class:`~ultraplot.gridspec.GridSpec` used in previous calls.

    These restrictions arise because we allocate a single,
    unique `~Figure.gridspec` for each figure.
number : int, optional
    The axes number used for a-b-c labeling. See `~ultraplot.axes.Axes.format` for
    details. By default this is incremented automatically based on the other subplots
    in the figure. Use e.g. ``number=None`` or ``number=False`` to ensure the subplot
    has no a-b-c label. Note the number corresponding to `a` is ``1``, not ``0``.
autoshare : bool, default: True
    Whether to automatically share the *x* and *y* axes with subplots spanning the
    same rows and columns based on the figure-wide `sharex` and `sharey` settings.
    This has no effect if :rcraw:`subplots.share` is ``False`` or if ``sharex=False``
    or ``sharey=False`` were passed to the figure.
%(axes.proj)s
%(axes.proj_kw)s
%(axes.backend)s

Other parameters
----------------
%(figure.axes_params)s

See also
--------
ultraplot.figure.Figure.add_axes
ultraplot.figure.Figure.subplots
ultraplot.figure.Figure.add_subplots
"""
docstring._snippet_manager["figure.subplot"] = _subplot_docstring


# Single axes
_axes_docstring = """
Add a non-subplot axes to the figure.

Parameters
----------
rect : 4-tuple of float
    The (left, bottom, width, height) dimensions of the axes in
    figure-relative coordinates.
%(axes.proj)s
%(axes.proj_kw)s
%(axes.backend)s

Other parameters
----------------
%(figure.axes_params)s

See also
--------
ultraplot.figure.Figure.subplot
ultraplot.figure.Figure.add_subplot
ultraplot.figure.Figure.subplots
ultraplot.figure.Figure.add_subplots
"""
docstring._snippet_manager["figure.axes"] = _axes_docstring


# Colorbar or legend panel docstring
_space_docstring = """
loc : str, optional
    The {name} location. Valid location keys are as follows.

%(axes.panel_loc)s

space : float or str, default: None
    The fixed space between the {name} and the subplot grid edge.
    %(units.em)s
    When the :ref:`tight layout algorithm <ug_tight>` is active for the figure,
    `space` is computed automatically (see `pad`). Otherwise, `space` is set to
    a suitable default.
pad : float or str, default: :rc:`subplots.innerpad` or :rc:`subplots.panelpad`
    The :ref:`tight layout padding <ug_tight>` between the {name} and the
    subplot grid. Default is :rcraw:`subplots.innerpad` for the first {name}
    and :rcraw:`subplots.panelpad` for subsequently "stacked" {name}s.
    %(units.em)s
row, rows
    Aliases for `span` for {name}s on the left or right side.
col, cols
    Aliases for `span` for {name}s on the top or bottom side.
span : int or 2-tuple of int, default: None
    Integer(s) indicating the span of the {name} across rows and columns of
    subplots. For example, ``fig.{name}(loc='b', col=1)`` draws a {name} beneath
    the leftmost column of subplots, and ``fig.{name}(loc='b', cols=(1, 2))``
    draws a {name} beneath the left two columns of subplots. By default
    the {name} will span every subplot row and column.
align : {{'center', 'top', 't', 'bottom', 'b', 'left', 'l', 'right', 'r'}}, optional
    For outer {name}s only. How to align the {name} against the
    subplot edge. The values ``'top'`` and ``'bottom'`` are valid for left and
    right {name}s and ``'left'`` and ``'right'`` are valid for top and bottom
    {name}s. The default is always ``'center'``.
"""
docstring._snippet_manager["figure.legend_space"] = _space_docstring.format(
    name="legend"
)  # noqa: E501
docstring._snippet_manager["figure.colorbar_space"] = _space_docstring.format(
    name="colorbar"
)  # noqa: E501


# Save docstring
_save_docstring = """
Save the figure.

Parameters
----------
path : path-like, optional
    The file path. User paths are expanded with `os.path.expanduser`.
**kwargs
    Passed to `~matplotlib.figure.Figure.savefig`

See also
--------
Figure.save
Figure.savefig
matplotlib.figure.Figure.savefig
"""
docstring._snippet_manager["figure.save"] = _save_docstring


def _get_journal_size(preset):
    """
    Return the width and height corresponding to the given preset.
    """
    value = JOURNAL_SIZES.get(preset, None)
    if value is None:
        raise ValueError(
            f"Unknown preset figure size specifier {preset!r}. "
            "Current options are: " + ", ".join(map(repr, JOURNAL_SIZES.keys()))
        )
    figwidth = figheight = None
    try:
        figwidth, figheight = value
    except (TypeError, ValueError):
        figwidth = value
    return figwidth, figheight


def _add_canvas_preprocessor(canvas, method, cache=False):
    """
    Return a pre-processer that can be used to override instance-level
    canvas draw() and print_figure() methods. This applies tight layout
    and aspect ratio-conserving adjustments and aligns labels. Required
    so canvas methods instantiate renderers with the correct dimensions.
    """

    # NOTE: Renderer must be (1) initialized with the correct figure size or
    # (2) changed inplace during draw, but vector graphic renderers *cannot*
    # be changed inplace. So options include (1) monkey patch
    # canvas.get_width_height, overriding figure.get_size_inches, and exploit
    # the FigureCanvasAgg.get_renderer() implementation (because FigureCanvasAgg
    # queries the bbox directly rather than using get_width_height() so requires
    # workaround), (2) override bbox and bbox_inches as *properties* (but these
    # are really complicated, dangerous, and result in unnecessary extra draws),
    # or (3) simply override canvas draw methods. Our choice is #3.
    def _needs_post_tight_layout(fig):
        """
        Return True if the figure should run a second tight-layout pass after draw.
        """
        if not getattr(fig, "_tight_active", False):
            return False
        for ax in fig._iter_axes(hidden=True, children=False):
            name = getattr(ax, "_name", None) or getattr(ax, "name", None)
            if name in ("polar",):
                return True
        return False

    def _canvas_preprocess(self, *args, **kwargs):
        fig = self.figure  # update even if not stale! needed after saves
        func = getattr(type(self), method)  # the original method

        # Bail out if we are already adjusting layout
        # NOTE: The _is_adjusting check necessary when inserting new
        # gridspec rows or columns with the qt backend.
        # NOTE: Return value for macosx _draw is the renderer, for qt draw is
        # nothing, and for print_figure is some figure object, but this block
        # has never been invoked when calling print_figure.
        if fig._is_adjusting:
            if method == "_draw":  # macosx backend
                return fig._get_renderer()
            else:
                return

        skip_autolayout = getattr(fig, "_skip_autolayout", False)
        layout_dirty = getattr(fig, "_layout_dirty", False)
        if (
            skip_autolayout
            and getattr(fig, "_layout_initialized", False)
            and not layout_dirty
        ):
            fig._skip_autolayout = False
            return func(self, *args, **kwargs)
        fig._skip_autolayout = False

        # Adjust layout
        # NOTE: The authorized_context is needed because some backends disable
        # constrained layout or tight layout before printing the figure.
        ctx1 = fig._context_adjusting(cache=cache)
        ctx2 = fig._context_authorized()  # skip backend set_constrained_layout()
        ctx3 = rc.context(fig._render_context)  # draw with figure-specific setting
        with ctx1, ctx2, ctx3:
            needs_post_layout = False
            if not fig._layout_initialized or layout_dirty:
                fig.auto_layout()
                fig._layout_initialized = True
                fig._layout_dirty = False
                needs_post_layout = _needs_post_tight_layout(fig)
            result = func(self, *args, **kwargs)
            if needs_post_layout:
                fig.auto_layout()
                result = func(self, *args, **kwargs)
            return result

    # Add preprocessor
    setattr(canvas, method, _canvas_preprocess.__get__(canvas))
    return canvas


def _clear_border_cache(func):
    """
    Decorator that clears the border cache after function execution.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, "_cached_border_axes"):
            delattr(self, "_cached_border_axes")
        return result

    return wrapper


class Figure(mfigure.Figure):
    """
    The `~matplotlib.figure.Figure` subclass used by ultraplot.
    """

    # Shared error and warning messages
    _share_message = (
        "Axis sharing level can be 0 or False (share nothing), "
        "1 or 'labels' or 'labs' (share axis labels), "
        "2 or 'limits' or 'lims' (share axis limits and axis labels), "
        "3 or True (share axis limits, axis labels, and tick labels), "
        "4 or 'all' (share axis labels and tick labels in the same gridspec "
        "rows and columns and share axis limits across all subplots), "
        "or 'auto' (start unshared and share only compatible axes)."
    )
    _space_message = (
        "To set the left, right, bottom, top, wspace, or hspace gridspec values, "
        "pass them as keyword arguments to uplt.figure() or uplt.subplots(). Please "
        "note they are now specified in physical units, with strings interpreted by "
        "uplt.units() and floats interpreted as font size-widths."
    )
    _tight_message = (
        "ultraplot uses its own tight layout algorithm that is activated by default. "
        "To disable it, set uplt.rc['subplots.tight'] to False or pass tight=False "
        "to uplt.subplots(). For details, see fig.auto_layout()."
    )
    _warn_interactive = True  # disabled after first warning

    def __repr__(self):
        opts = {}
        for attr in ("refaspect", "refwidth", "refheight", "figwidth", "figheight"):
            value = getattr(self, "_" + attr)
            if value is not None:
                opts[attr] = np.round(value, 2)
        geom = ""
        if self.gridspec:
            nrows, ncols = self.gridspec.get_geometry()
            geom = f"nrows={nrows}, ncols={ncols}, "
        opts = ", ".join(f"{key}={value!r}" for key, value in opts.items())
        return f"Figure({geom}{opts})"

    # NOTE: If _rename_kwargs argument is an invalid identifier, it is
    # simply used in the warning message.
    @docstring._obfuscate_kwargs
    @docstring._snippet_manager
    @warnings._rename_kwargs(
        "0.7.0", axpad="innerpad", autoformat="uplt.rc.autoformat = {}"
    )
    def __init__(
        self,
        *,
        refnum=None,
        ref=None,
        refaspect=None,
        aspect=None,
        refwidth=None,
        refheight=None,
        axwidth=None,
        axheight=None,
        figwidth=None,
        figheight=None,
        width=None,
        height=None,
        journal=None,
        sharex=None,
        sharey=None,
        share=None,  # used for default spaces
        spanx=None,
        spany=None,
        span=None,
        alignx=None,
        aligny=None,
        align=None,
        left=None,
        right=None,
        top=None,
        bottom=None,
        wspace=None,
        hspace=None,
        space=None,
        tight=None,
        outerpad=None,
        innerpad=None,
        panelpad=None,
        wpad=None,
        hpad=None,
        pad=None,
        wequal=None,
        hequal=None,
        equal=None,
        wgroup=None,
        hgroup=None,
        group=None,
        **kwargs,
    ):
        """
        Parameters
        ----------
        %(figure.figure)s

        Other parameters
        ----------------
        %(figure.format)s
        **kwargs
            Passed to `matplotlib.figure.Figure`.

        See also
        --------
        Figure.format
        ultraplot.ui.figure
        ultraplot.ui.subplots
        matplotlib.figure.Figure
        """
        size_options = resolve_size_options(
            refnum=refnum,
            ref=ref,
            refaspect=refaspect,
            aspect=aspect,
            refwidth=refwidth,
            refheight=refheight,
            axwidth=axwidth,
            axheight=axheight,
            figwidth=figwidth,
            figheight=figheight,
            width=width,
            height=height,
            journal=journal,
            journal_size_resolver=_get_journal_size,
            backend_name=_not_none(rc.backend, ""),
            warn_interactive_enabled=self._warn_interactive,
        )
        self._refnum = size_options.refnum
        self._refaspect = size_options.refaspect
        self._refaspect_default = 1  # updated for imshow and geographic plots
        self._refwidth = size_options.refwidth
        self._refheight = size_options.refheight
        self._figwidth = figwidth = size_options.figwidth
        self._figheight = figheight = size_options.figheight
        if size_options.interactive_warning:
            Figure._warn_interactive = False
            warnings._warn_ultraplot(
                "Auto-sized ultraplot figures are not compatible with interactive "
                "backends like '%matplotlib widget' and '%matplotlib notebook'. "
                f"Reverting to the figure size ({figwidth}, {figheight}). To make "
                "auto-sized figures, please consider using the non-interactive "
                "(default) backend. This warning message is shown the first time "
                "you create a figure without explicitly specifying the size."
            )

        self._gridspec_params = build_gridspec_params(
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace,
            space=space,
            wequal=wequal,
            hequal=hequal,
            equal=equal,
            wgroup=wgroup,
            hgroup=hgroup,
            group=group,
            wpad=wpad,
            hpad=hpad,
            pad=pad,
            outerpad=outerpad,
            innerpad=innerpad,
            panelpad=panelpad,
        )
        self._tight_active = resolve_tight_active(
            kwargs,
            tight=tight,
            space_message=self._space_message,
            tight_message=self._tight_message,
        )

        share_options = resolve_share_options(
            sharex=sharex,
            sharey=sharey,
            share=share,
            share_message=self._share_message,
        )
        self._sharex = share_options.sharex
        self._sharey = share_options.sharey
        self._sharex_auto = share_options.sharex_auto
        self._sharey_auto = share_options.sharey_auto
        self._share_incompat_warned = False

        span_align = resolve_span_align_options(
            sharex=self._sharex,
            sharey=self._sharey,
            spanx=spanx,
            spany=spany,
            span=span,
            alignx=alignx,
            aligny=aligny,
            align=align,
        )
        self._spanx = span_align.spanx
        self._spany = span_align.spany
        self._alignx = span_align.alignx
        self._aligny = span_align.aligny

        # Initialize the figure
        # NOTE: Super labels are stored inside {axes: text} dictionaries
        self._gridspec = None
        self._panel_dict = {"left": [], "right": [], "bottom": [], "top": []}
        self._subplot_dict = {}  # subplots indexed by number
        self._subplot_counter = 0  # avoid add_subplot() returning an existing subplot
        self._is_adjusting = False
        self._is_authorized = False
        self._layout_initialized = False
        self._layout_dirty = True
        self._skip_autolayout = False
        self._includepanels = None
        # Figure is the facade and state owner. Helper objects own most policy:
        # projection/subplot creation, layout queries, guide placement, sharing,
        # and spanning-label orchestration. Keep cross-module interactions going
        # through Figure._... methods rather than reaching into helpers directly
        # unless the caller lives wholly inside the same internal subsystem.
        self._layout_helper = FigureLayout(self)
        self._factory_helper = FigureFactory(self)
        self._guide_helper = FigureGuides(self)
        self._label_helper = FigureLabels(self)
        self._panel_helper = FigurePanels(self)
        self._share_helper = FigureSharing(self)
        self._format_helper = FigureFormatting(self)
        self._render_context = {}
        rc_kw, rc_mode = _pop_rc(kwargs)
        kw_format = _pop_params(kwargs, self._format_signature)
        if figwidth is not None and figheight is not None:
            kwargs["figsize"] = (figwidth, figheight)
        with self._context_authorized():
            super().__init__(**kwargs)

        # Super labels. We don't rely on private matplotlib _suptitle attribute and
        # _align_axis_labels supports arbitrary spanning labels for subplot groups.
        # NOTE: Don't use 'anchor' rotation mode otherwise switching to horizontal
        # left and right super labels causes overlap. Current method is fine.
        self._suptitle = self.text(0.5, 0.95, "", ha="center", va="bottom")
        self._supxlabel_dict = {}  # an axes: label mapping
        self._supylabel_dict = {}  # an axes: label mapping
        self._suplabel_dict = {"left": {}, "right": {}, "bottom": {}, "top": {}}
        self._share_label_groups = {"x": {}, "y": {}}  # explicit label-sharing groups
        self._suptitle_pad = rc["suptitle.pad"]
        d = self._suplabel_props = {}  # store the super label props
        d["left"] = {"va": "center", "ha": "right"}
        d["right"] = {"va": "center", "ha": "left"}
        d["bottom"] = {"va": "top", "ha": "center"}
        d["top"] = {"va": "bottom", "ha": "center"}
        d = self._suplabel_pad = {}  # store the super label padding
        d["left"] = rc["leftlabel.pad"]
        d["right"] = rc["rightlabel.pad"]
        d["bottom"] = rc["bottomlabel.pad"]
        d["top"] = rc["toplabel.pad"]

        # Format figure
        # NOTE: This ignores user-input rc_mode.
        self.format(rc_kw=rc_kw, rc_mode=1, skip_axes=True, **kw_format)

    @override
    def draw(self, renderer):
        self._snap_axes_to_pixel_grid(renderer)
        # implement the tick sharing here
        # should be shareable --> either all cartesian or all geographic
        # but no mixing (panels can be mixed)
        # check which ticks are on for x or y and push the labels to the
        # outer most on a given column or row.
        # we can use get_border_axes for the outermost plots and then collect their outermost panels that are not colorbars
        self._share_helper.share_ticklabels(axis="x")
        self._share_helper.share_ticklabels(axis="y")
        self._label_helper.apply_share_label_groups()
        super().draw(renderer)

    @override
    def draw_without_rendering(self):
        """
        Draw without output while preserving figure dpi state.
        """
        dpi = self.dpi
        try:
            return super().draw_without_rendering()
        finally:
            if self.dpi != dpi:
                mfigure.Figure.set_dpi(self, dpi)

    def _is_auto_share_mode(self, which: str) -> bool:
        """Return whether a given axis uses auto-share mode."""
        if which not in ("x", "y"):
            return False
        return bool(getattr(self, f"_share{which}_auto", False))

    def _share_axes_compatible(self, ref, other, which: str):
        """Check whether two axes are compatible for sharing along one axis."""
        return self._share_helper.share_axes_compatible(ref, other, which)

    def _warn_incompatible_share(self, which: str, ref, other, reason: str) -> None:
        """Warn once per figure for explicit incompatible sharing."""
        self._share_helper.warn_incompatible_share(which, ref, other, reason)

    def _partition_share_axes(self, axes, which: str):
        """Partition a candidate share list into compatible sub-groups."""
        return self._share_helper.partition_share_axes(axes, which)

    def _refresh_auto_share(self, which: Optional[str] = None) -> None:
        """Recompute auto-sharing groups after local axis-state changes."""
        self._share_helper.refresh_auto_share(which)

    def _snap_axes_to_pixel_grid(self, renderer) -> None:
        """
        Snap visible axes bounds to the renderer pixel grid.
        """
        if not rc.find("subplots.pixelsnap", context=True):
            return

        width = getattr(renderer, "width", None)
        height = getattr(renderer, "height", None)
        if not width or not height:
            return

        width = float(width)
        height = float(height)
        if width <= 0 or height <= 0:
            return

        invw = 1.0 / width
        invh = 1.0 / height
        minw = invw
        minh = invh

        # Only snap main subplot axes. Guide/panel axes host legends/colorbars
        # that use their own fractional placement and can be over-constrained.
        for ax in self._iter_axes(hidden=False, children=False, panels=False):
            bbox = ax.get_position(original=False)
            old = np.array([bbox.x0, bbox.y0, bbox.x1, bbox.y1], dtype=float)
            new = np.array(
                [
                    round(old[0] * width) * invw,
                    round(old[1] * height) * invh,
                    round(old[2] * width) * invw,
                    round(old[3] * height) * invh,
                ],
                dtype=float,
            )

            if new[2] <= new[0]:
                new[2] = new[0] + minw
            if new[3] <= new[1]:
                new[3] = new[1] + minh

            if np.allclose(new, old, rtol=0.0, atol=1e-12):
                continue
            ax.set_position(
                [new[0], new[1], new[2] - new[0], new[3] - new[1]],
                which="both",
            )

    def _context_adjusting(self, cache=True):
        """
        Prevent re-running auto layout steps due to draws triggered by figure
        resizes. Otherwise can get infinite loops.
        """
        kw = {"_is_adjusting": True}
        if not cache:
            kw["_cachedRenderer"] = None  # temporarily ignore it
        return context._state_context(self, **kw)

    def _context_authorized(self):
        """
        Prevent warning message when internally calling no-op methods. Otherwise
        emit warnings to help new users.
        """
        return context._state_context(self, _is_authorized=True)

    @staticmethod
    def _parse_backend(backend=None, basemap=None):
        """
        Handle deprecation of basemap and cartopy package.
        """
        # Basemap is currently being developed again so are removing the deprecation warning
        if backend == "basemap":
            warnings._warn_ultraplot(
                f"{backend=} will be deprecated in next major release (v2.0). See https://github.com/Ultraplot/ultraplot/pull/243"
            )
        return backend

    def _parse_proj(
        self,
        proj=None,
        projection=None,
        proj_kw=None,
        projection_kw=None,
        backend=None,
        basemap=None,
        **kwargs,
    ):
        """
        Translate the user-input projection into a registered matplotlib
        axes class. Input projection can be a string, `matplotlib.axes.Axes`,
        `cartopy.crs.Projection`, or `mpl_toolkits.basemap.Basemap`.
        """
        return self._factory_helper.parse_proj(
            proj=proj,
            projection=projection,
            proj_kw=proj_kw,
            projection_kw=projection_kw,
            backend=backend,
            basemap=basemap,
            **kwargs,
        )

    def _get_align_axes(self, side):
        """Return the main axes along the requested edge of the figure."""
        return self._layout_helper.get_align_axes(side)

    def _get_border_axes(
        self, *, same_type=False, force_recalculate=False
    ) -> dict[str, list[paxes.Axes]]:
        """Return the axes on each outer border of the figure grid."""
        return self._layout_helper.get_border_axes(
            same_type=same_type,
            force_recalculate=force_recalculate,
        )

    def _get_align_coord(self, side, axs, align="center", includepanels=False):
        """Return the alignment coordinate for spanning labels or super titles."""
        return self._layout_helper.get_align_coord(
            side,
            axs,
            align=align,
            includepanels=includepanels,
        )

    def _get_offset_coord(self, side, axs, renderer, *, pad=None, extra=None):
        """Return the offset coordinate for super labels and super titles."""
        return self._layout_helper.get_offset_coord(
            side,
            axs,
            renderer,
            pad=pad,
            extra=extra,
        )

    def _get_renderer(self):
        """Get a renderer at all costs."""
        return self._layout_helper.get_renderer()

    @_clear_border_cache
    def _add_axes_panel(
        self,
        ax: "paxes.Axes",
        side: Optional[str] = None,
        span: Optional[Union[int, Tuple[int, int]]] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        rows: Optional[Union[int, Tuple[int, int]]] = None,
        cols: Optional[Union[int, Tuple[int, int]]] = None,
        **kwargs,
    ) -> "paxes.Axes":
        """
        Add an axes panel.
        """
        return self._panel_helper.add_axes_panel(
            ax,
            side=side,
            span=span,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            **kwargs,
        )

    @_clear_border_cache
    def _add_figure_panel(
        self,
        side: Optional[str] = None,
        span: Optional[Union[int, Tuple[int, int]]] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        rows: Optional[Union[int, Tuple[int, int]]] = None,
        cols: Optional[Union[int, Tuple[int, int]]] = None,
        **kwargs,
    ) -> "paxes.Axes":
        """
        Add a figure panel.
        """
        self._layout_dirty = True
        # Interpret args and enforce sensible keyword args
        side = _translate_loc(side, "panel", default="right")
        if side in ("left", "right"):
            for key, value in (("col", col), ("cols", cols)):
                if value is not None:
                    raise ValueError(f"Invalid keyword {key!r} for {side!r} panel.")
            span = _not_none(span=span, row=row, rows=rows)
        else:
            for key, value in (("row", row), ("rows", rows)):
                if value is not None:
                    raise ValueError(f"Invalid keyword {key!r} for {side!r} panel.")
            span = _not_none(span=span, col=col, cols=cols)

        # Add and setup panel
        # NOTE: This is only called internally by colorbar and legend so
        # do not need to pass aribtrary axes keyword arguments.
        gs = self.gridspec
        if not gs:
            raise RuntimeError("The gridspec must be active.")
        ss, _ = gs._insert_panel_slot(side, span, filled=True, **kwargs)
        pax = self.add_subplot(ss, autoshare=False, number=False)
        plist = self._panel_dict[side]
        plist.append(pax)
        pax._panel_side = side
        pax._panel_share = False
        pax._panel_parent = None
        return pax

    @_clear_border_cache
    def _add_subplot(self, *args, **kwargs):
        """
        The driver function for adding single subplots.
        """
        return self._factory_helper.add_subplot(*args, **kwargs)

    def _unshare_axes(self):

        for which in "xyz":
            self._toggle_axis_sharing(which=which, share=False)
        # Force setting extent
        # This is necessary to ensure that the axes are properly
        # aligned and we don't get weird scaling issues for
        #  geographic axes. This action is expensive for GeoAxes
        for ax in self.axes:
            if isinstance(ax, paxes.GeoAxes) and hasattr(ax, "set_global"):
                ax.set_global()

    def _toggle_axis_sharing(
        self,
        *,
        which="y",
        share=True,
        panels=False,
        children=False,
        hidden=False,
    ):
        """
        Share or unshare axes in the figure along a given direction.

        Parameters:
        - which: 'x', 'y', 'z', or 'view'.
        - share: int indicating the levels (see above)
        - panels: Whether to include panel axes.
        - children: Whether to include child axes.
        - hidden: Whether to include hidden axes.
        """
        self._share_helper.toggle_axis_sharing(
            which=which,
            share=share,
            panels=panels,
            children=children,
            hidden=hidden,
        )

    def _add_subplots(
        self,
        array=None,
        nrows=1,
        ncols=1,
        order="C",
        proj=None,
        projection=None,
        proj_kw=None,
        projection_kw=None,
        backend=None,
        basemap=None,
        **kwargs,
    ):
        """
        The driver function for adding multiple subplots.
        """
        return self._factory_helper.add_subplots(
            array=array,
            nrows=nrows,
            ncols=ncols,
            order=order,
            proj=proj,
            projection=projection,
            proj_kw=proj_kw,
            projection_kw=projection_kw,
            backend=backend,
            basemap=basemap,
            **kwargs,
        )

    def _register_share_label_group(self, axes, *, target, source=None):
        """
        Register an explicit label-sharing group for a subset of axes.
        """
        self._label_helper.register_share_label_group(
            axes,
            target=target,
            source=source,
        )

    def _is_share_label_group_member(self, ax, axis):
        """
        Return True if the axes belongs to any explicit label-sharing group.
        """
        return self._label_helper.is_share_label_group_member(ax, axis)

    def _clear_share_label_groups(self, axes=None, *, target=None):
        """
        Clear explicit label-sharing groups, optionally filtered by axes.
        """
        self._label_helper.clear_share_label_groups(axes=axes, target=target)

    def _update_super_labels(self, side, labels, **kwargs):
        """
        Assign the figure super labels and update settings.
        """
        self._label_helper.update_super_labels(side, labels, **kwargs)

    def _update_super_title(self, title, **kwargs):
        """
        Assign the figure super title and update settings.
        """
        self._label_helper.update_super_title(title, **kwargs)

    @_clear_border_cache
    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def add_axes(self, rect, **kwargs):
        """
        %(figure.axes)s
        """
        kwargs = self._parse_proj(**kwargs)
        return super().add_axes(rect, **kwargs)

    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def add_subplot(self, *args, **kwargs):
        """
        %(figure.subplot)s
        """
        return self._add_subplot(*args, **kwargs)

    @docstring._snippet_manager
    def subplot(self, *args, **kwargs):  # shorthand
        """
        %(figure.subplot)s
        """
        return self._add_subplot(*args, **kwargs)

    @docstring._snippet_manager
    def add_subplots(self, *args, **kwargs):
        """
        %(figure.subplots)s
        """
        return self._add_subplots(*args, **kwargs)

    @docstring._snippet_manager
    def subplots(self, *args, **kwargs):
        """
        %(figure.subplots)s
        """
        return self._add_subplots(*args, **kwargs)

    def auto_layout(self, renderer=None, aspect=None, tight=None, resize=None):
        """
        Automatically adjust the figure size and subplot positions. This is
        triggered automatically whenever the figure is drawn.

        Parameters
        ----------
        renderer : `~matplotlib.backend_bases.RendererBase`, optional
            The renderer. If ``None`` a default renderer will be produced.
        aspect : bool, optional
            Whether to update the figure size based on the reference subplot aspect
            ratio. By default, this is ``True``. This only has an effect if the
            aspect ratio is fixed (e.g., due to an image plot or geographic projection).
        tight : bool, optional
            Whether to update the figuer size and subplot positions according to
            a "tight layout". By default, this takes on the value of `tight` passed
            to `Figure`. If nothing was passed, it is :rc:`subplots.tight`.
        resize : bool, optional
            If ``False``, the current figure dimensions are fixed and automatic
            figure resizing is disabled. By default, the figure size may change
            unless both `figwidth` and `figheight` or `figsize` were passed
            to `~Figure.subplots`, `~Figure.set_size_inches` was called manually,
            or the figure was resized manually with an interactive backend.
        """
        # *Impossible* to get notebook backend to work with auto resizing so we
        # just do the tight layout adjustments and skip resizing.
        gs = self.gridspec
        renderer = self._get_renderer()
        if aspect is None:
            aspect = True
        if tight is None:
            tight = self._tight_active
        if resize is False:  # fix the size
            self._figwidth, self._figheight = self.get_size_inches()
            self._refwidth = self._refheight = None  # critical!

        # Helper functions
        # NOTE: Have to draw legends and colorbars early (before reaching axes
        # draw methods) because we have to take them into account for alignment.
        # Also requires another figure resize (which triggers a gridspec update).
        def _draw_content():
            for ax in self._iter_axes(hidden=False, children=True):
                ax._add_queued_guides()  # may trigger resizes if panels are added

        def _align_content():  # noqa: E306
            for axis in "xy":
                self._label_helper.align_axis_label(axis)
            for side in ("left", "right", "top", "bottom"):
                self._label_helper.align_super_labels(side, renderer)
            self._label_helper.align_super_title(renderer)

        # Update the layout
        # WARNING: Tried to avoid two figure resizes but made
        # subsequent tight layout really weird. Have to resize twice.
        _draw_content()
        if not gs:
            return
        if aspect:
            gs._auto_layout_aspect()
        _align_content()
        if tight:
            gs._auto_layout_tight(renderer)
        _align_content()

    @warnings._rename_kwargs(
        "0.10.0", mathtext_fallback="uplt.rc.mathtext_fallback = {}"
    )
    @docstring._snippet_manager
    def format(
        self,
        axs=None,
        *,
        figtitle=None,
        suptitle=None,
        suptitle_kw=None,
        llabels=None,
        leftlabels=None,
        leftlabels_kw=None,
        rlabels=None,
        rightlabels=None,
        rightlabels_kw=None,
        blabels=None,
        bottomlabels=None,
        bottomlabels_kw=None,
        tlabels=None,
        toplabels=None,
        toplabels_kw=None,
        rowlabels=None,
        collabels=None,  # aliases
        includepanels=None,
        **kwargs,
    ):
        """
        Modify figure-wide labels and call ``format`` for the
        input axes. By default the numbered subplots are used.

        Parameters
        ----------
        axs : sequence of `~ultraplot.axes.Axes`, optional
            The axes to format. Default is the numbered subplots.
        %(figure.format)s

        Important
        ---------
        `leftlabelpad`, `toplabelpad`, `rightlabelpad`, and `bottomlabelpad`
        keywords are actually :ref:`configuration settings <ug_config>`.
        We explicitly document these arguments here because it is common to
        change them for specific figures. But many :ref:`other configuration
        settings <ug_format>` can be passed to ``format`` too.

        Other parameters
        ----------------
        %(axes.format)s
        %(cartesian.format)s
        %(polar.format)s
        %(geo.format)s
        %(rc.format)s

        See also
        --------
        ultraplot.axes.Axes.format
        ultraplot.axes.CartesianAxes.format
        ultraplot.axes.PolarAxes.format
        ultraplot.axes.GeoAxes.format
        ultraplot.gridspec.SubplotGrid.format
        ultraplot.config.Configurator.context
        """
        return self._format_helper.format(
            axs=axs,
            figtitle=figtitle,
            suptitle=suptitle,
            suptitle_kw=suptitle_kw,
            llabels=llabels,
            leftlabels=leftlabels,
            leftlabels_kw=leftlabels_kw,
            rlabels=rlabels,
            rightlabels=rightlabels,
            rightlabels_kw=rightlabels_kw,
            blabels=blabels,
            bottomlabels=bottomlabels,
            bottomlabels_kw=bottomlabels_kw,
            tlabels=tlabels,
            toplabels=toplabels,
            toplabels_kw=toplabels_kw,
            rowlabels=rowlabels,
            collabels=collabels,
            includepanels=includepanels,
            **kwargs,
        )

    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def colorbar(
        self,
        mappable,
        values=None,
        loc: Optional[str] = None,
        location: Optional[str] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        rows: Optional[Union[int, Tuple[int, int]]] = None,
        cols: Optional[Union[int, Tuple[int, int]]] = None,
        span: Optional[Union[int, Tuple[int, int]]] = None,
        space: Optional[Union[float, str]] = None,
        pad: Optional[Union[float, str]] = None,
        width: Optional[Union[float, str]] = None,
        **kwargs,
    ):
        """
        Add a colorbar along the side of the figure.

        Parameters
        ----------
        %(axes.colorbar_args)s
        length : float, default: :rc:`colorbar.length`
            The colorbar length. Units are relative to the span of the rows and
            columns of subplots.
        shrink : float, optional
            Alias for `length`. This is included for consistency with
            `matplotlib.figure.Figure.colorbar`.
        width : unit-spec, default: :rc:`colorbar.width`
            The colorbar width.
            %(units.in)s
        %(figure.colorbar_space)s
            Has no visible effect if `length` is ``1``.

        Other parameters
        ----------------
        %(axes.colorbar_kwargs)s

        See also
        --------
        ultraplot.axes.Axes.colorbar
        matplotlib.figure.Figure.colorbar
        """
        return self._guide_helper.colorbar(
            mappable,
            values,
            loc=loc,
            location=location,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            span=span,
            space=space,
            pad=pad,
            width=width,
            **kwargs,
        )

    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def legend(
        self,
        handles=None,
        labels=None,
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
        """
        Add a legend along the side of the figure.

        Parameters
        ----------
        %(axes.legend_args)s
        %(figure.legend_space)s
        width : unit-spec, optional
            The space allocated for the legend box. This does nothing if
            the :ref:`tight layout algorithm <ug_tight>` is active for the figure.
            %(units.in)s

        Other parameters
        ----------------
        %(axes.legend_kwargs)s

        See also
        --------
        ultraplot.axes.Axes.legend
        matplotlib.axes.Axes.legend
        """
        return self._guide_helper.legend(
            handles,
            labels,
            loc=loc,
            location=location,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            span=span,
            space=space,
            pad=pad,
            width=width,
            **kwargs,
        )

    @docstring._snippet_manager
    def save(self, filename, **kwargs):
        """
        %(figure.save)s
        """
        return self.savefig(filename, **kwargs)

    @docstring._concatenate_inherited
    @docstring._snippet_manager
    def savefig(self, filename, **kwargs):
        """
        %(figure.save)s
        """
        # Automatically expand the user name. Undocumented because we
        # do not want to overwrite the matplotlib docstring.
        if isinstance(filename, str):
            filename = os.path.expanduser(filename)
        # NOTE: this draw ensures that we are applying ultraplots layout adjustment. It is unclear what changed with ultraplot's history that makes this necessary, but it seems to cause no issues. Future devs, if unnecessary remove this line and test.
        self.canvas.draw()
        super().savefig(filename, **kwargs)

    @docstring._concatenate_inherited
    def set_canvas(self, canvas):
        """
        Set the figure canvas. Add monkey patches for the instance-level
        `~matplotlib.backend_bases.FigureCanvasBase.draw` and
        `~matplotlib.backend_bases.FigureCanvasBase.print_figure` methods.

        Parameters
        ----------
        canvas : `~matplotlib.backend_bases.FigureCanvasBase`
            The figure canvas.

        See also
        --------
        matplotlib.figure.Figure.set_canvas
        """
        # NOTE: Use the _draw method if it exists, e.g. for osx backends. Critical
        # or else wrong renderer size is used.
        # NOTE: See _add_canvas_preprocessor for details. Critical to not add cache
        # print_figure renderer when the print method (print_pdf, print_png, etc.)
        # calls Figure.draw(). Otherwise have issues where (1) figure size and/or
        # bounds are incorrect after saving figure *then* displaying it in qt or inline
        # notebook backends, and (2) figure fails to update correctly after successively
        # modifying and displaying within inline notebook backend (previously worked
        # around this by forcing additional draw() call in this function before
        # proceeding with print_figure). Set the canvas and add monkey patches
        # to the instance-level draw and print_figure methods.
        method = "draw"
        # if getattr(canvas, "_draw", None):
        # method = "_draw"
        # method = '_draw' if callable(getattr(canvas, '_draw', None)) else 'draw'
        _add_canvas_preprocessor(canvas, "print_figure", cache=False)  # saves, inlines
        _add_canvas_preprocessor(canvas, method, cache=True)  # renderer displays

        orig_draw_idle = getattr(type(canvas), "draw_idle", None)
        if orig_draw_idle is not None:

            def _draw_idle(self, *args, **kwargs):
                fig = self.figure
                if fig is not None:
                    fig._skip_autolayout = True
                return orig_draw_idle(self, *args, **kwargs)

            canvas.draw_idle = _draw_idle.__get__(canvas)
        super().set_canvas(canvas)

    def _is_same_size(self, figsize, eps=None):
        """
        Test if the figure size is unchanged up to some tolerance in inches.
        """
        return self._layout_helper.is_same_size(figsize, eps)

    @docstring._concatenate_inherited
    def set_size_inches(self, w, h=None, *, forward=True, internal=False, eps=None):
        """
        Set the figure size. If this is being called manually or from an interactive
        backend, update the default layout with this fixed size. If the figure size is
        unchanged or this is an internal call, do not update the default layout.

        Parameters
        ----------
        *args : float
            The width and height passed as positional arguments or a 2-tuple.
        forward : bool, optional
            Whether to update the canvas.
        internal : bool, optional
            Whether this is an internal resize.
        eps : float, optional
            The deviation from the current size in inches required to treat this
            as a user-triggered figure resize that fixes the layout.

        See also
        --------
        matplotlib.figure.Figure.set_size_inches
        """
        self._layout_helper.set_size_inches(
            w,
            h,
            forward=forward,
            internal=internal,
            eps=eps,
        )

    def _iter_axes(self, hidden=False, children=False, panels=True):
        """
        Iterate over all axes and panels in the figure belonging to the
        `~ultraplot.axes.Axes` class. Exclude inset and twin axes.

        Parameters
        ----------
        hidden : bool, optional
            Whether to include "hidden" panels.
        children : bool, optional
            Whether to include child axes. Note this now includes "twin" axes.
        panels : bool or str or sequence of str, optional
            Whether to include panels or the panels to include.
        """
        yield from self._layout_helper.iter_axes(
            hidden=hidden,
            children=children,
            panels=panels,
        )

    @property
    def gridspec(self):
        """
        The single :class:`~ultraplot.gridspec.GridSpec` instance used for all
        subplots in the figure.

        See also
        --------
        ultraplot.figure.Figure.subplotgrid
        ultraplot.gridspec.GridSpec.figure
        ultraplot.gridspec.SubplotGrid.gridspec
        """
        return self._gridspec

    @gridspec.setter
    def gridspec(self, gs):
        if not isinstance(gs, pgridspec.GridSpec):
            raise ValueError("Gridspec must be a ultraplot.GridSpec instance.")
        self._gridspec = gs
        gs.figure = self  # trigger copying settings from the figure

    @property
    def subplotgrid(self):
        """
        A :class:`~ultraplot.gridspec.SubplotGrid` containing the numbered subplots in the
        figure. The subplots are ordered by increasing `~ultraplot.axes.Axes.number`.

        See also
        --------
        ultraplot.figure.Figure.gridspec
        ultraplot.gridspec.SubplotGrid.figure
        """
        return pgridspec.SubplotGrid([s for _, s in sorted(self._subplot_dict.items())])

    @property
    def tight(self):
        """
        Whether the :ref:`tight layout algorithm <ug_tight>` is active for the
        figure. This value is passed to `~ultraplot.figure.Figure.auto_layout`
        every time the figure is drawn. Can be changed e.g. ``fig.tight = False``.

        See also
        --------
        ultraplot.figure.Figure.auto_layout
        """
        return self._tight_active

    @tight.setter
    def tight(self, b):
        self._tight_active = bool(b)

    # Apply signature obfuscation after getting keys
    # NOTE: This is needed for axes and figure instantiation.
    _format_signature = inspect.signature(format)
    format = docstring._obfuscate_kwargs(format)


# Add deprecated properties. There are *lots* of properties we pass to Figure
# and do not like idea of publicly tracking every single one of them. If we
# want to improve user introspection consider modifying Figure.__repr__.
for _attr in ("alignx", "aligny", "sharex", "sharey", "spanx", "spany", "tight", "ref"):

    def _get_deprecated(self, attr=_attr):
        warnings._warn_ultraplot(
            f"The property {attr!r} is no longer public as of v0.8. It will be "
            "removed in a future release."
        )
        return getattr(self, "_" + attr)

    _getter = property(_get_deprecated)
    setattr(Figure, _attr, property(_get_deprecated))


# Disable native matplotlib layout and spacing functions when called
# manually and emit warning message to help new users.
for _attr, _msg in (
    ("set_tight_layout", Figure._tight_message),
    ("set_constrained_layout", Figure._tight_message),
    ("tight_layout", Figure._tight_message),
    ("init_layoutbox", Figure._tight_message),
    ("execute_constrained_layout", Figure._tight_message),
    ("subplots_adjust", Figure._space_message),
):
    _func = getattr(Figure, _attr, None)
    if _func is None:
        continue

    @functools.wraps(_func)  # noqa: E301
    def _disable_method(self, *args, func=_func, message=_msg, **kwargs):
        message = (
            f"fig.{func.__name__}() has no effect on ultraplot figures. " + message
        )
        if self._is_authorized:
            return func(self, *args, **kwargs)
        else:
            warnings._warn_ultraplot(message)  # noqa: E501, U100

    _disable_method.__doc__ = None  # remove docs
    setattr(Figure, _attr, _disable_method)
