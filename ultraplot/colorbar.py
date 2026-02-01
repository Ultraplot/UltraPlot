# Auto-extracted colorbar builder
from dataclasses import dataclass
from typing import Any, Iterable, MutableMapping, Optional, Tuple, Union
from numbers import Number
import numpy as np
import matplotlib.axes as maxes
import matplotlib.cm as mcm
import matplotlib.colorbar as mcolorbar
import matplotlib.colors as mcolors
import matplotlib.contour as mcontour
import matplotlib.figure as mfigure
import matplotlib.ticker as mticker
import matplotlib.offsetbox as moffsetbox
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
import matplotlib.text as mtext
from packaging import version

from . import constructor, colors as pcolors
from .internals import _not_none, _pop_params, guides, warnings
from .config import rc, _version_mpl
from .ultralayout import KIWI_AVAILABLE, ColorbarLayoutSolver
from . import ticker as pticker
from .utils import units


ColorbarLabelKw = dict[str, Any]
ColorbarTickKw = dict[str, Any]


@dataclass(frozen=True)
class _TextKw:
    kw_label: ColorbarLabelKw
    kw_ticklabels: ColorbarTickKw


class UltraColorbar:
    """
    Centralized colorbar builder for axes.
    """

    def __init__(self, axes: maxes.Axes):
        self.axes = axes

    def add(
        self,
        mappable: Any,
        values: Optional[Iterable[float]] = None,
        *,
        loc: Optional[str] = None,
        align: Optional[str] = None,
        space: Optional[Union[float, str]] = None,
        pad: Optional[Union[float, str]] = None,
        width: Optional[Union[float, str]] = None,
        length: Optional[Union[float, str]] = None,
        span: Optional[Union[int, Tuple[int, int]]] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        rows: Optional[Union[int, Tuple[int, int]]] = None,
        cols: Optional[Union[int, Tuple[int, int]]] = None,
        shrink: Optional[Union[float, str]] = None,
        label: Optional[str] = None,
        title: Optional[str] = None,
        reverse: bool = False,
        rotation: Optional[float] = None,
        grid: Optional[bool] = None,
        edges: Optional[bool] = None,
        drawedges: Optional[bool] = None,
        extend: Optional[str] = None,
        extendsize: Optional[Union[float, str]] = None,
        extendfrac: Optional[float] = None,
        ticks: Optional[Iterable[float]] = None,
        locator: Optional[Any] = None,
        locator_kw: Optional[dict[str, Any]] = None,
        format: Optional[str] = None,
        formatter: Optional[Any] = None,
        ticklabels: Optional[Iterable[str]] = None,
        formatter_kw: Optional[dict[str, Any]] = None,
        minorticks: Optional[bool] = None,
        minorlocator: Optional[Any] = None,
        minorlocator_kw: Optional[dict[str, Any]] = None,
        tickminor: Optional[bool] = None,
        ticklen: Optional[Union[float, str]] = None,
        ticklenratio: Optional[float] = None,
        tickdir: Optional[str] = None,
        tickdirection: Optional[str] = None,
        tickwidth: Optional[Union[float, str]] = None,
        tickwidthratio: Optional[float] = None,
        ticklabelsize: Optional[float] = None,
        ticklabelweight: Optional[str] = None,
        ticklabelcolor: Optional[str] = None,
        labelloc: Optional[str] = None,
        labellocation: Optional[str] = None,
        labelsize: Optional[float] = None,
        labelweight: Optional[str] = None,
        labelcolor: Optional[str] = None,
        c: Optional[str] = None,
        color: Optional[str] = None,
        lw: Optional[Union[float, str]] = None,
        linewidth: Optional[Union[float, str]] = None,
        edgefix: Optional[bool] = None,
        rasterized: Optional[bool] = None,
        outline: Union[bool, None] = None,
        labelrotation: Optional[Union[str, float]] = None,
        center_levels: Optional[bool] = None,
        **kwargs,
    ) -> mcolorbar.Colorbar:
        """
        The driver function for adding axes colorbars.
        """
        ax = self.axes
        # Parse input arguments and apply defaults
        # TODO: Get the 'best' inset colorbar location using the legend algorithm
        # and implement inset colorbars the same as inset legends.
        grid = _not_none(
            grid=grid, edges=edges, drawedges=drawedges, default=rc["colorbar.grid"]
        )  # noqa: E501
        length = _not_none(length=length, shrink=shrink)
        label = _not_none(title=title, label=label)
        labelloc = _not_none(labelloc=labelloc, labellocation=labellocation)
        locator = _not_none(ticks=ticks, locator=locator)
        formatter = _not_none(ticklabels=ticklabels, formatter=formatter, format=format)
        minorlocator = _not_none(minorticks=minorticks, minorlocator=minorlocator)
        color = _not_none(c=c, color=color, default=rc["axes.edgecolor"])
        linewidth = _not_none(lw=lw, linewidth=linewidth)
        ticklen = units(_not_none(ticklen, rc["tick.len"]), "pt")
        tickdir = _not_none(tickdir=tickdir, tickdirection=tickdirection)
        tickwidth = units(_not_none(tickwidth, linewidth, rc["tick.width"]), "pt")
        linewidth = units(_not_none(linewidth, default=rc["axes.linewidth"]), "pt")
        ticklenratio = _not_none(ticklenratio, rc["tick.lenratio"])
        tickwidthratio = _not_none(tickwidthratio, rc["tick.widthratio"])
        rasterized = _not_none(rasterized, rc["colorbar.rasterized"])
        center_levels = _not_none(center_levels, rc["colorbar.center_levels"])

        # Build label and locator keyword argument dicts
        # NOTE: This carefully handles the 'maxn' and 'maxn_minor' deprecations
        locator_kw = locator_kw or {}
        formatter_kw = formatter_kw or {}
        minorlocator_kw = minorlocator_kw or {}
        text_kw = _build_label_tick_kwargs(
            labelsize=labelsize,
            labelweight=labelweight,
            labelcolor=labelcolor,
            ticklabelsize=ticklabelsize,
            ticklabelweight=ticklabelweight,
            ticklabelcolor=ticklabelcolor,
            rotation=rotation,
        )
        for b, kw in enumerate((locator_kw, minorlocator_kw)):
            key = "maxn_minor" if b else "maxn"
            name = "minorlocator" if b else "locator"
            nbins = kwargs.pop("maxn_minor" if b else "maxn", None)
            if nbins is not None:
                kw["nbins"] = nbins
                warnings._warn_ultraplot(
                    f"The colorbar() keyword {key!r} was deprecated in v0.10. To "
                    "achieve the same effect, you can pass 'nbins' to the new default "
                    f"locator DiscreteLocator using {name}_kw={{'nbins': {nbins}}}. "
                )

        # Generate and prepare the colorbar axes
        # NOTE: The inset axes function needs 'label' to know how to pad the box
        # TODO: Use seperate keywords for frame properties vs. colorbar edge properties?
        if loc in ("fill", "left", "right", "top", "bottom"):
            length = _not_none(length, rc["colorbar.length"])  # for _add_guide_panel
            kwargs.update({"align": align, "length": length})
            extendsize = _not_none(extendsize, rc["colorbar.extend"])
            panel_ax = ax._add_guide_panel(
                loc,
                align,
                length=length,
                width=width,
                space=space,
                pad=pad,
                span=span,
                row=row,
                col=col,
                rows=rows,
                cols=cols,
            )  # noqa: E501
            cax, kwargs = panel_ax._parse_colorbar_filled(**kwargs)
        else:
            kwargs.update({"label": label, "length": length, "width": width})
            extendsize = _not_none(extendsize, rc["colorbar.insetextend"])
            cax, kwargs = ax._parse_colorbar_inset(
                loc=loc,
                labelloc=labelloc,
                labelrotation=labelrotation,
                labelsize=labelsize,
                pad=pad,
                **kwargs,
            )  # noqa: E501

        # Parse the colorbar mappable
        # NOTE: Account for special case where auto colorbar is generated from 1D
        # methods that construct an 'artist list' (i.e. colormap scatter object)
        mappable, kwargs = _resolve_mappable(mappable, values, cax, kwargs)

        # Parse 'extendsize' and 'extendfrac' keywords
        # TODO: Make this auto-adjust to the subplot size
        vert = kwargs["orientation"] == "vertical"
        extendfrac = _resolve_extendfrac(
            extendsize=extendsize,
            extendfrac=extendfrac,
            cax=cax,
            vertical=vert,
        )

        # Parse the tick locators and formatters
        # NOTE: In presence of BoundaryNorm or similar handle ticks with special
        # DiscreteLocator or else get issues (see mpl #22233).
        norm, formatter, locator, minorlocator, tickminor = _resolve_locators(
            mappable=mappable,
            formatter=formatter,
            formatter_kw=formatter_kw,
            locator=locator,
            locator_kw=locator_kw,
            minorlocator=minorlocator,
            minorlocator_kw=minorlocator_kw,
            tickminor=tickminor,
            vertical=vert,
        )

        # Special handling for colorbar keyword arguments
        # WARNING: Critical to not pass empty major locators in matplotlib < 3.5
        # See this issue: https://github.com/ultraplot-dev/ultraplot/issues/301
        # WARNING: ultraplot 'supports' passing one extend to a mappable function
        # then overwriting by passing another 'extend' to colobar. But contour
        # colorbars break when you try to change its 'extend'. Matplotlib gets
        # around this by just silently ignoring 'extend' passed to colorbar() but
        # we issue warning. Also note ContourSet.extend existed in matplotlib 3.0.
        # WARNING: Confusingly the only default way to have auto-adjusting
        # colorbar ticks is to specify no locator. Then _get_ticker_locator_formatter
        # uses the default ScalarFormatter on the axis that already has a set axis.
        # Otherwise it sets a default axis with locator.create_dummy_axis() in
        # update_ticks() which does not track axis size. Workaround is to manually
        # set the locator and formatter axis... however this messes up colorbar lengths
        # in matplotlib < 3.2. So we only apply this conditionally and in earlier
        # verisons recognize that DiscreteLocator will behave like FixedLocator.
        axis = cax.yaxis if vert else cax.xaxis
        if not isinstance(mappable, mcontour.ContourSet):
            extend = _not_none(extend, "neither")
            kwargs["extend"] = extend
        elif extend is not None and extend != mappable.extend:
            warnings._warn_ultraplot(
                "Ignoring extend={extend!r}. ContourSet extend cannot be changed."
            )
        if (
            isinstance(locator, mticker.NullLocator)
            or hasattr(locator, "locs")
            and len(locator.locs) == 0
        ):
            minorlocator, tickminor = None, False  # attempted fix
        for ticker in (locator, formatter, minorlocator):
            if version.parse(str(_version_mpl)) < version.parse("3.2"):
                pass  # see notes above
            elif isinstance(ticker, mticker.TickHelper):
                ticker.set_axis(axis)

        # Create colorbar and update ticks and axis direction
        # NOTE: This also adds the guides._update_ticks() monkey patch that triggers
        # updates to DiscreteLocator when parent axes is drawn.
        orientation = _not_none(
            kwargs.pop("orientation", None), kwargs.pop("vert", None)
        )

        obj = cax._colorbar_fill = cax.figure.colorbar(
            mappable,
            cax=cax,
            ticks=locator,
            format=formatter,
            drawedges=grid,
            extendfrac=extendfrac,
            orientation=orientation,
            **kwargs,
        )
        outline = _not_none(outline, rc["colorbar.outline"])
        obj.outline.set_visible(outline)
        obj.ax.grid(False)
        # obj.minorlocator = minorlocator  # backwards compatibility
        obj.update_ticks = guides._update_ticks.__get__(obj)  # backwards compatible
        if minorlocator is not None:
            # Note we make use of mpl's setters and getters
            current = obj.minorlocator
            if current != minorlocator:
                obj.minorlocator = minorlocator
            obj.update_ticks()
        elif tickminor:
            obj.minorticks_on()
        else:
            obj.minorticks_off()
        if getattr(norm, "descending", None):
            axis.set_inverted(True)
        if reverse:  # potentially double reverse, although that would be weird...
            axis.set_inverted(True)

        # Update other colorbar settings
        # WARNING: Must use the colorbar set_label to set text. Calling set_label
        # on the actual axis will do nothing!
        if center_levels:
            # Center the ticks to the center of the colorbar
            # rather than showing them on  the edges
            if hasattr(obj.norm, "boundaries"):
                # Only apply to discrete norms
                bounds = obj.norm.boundaries
                centers = 0.5 * (bounds[:-1] + bounds[1:])
                axis.set_ticks(centers)
                ticklenratio = 0
                tickwidthratio = 0
        axis.set_tick_params(which="both", color=color, direction=tickdir)
        axis.set_tick_params(which="major", length=ticklen, width=tickwidth)
        axis.set_tick_params(
            which="minor",
            length=ticklen * ticklenratio,
            width=tickwidth * tickwidthratio,
        )  # noqa: E501

        # Set label and label location
        long_or_short_axis = _get_axis_for(
            labelloc, loc, orientation=orientation, ax=obj
        )
        if labelloc is None:
            labelloc = long_or_short_axis.get_ticks_position()
        long_or_short_axis.set_label_text(label)
        long_or_short_axis.set_label_position(labelloc)

        labelrotation = _not_none(labelrotation, rc["colorbar.labelrotation"])
        # Note kw_label is updated in place
        _determine_label_rotation(
            labelrotation,
            labelloc=labelloc,
            orientation=orientation,
            kw_label=text_kw.kw_label,
        )

        long_or_short_axis.label.update(text_kw.kw_label)
        # Assume ticks are set on the long axis(!))
        if hasattr(obj, "_long_axis"):
            # mpl <=3.9
            longaxis = obj._long_axis()
        else:
            # mpl >=3.10
            longaxis = obj.long_axis
        for label in longaxis.get_ticklabels():
            label.update(text_kw.kw_ticklabels)
        if KIWI_AVAILABLE and getattr(cax, "_inset_colorbar_layout", None):
            _reflow_inset_colorbar_frame(obj, labelloc=labelloc, ticklen=ticklen)
            cax._inset_colorbar_obj = obj
            cax._inset_colorbar_labelloc = labelloc
            cax._inset_colorbar_ticklen = ticklen
            _register_inset_colorbar_reflow(ax.figure)
        kw_outline = {"edgecolor": color, "linewidth": linewidth}
        if obj.outline is not None:
            obj.outline.update(kw_outline)
        if obj.dividers is not None:
            obj.dividers.update(kw_outline)
        if obj.solids:
            from .axes import PlotAxes

            obj.solids.set_rasterized(rasterized)
            PlotAxes._fix_patch_edges(obj.solids, edgefix=edgefix)

        # Register location and return
        ax._register_guide("colorbar", obj, (loc, align))  # possibly replace another
        return obj


def _build_label_tick_kwargs(
    *,
    labelsize: Optional[float],
    labelweight: Optional[str],
    labelcolor: Optional[str],
    ticklabelsize: Optional[float],
    ticklabelweight: Optional[str],
    ticklabelcolor: Optional[str],
    rotation: Optional[float],
) -> _TextKw:
    kw_label: ColorbarLabelKw = {}
    for key, value in (
        ("size", labelsize),
        ("weight", labelweight),
        ("color", labelcolor),
    ):
        if value is not None:
            kw_label[key] = value
    kw_ticklabels: ColorbarTickKw = {}
    for key, value in (
        ("size", ticklabelsize),
        ("weight", ticklabelweight),
        ("color", ticklabelcolor),
        ("rotation", rotation),
    ):
        if value is not None:
            kw_ticklabels[key] = value
    return _TextKw(kw_label=kw_label, kw_ticklabels=kw_ticklabels)


def _resolve_mappable(
    mappable: Any,
    values: Optional[Iterable[float]],
    cax: maxes.Axes,
    kwargs: dict[str, Any],
) -> tuple[mcm.ScalarMappable, dict[str, Any]]:
    if isinstance(mappable, Iterable) and not isinstance(mappable, (str, bytes)):
        mappable_list = list(mappable)
        if len(mappable_list) == 1 and isinstance(mappable_list[0], mcm.ScalarMappable):
            mappable = mappable_list[0]
    if not isinstance(mappable, mcm.ScalarMappable):
        mappable, kwargs = cax._parse_colorbar_arg(mappable, values, **kwargs)
    else:
        pop = _pop_params(kwargs, cax._parse_colorbar_arg, ignore_internal=True)
        if pop:
            warnings._warn_ultraplot(
                f"Input is already a ScalarMappable. "
                f"Ignoring unused keyword arg(s): {pop}"
            )
    return mappable, kwargs


def _resolve_extendfrac(
    *,
    extendsize: Optional[Union[float, str]],
    extendfrac: Optional[float],
    cax: maxes.Axes,
    vertical: bool,
) -> float:
    if extendsize is not None and extendfrac is not None:
        warnings._warn_ultraplot(
            f"You cannot specify both an absolute extendsize={extendsize!r} "
            f"and a relative extendfrac={extendfrac!r}. Ignoring 'extendfrac'."
        )
        extendfrac = None
    if extendfrac is None:
        width, height = cax._get_size_inches()
        scale = height if vertical else width
        extendsize = units(extendsize, "em", "in")
        extendfrac = extendsize / max(scale - 2 * extendsize, units(1, "em", "in"))
    return extendfrac


def _resolve_locators(
    *,
    mappable: mcm.ScalarMappable,
    formatter: Optional[Any],
    formatter_kw: dict[str, Any],
    locator: Optional[Any],
    locator_kw: dict[str, Any],
    minorlocator: Optional[Any],
    minorlocator_kw: dict[str, Any],
    tickminor: Optional[bool],
    vertical: bool,
) -> tuple[mcolors.Normalize, mticker.Formatter, Optional[Any], Optional[Any], bool]:
    norm = mappable.norm
    formatter = _not_none(formatter, getattr(norm, "_labels", None), "auto")
    formatter_kw.setdefault("tickrange", (norm.vmin, norm.vmax))
    formatter = constructor.Formatter(formatter, **formatter_kw)
    categorical = isinstance(formatter, mticker.FixedFormatter)
    if locator is not None:
        locator = constructor.Locator(locator, **locator_kw)
    if minorlocator is not None:  # overrides tickminor
        minorlocator = constructor.Locator(minorlocator, **minorlocator_kw)
    elif tickminor is None:
        tickminor = False if categorical else rc["xy"[vertical] + "tick.minor.visible"]
    if isinstance(norm, mcolors.BoundaryNorm):  # DiscreteNorm or BoundaryNorm
        ticks = getattr(norm, "_ticks", norm.boundaries)
        segmented = isinstance(getattr(norm, "_norm", None), pcolors.SegmentedNorm)
        if locator is None:
            if categorical or segmented:
                locator = mticker.FixedLocator(ticks)
            else:
                locator = pticker.DiscreteLocator(ticks)
        if tickminor and minorlocator is None:
            minorlocator = pticker.DiscreteLocator(ticks, minor=True)
    return norm, formatter, locator, minorlocator, bool(tickminor)


def _get_axis_for(
    labelloc: Optional[str],
    loc: Optional[str],
    *,
    ax: maxes.Axes,
    orientation: Optional[str],
) -> maxes.Axes:
    """
    Helper function to determine the axis for a label.
    Particularly used for colorbars but can be used for other purposes
    """

    def get_short_or_long(which):
        if hasattr(ax, f"{which}_axis"):
            return getattr(ax, f"{which}_axis")
        return getattr(ax, f"_{which}_axis")()

    short = get_short_or_long("short")
    long = get_short_or_long("long")

    label_axis = None
    # For fill or none, we use default locations.
    # This would be the long axis for horizontal orientation
    # and the short axis for vertical orientation.
    if not isinstance(labelloc, str):
        label_axis = long
    # if the orientation is horizontal,
    # the short axis is the y-axis, and the long axis is the
    # x-axis. The inverse holds true for vertical orientation.
    elif "left" in labelloc or "right" in labelloc:
        # Vertical label, use short axis
        label_axis = short if orientation == "horizontal" else long
    elif "top" in labelloc or "bottom" in labelloc:
        label_axis = long if orientation == "horizontal" else short

    if label_axis is None:
        raise ValueError(
            f"Could not determine label axis for {labelloc=}, with {orientation=}."
        )
    return label_axis


def _determine_label_rotation(
    labelrotation: Union[str, Number],
    labelloc: str,
    orientation: str,
    kw_label: MutableMapping,
):
    """
    Note we update kw_label in place.
    """
    if labelrotation == "auto":
        # Automatically determine label rotation based on location, we also align the label to make it look
        # extra nice for 90 degree rotations
        if orientation == "horizontal":
            if labelloc in ["left", "right"]:
                labelrotation = 90 if "left" in labelloc else -90
                kw_label["ha"] = "center"
                kw_label["va"] = "bottom" if "left" in labelloc else "bottom"
            elif labelloc in ["top", "bottom"]:
                labelrotation = 0
                kw_label["ha"] = "center"
                kw_label["va"] = "bottom" if "top" in labelloc else "top"
        elif orientation == "vertical":
            if labelloc in ["left", "right"]:
                labelrotation = 90 if "left" in labelloc else -90
                kw_label["ha"] = "center"
                kw_label["va"] = "bottom" if "left" in labelloc else "bottom"
            elif labelloc in ["top", "bottom"]:
                labelrotation = 0
                kw_label["ha"] = "center"
                kw_label["va"] = "bottom" if "top" in labelloc else "top"

    if not isinstance(labelrotation, (int, float)):
        raise ValueError(
            f"Label rotation must be a number or 'auto', got {labelrotation!r}."
        )
    kw_label.update({"rotation": labelrotation})


def _resolve_label_rotation(
    labelrotation: str | Number,
    *,
    labelloc: str,
    orientation: str,
) -> float:
    layout_rotation = _not_none(labelrotation, 0)
    if layout_rotation == "auto":
        kw_label = {}
        _determine_label_rotation(
            "auto",
            labelloc=labelloc,
            orientation=orientation,
            kw_label=kw_label,
        )
        layout_rotation = kw_label.get("rotation", 0)
    if not isinstance(layout_rotation, (int, float)):
        return 0.0
    return float(layout_rotation)


def _measure_label_points(
    label: str,
    rotation: float,
    fontsize: float,
    figure,
) -> Optional[Tuple[float, float]]:
    try:
        renderer = figure._get_renderer()
        text = mtext.Text(0, 0, label, rotation=rotation, fontsize=fontsize)
        text.set_figure(figure)
        bbox = text.get_window_extent(renderer=renderer)
    except Exception:
        return None
    dpi = figure.dpi
    return (bbox.width * 72 / dpi, bbox.height * 72 / dpi)


def _measure_text_artist_points(
    text: mtext.Text, figure
) -> Optional[Tuple[float, float]]:
    try:
        renderer = figure._get_renderer()
        bbox = text.get_window_extent(renderer=renderer)
    except Exception:
        return None
    dpi = figure.dpi
    return (bbox.width * 72 / dpi, bbox.height * 72 / dpi)


def _measure_ticklabel_extent_points(axis, figure) -> Optional[Tuple[float, float]]:
    try:
        renderer = figure._get_renderer()
        labels = axis.get_ticklabels()
    except Exception:
        return None
    max_width = 0.0
    max_height = 0.0
    for label in labels:
        if not label.get_visible() or not label.get_text():
            continue
        extent = _measure_text_artist_points(label, figure)
        if extent is None:
            continue
        width_pt, height_pt = extent
        max_width = max(max_width, width_pt)
        max_height = max(max_height, height_pt)
    if max_width == 0.0 and max_height == 0.0:
        return None
    return (max_width, max_height)


def _measure_text_overhang_axes(
    text: mtext.Text, axes
) -> Optional[Tuple[float, float, float, float]]:
    try:
        renderer = axes.figure._get_renderer()
        bbox = text.get_window_extent(renderer=renderer)
        inv = axes.transAxes.inverted()
        (x0, y0) = inv.transform((bbox.x0, bbox.y0))
        (x1, y1) = inv.transform((bbox.x1, bbox.y1))
    except Exception:
        return None
    left = max(0.0, -x0)
    right = max(0.0, x1 - 1.0)
    bottom = max(0.0, -y0)
    top = max(0.0, y1 - 1.0)
    return (left, right, bottom, top)


def _measure_ticklabel_overhang_axes(
    axis, axes
) -> Optional[Tuple[float, float, float, float]]:
    try:
        renderer = axes.figure._get_renderer()
        inv = axes.transAxes.inverted()
        labels = axis.get_ticklabels()
    except Exception:
        return None
    min_x, max_x = 0.0, 1.0
    min_y, max_y = 0.0, 1.0
    found = False
    for label in labels:
        if not label.get_visible() or not label.get_text():
            continue
        bbox = label.get_window_extent(renderer=renderer)
        (x0, y0) = inv.transform((bbox.x0, bbox.y0))
        (x1, y1) = inv.transform((bbox.x1, bbox.y1))
        min_x = min(min_x, x0)
        max_x = max(max_x, x1)
        min_y = min(min_y, y0)
        max_y = max(max_y, y1)
        found = True
    if not found:
        return None
    left = max(0.0, -min_x)
    right = max(0.0, max_x - 1.0)
    bottom = max(0.0, -min_y)
    top = max(0.0, max_y - 1.0)
    return (left, right, bottom, top)


def _get_colorbar_long_axis(colorbar: mcolorbar.Colorbar):
    if hasattr(colorbar, "_long_axis"):
        return colorbar._long_axis()
    return colorbar.long_axis


def _register_inset_colorbar_reflow(fig: mfigure.Figure):
    if getattr(fig, "_inset_colorbar_reflow_cid", None) is not None:
        return

    def _on_resize(event):
        axes = list(event.canvas.figure.axes)
        i = 0
        seen = set()
        while i < len(axes):
            ax = axes[i]
            i += 1
            ax_id = id(ax)
            if ax_id in seen:
                continue
            seen.add(ax_id)
            child_axes = getattr(ax, "child_axes", ())
            if child_axes:
                axes.extend(child_axes)
            if getattr(ax, "_inset_colorbar_obj", None) is None:
                continue
            ax._inset_colorbar_needs_reflow = True
        event.canvas.draw_idle()

    fig._inset_colorbar_reflow_cid = fig.canvas.mpl_connect("resize_event", _on_resize)


def _solve_inset_colorbar_bounds(
    *,
    axes: maxes.Axes,
    loc: str,
    orientation: str,
    length: float,
    width: float,
    xpad: float,
    ypad: float,
    ticklocation: str,
    labelloc: Optional[str],
    label: Optional[str],
    labelrotation: Optional[Union[str, float]],
    tick_fontsize: float,
    label_fontsize: float,
) -> Tuple[list[float], list[float]]:
    scale = 1.2
    labelloc_layout = labelloc if isinstance(labelloc, str) else ticklocation
    if orientation == "vertical" and labelloc_layout in ("left", "right"):
        scale = 2

    tick_space_pt = rc["xtick.major.size"] + scale * tick_fontsize
    label_space_pt = 0.0
    if label is not None:
        label_space_pt = scale * label_fontsize
        layout_rotation = _resolve_label_rotation(
            labelrotation, labelloc=labelloc_layout, orientation=orientation
        )
        extent = _measure_label_points(
            str(label), layout_rotation, label_fontsize, axes.figure
        )
        if extent is not None:
            width_pt, height_pt = extent
            if labelloc_layout in ("left", "right"):
                label_space_pt = max(label_space_pt, width_pt)
            else:
                label_space_pt = max(label_space_pt, height_pt)

    fig_w, fig_h = axes._get_size_inches()
    tick_space_x = (
        tick_space_pt / 72 / fig_w if ticklocation in ("left", "right") else 0
    )
    tick_space_y = (
        tick_space_pt / 72 / fig_h if ticklocation in ("top", "bottom") else 0
    )
    label_space_x = (
        label_space_pt / 72 / fig_w if labelloc_layout in ("left", "right") else 0
    )
    label_space_y = (
        label_space_pt / 72 / fig_h if labelloc_layout in ("top", "bottom") else 0
    )

    pad_left = xpad + (tick_space_x if ticklocation == "left" else 0)
    pad_left += label_space_x if labelloc_layout == "left" else 0
    pad_right = xpad + (tick_space_x if ticklocation == "right" else 0)
    pad_right += label_space_x if labelloc_layout == "right" else 0
    pad_bottom = ypad + (tick_space_y if ticklocation == "bottom" else 0)
    pad_bottom += label_space_y if labelloc_layout == "bottom" else 0
    pad_top = ypad + (tick_space_y if ticklocation == "top" else 0)
    pad_top += label_space_y if labelloc_layout == "top" else 0

    if orientation == "horizontal":
        cb_width, cb_height = length, width
    else:
        cb_width, cb_height = width, length
    solver = ColorbarLayoutSolver(
        loc,
        cb_width,
        cb_height,
        pad_left,
        pad_right,
        pad_bottom,
        pad_top,
    )
    layout = solver.solve()
    return list(layout["inset"]), list(layout["frame"])


def _legacy_inset_colorbar_bounds(
    *,
    axes: maxes.Axes,
    loc: str,
    orientation: str,
    length: float,
    width: float,
    xpad: float,
    ypad: float,
    ticklocation: str,
    labelloc: Optional[str],
    label: Optional[str],
    labelrotation: Optional[Union[str, float]],
    tick_fontsize: float,
    label_fontsize: float,
) -> Tuple[list[float], list[float]]:
    labspace = rc["xtick.major.size"] / 72
    scale = 1.2
    if orientation == "vertical" and labelloc in ("left", "right"):
        scale = 2
    if label is not None:
        labspace += 2 * scale * label_fontsize / 72
    else:
        labspace += scale * tick_fontsize / 72

    if orientation == "horizontal":
        labspace /= axes._get_size_inches()[1]
    else:
        labspace /= axes._get_size_inches()[0]

    if orientation == "horizontal":
        frame_width = 2 * xpad + length
        frame_height = 2 * ypad + width + labspace
    else:
        frame_width = 2 * xpad + width + labspace
        frame_height = 2 * ypad + length

    xframe = yframe = 0
    if loc == "upper right":
        xframe = 1 - frame_width
        yframe = 1 - frame_height
        cb_x = xframe + xpad
        cb_y = yframe + ypad
    elif loc == "upper left":
        yframe = 1 - frame_height
        cb_x = xpad
        cb_y = yframe + ypad
    elif loc == "lower left":
        cb_x = xpad
        cb_y = ypad
    else:
        xframe = 1 - frame_width
        cb_x = xframe + xpad
        cb_y = ypad

    label_offset = 0.5 * labspace
    labelrotation = _not_none(labelrotation, 0)
    if labelrotation == "auto":
        kw_label = {}
        _determine_label_rotation(
            "auto",
            labelloc=labelloc or ticklocation,
            orientation=orientation,
            kw_label=kw_label,
        )
        labelrotation = kw_label.get("rotation", 0)
    if not isinstance(labelrotation, (int, float)):
        labelrotation = 0
    if labelrotation != 0 and label is not None:
        import math

        estimated_text_width = len(str(label)) * label_fontsize * 0.6 / 72
        text_height = label_fontsize / 72
        angle_rad = math.radians(abs(labelrotation))
        rotated_width = estimated_text_width * math.cos(
            angle_rad
        ) + text_height * math.sin(angle_rad)
        rotated_height = estimated_text_width * math.sin(
            angle_rad
        ) + text_height * math.cos(angle_rad)

        if orientation == "horizontal":
            rotation_offset = rotated_height / axes._get_size_inches()[1]
        else:
            rotation_offset = rotated_width / axes._get_size_inches()[0]

        label_offset = max(label_offset, rotation_offset)

    if orientation == "vertical":
        if labelloc == "left":
            cb_x += label_offset
        elif labelloc == "top":
            cb_x += label_offset
            if "upper" in loc:
                cb_y -= label_offset
                yframe -= label_offset
                frame_height += label_offset
                frame_width += label_offset
                if "right" in loc:
                    xframe -= label_offset
                    cb_x -= label_offset
            elif "lower" in loc:
                frame_height += label_offset
                frame_width += label_offset
                if "right" in loc:
                    xframe -= label_offset
                    cb_x -= label_offset
        elif labelloc == "bottom":
            if "left" in loc:
                cb_x += label_offset
                frame_width += label_offset
            else:
                xframe -= label_offset
                frame_width += label_offset
            if "lower" in loc:
                cb_y += label_offset
                frame_height += label_offset
            elif "upper" in loc:
                yframe -= label_offset
                frame_height += label_offset
    elif orientation == "horizontal":
        cb_y += 2 * label_offset
        if labelloc == "bottom":
            if "upper" in loc:
                yframe -= label_offset
                frame_height += label_offset
            elif "lower" in loc:
                frame_height += label_offset
                cb_y += 0.5 * label_offset
        elif labelloc == "top":
            if "upper" in loc:
                cb_y -= 1.5 * label_offset
                yframe -= label_offset
                frame_height += label_offset
            elif "lower" in loc:
                frame_height += label_offset
                cb_y -= 0.5 * label_offset

    bounds_inset = [cb_x, cb_y]
    bounds_frame = [xframe, yframe]
    if orientation == "horizontal":
        bounds_inset.extend((length, width))
    else:
        bounds_inset.extend((width, length))
    bounds_frame.extend((frame_width, frame_height))
    return bounds_inset, bounds_frame


def _apply_inset_colorbar_layout(
    axes: maxes.Axes,
    *,
    bounds_inset: list[float],
    bounds_frame: list[float],
    frame: Optional[mpatches.FancyBboxPatch],
):
    parent = getattr(axes, "_inset_colorbar_parent", None)
    transform = parent.transAxes if parent is not None else axes.transAxes
    locator = axes._make_inset_locator(bounds_inset, transform)
    axes.set_axes_locator(locator)
    axes.set_position(locator(axes, None).bounds)
    axes._inset_colorbar_bounds = {
        "inset": bounds_inset,
        "frame": bounds_frame,
    }
    if frame is not None:
        frame.set_bounds(*bounds_frame)


def _reflow_inset_colorbar_frame(
    colorbar: mcolorbar.Colorbar,
    *,
    labelloc: Optional[str],
    ticklen: float,
):
    cax = colorbar.ax
    layout = getattr(cax, "_inset_colorbar_layout", None)
    frame = getattr(cax, "_inset_colorbar_frame", None)
    if not layout:
        return
    parent = getattr(cax, "_inset_colorbar_parent", None)
    if parent is None:
        return
    orientation = layout["orientation"]
    loc = layout["loc"]
    ticklocation = layout["ticklocation"]
    length_raw = layout.get("length_raw")
    width_raw = layout.get("width_raw")
    pad_raw = layout.get("pad_raw")
    if length_raw is None or width_raw is None or pad_raw is None:
        length = layout["length"]
        width = layout["width"]
        xpad = layout["xpad"]
        ypad = layout["ypad"]
    else:
        length = units(length_raw, "em", "ax", axes=parent, width=True)
        width = units(width_raw, "em", "ax", axes=parent, width=False)
        xpad = units(pad_raw, "em", "ax", axes=parent, width=True)
        ypad = units(pad_raw, "em", "ax", axes=parent, width=False)
        layout["length"] = length
        layout["width"] = width
        layout["xpad"] = xpad
        layout["ypad"] = ypad
    labelloc_layout = labelloc if isinstance(labelloc, str) else ticklocation
    if orientation == "horizontal":
        cb_width = length
        cb_height = width
    else:
        cb_width = width
        cb_height = length

    renderer = cax.figure._get_renderer()
    if hasattr(colorbar, "update_ticks"):
        colorbar.update_ticks(manual_only=True)
    bboxes = []
    longaxis = _get_colorbar_long_axis(colorbar)
    try:
        bbox = longaxis.get_tightbbox(renderer)
    except Exception:
        bbox = None
    if bbox is not None:
        bboxes.append(bbox)
    label_axis = _get_axis_for(
        labelloc_layout, loc, orientation=orientation, ax=colorbar
    )
    if label_axis.label.get_text():
        try:
            bboxes.append(label_axis.label.get_window_extent(renderer=renderer))
        except Exception:
            pass
    if colorbar.outline is not None:
        try:
            bboxes.append(colorbar.outline.get_window_extent(renderer=renderer))
        except Exception:
            pass
    if getattr(colorbar, "solids", None) is not None:
        try:
            bboxes.append(colorbar.solids.get_window_extent(renderer=renderer))
        except Exception:
            pass
    if getattr(colorbar, "dividers", None) is not None:
        try:
            bboxes.append(colorbar.dividers.get_window_extent(renderer=renderer))
        except Exception:
            pass
    if not bboxes:
        return
    x0 = min(b.x0 for b in bboxes)
    y0 = min(b.y0 for b in bboxes)
    x1 = max(b.x1 for b in bboxes)
    y1 = max(b.y1 for b in bboxes)
    inv_parent = parent.transAxes.inverted()
    (px0, py0) = inv_parent.transform((x0, y0))
    (px1, py1) = inv_parent.transform((x1, y1))
    cax_bbox = cax.get_window_extent(renderer=renderer)
    (cx0, cy0) = inv_parent.transform((cax_bbox.x0, cax_bbox.y0))
    (cx1, cy1) = inv_parent.transform((cax_bbox.x1, cax_bbox.y1))
    px0, px1 = sorted((px0, px1))
    py0, py1 = sorted((py0, py1))
    cx0, cx1 = sorted((cx0, cx1))
    cy0, cy1 = sorted((cy0, cy1))
    delta_left = max(0.0, cx0 - px0)
    delta_right = max(0.0, px1 - cx1)
    delta_bottom = max(0.0, cy0 - py0)
    delta_top = max(0.0, py1 - cy1)

    pad_left = xpad + delta_left
    pad_right = xpad + delta_right
    pad_bottom = ypad + delta_bottom
    pad_top = ypad + delta_top
    try:
        solver = ColorbarLayoutSolver(
            loc,
            cb_width,
            cb_height,
            pad_left,
            pad_right,
            pad_bottom,
            pad_top,
        )
        bounds = solver.solve()
    except Exception:
        return
    _apply_inset_colorbar_layout(
        cax,
        bounds_inset=list(bounds["inset"]),
        bounds_frame=list(bounds["frame"]),
        frame=frame,
    )
