from typing import Any, Optional, Tuple, Union

import numpy as np
import matplotlib.patches as mpatches
import matplotlib.text as mtext
from matplotlib import legend as mlegend
from matplotlib import legend_handler as mhandler
from matplotlib import lines as mlines

from .config import rc
from .internals import _not_none, _pop_props, guides, rcsetup
from .utils import _fontsize_to_pt, units

try:
    from typing import override
except ImportError:
    from typing_extensions import override

__all__ = ["Legend", "LegendEntry"]


def _wedge_legend_patch(
    legend,
    orig_handle,
    xdescent,
    ydescent,
    width,
    height,
    fontsize,
):
    """
    Draw wedge-shaped legend keys for pie wedge handles.
    """
    center = (-xdescent + width * 0.5, -ydescent + height * 0.5)
    radius = 0.5 * min(width, height)
    theta1 = float(getattr(orig_handle, "theta1", 0.0))
    theta2 = float(getattr(orig_handle, "theta2", 300.0))
    if theta2 == theta1:
        theta2 = theta1 + 300.0
    return mpatches.Wedge(center, radius, theta1=theta1, theta2=theta2)


class LegendEntry(mlines.Line2D):
    """
    Convenience artist for custom legend entries.

    This is a lightweight wrapper around `matplotlib.lines.Line2D` that
    initializes with empty data so it can be passed directly to
    `Axes.legend()` or `Figure.legend()` handles.
    """

    def __init__(
        self,
        label=None,
        *,
        color=None,
        line=True,
        marker=None,
        linestyle="-",
        linewidth=2,
        markersize=6,
        markerfacecolor=None,
        markeredgecolor=None,
        markeredgewidth=None,
        alpha=None,
        **kwargs,
    ):
        marker = "o" if marker is None and not line else marker
        linestyle = "none" if not line else linestyle
        if markerfacecolor is None and color is not None:
            markerfacecolor = color
        if markeredgecolor is None and color is not None:
            markeredgecolor = color
        super().__init__(
            [],
            [],
            label=label,
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=linewidth,
            markersize=markersize,
            markerfacecolor=markerfacecolor,
            markeredgecolor=markeredgecolor,
            markeredgewidth=markeredgewidth,
            alpha=alpha,
            **kwargs,
        )

    @classmethod
    def line(cls, label=None, **kwargs):
        """
        Build a line-style legend entry.
        """
        return cls(label=label, line=True, **kwargs)

    @classmethod
    def marker(cls, label=None, marker="o", **kwargs):
        """
        Build a marker-style legend entry.
        """
        return cls(label=label, line=False, marker=marker, **kwargs)


ALIGN_OPTS = {
    None: {
        "center": "center",
        "left": "center left",
        "right": "center right",
        "top": "upper center",
        "bottom": "lower center",
    },
    "left": {
        "center": "center right",
        "left": "center right",
        "right": "center right",
        "top": "upper right",
        "bottom": "lower right",
    },
    "right": {
        "center": "center left",
        "left": "center left",
        "right": "center left",
        "top": "upper left",
        "bottom": "lower left",
    },
    "top": {
        "center": "lower center",
        "left": "lower left",
        "right": "lower right",
        "top": "lower center",
        "bottom": "lower center",
    },
    "bottom": {
        "center": "upper center",
        "left": "upper left",
        "right": "upper right",
        "top": "upper center",
        "bottom": "upper center",
    },
}


class Legend(mlegend.Legend):
    # Soft wrapper of matplotlib legend's class.
    # Currently we only override the syncing of the location.
    # The user may change the location and the legend_dict should
    # be updated accordingly. This caused an issue where
    # a legend format was not behaving according to the docs
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get_default_handler_map(cls):
        """
        Extend matplotlib defaults with a wedge handler for pie legends.
        """
        handler_map = dict(super().get_default_handler_map())
        handler_map.setdefault(
            mpatches.Wedge,
            mhandler.HandlerPatch(patch_func=_wedge_legend_patch),
        )
        return handler_map

    @override
    def set_loc(self, loc=None):
        # Sync location setting with the move
        old_loc = None
        if self.axes is not None:
            # Get old location which is a tuple of location and
            # legend type
            for k, v in self.axes._legend_dict.items():
                if v is self:
                    old_loc = k
                    break
        super().set_loc(loc)
        if old_loc is not None:
            value = self.axes._legend_dict.pop(old_loc, None)
            where, type = old_loc
            self.axes._legend_dict[(loc, type)] = value


class UltraLegend:
    """
    Centralized legend builder for axes.
    """

    def __init__(self, axes):
        self.axes = axes

    def add(
        self,
        handles=None,
        labels=None,
        *,
        loc=None,
        align=None,
        width=None,
        pad=None,
        space=None,
        frame=None,
        frameon=None,
        ncol=None,
        ncols=None,
        alphabetize=False,
        center=None,
        order=None,
        label=None,
        title=None,
        fontsize=None,
        fontweight=None,
        fontcolor=None,
        titlefontsize=None,
        titlefontweight=None,
        titlefontcolor=None,
        handle_kw=None,
        handler_map=None,
        span: Optional[Union[int, Tuple[int, int]]] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        rows: Optional[Union[int, Tuple[int, int]]] = None,
        cols: Optional[Union[int, Tuple[int, int]]] = None,
        **kwargs,
    ):
        """
        The driver function for adding axes legends.
        """
        ax = self.axes
        # Parse input argument units
        ncol = _not_none(ncols=ncols, ncol=ncol)
        order = _not_none(order, "C")
        frameon = _not_none(frame=frame, frameon=frameon, default=rc["legend.frameon"])
        fontsize = _not_none(fontsize, rc["legend.fontsize"])
        titlefontsize = _not_none(
            title_fontsize=kwargs.pop("title_fontsize", None),
            titlefontsize=titlefontsize,
            default=rc["legend.title_fontsize"],
        )
        fontsize = _fontsize_to_pt(fontsize)
        titlefontsize = _fontsize_to_pt(titlefontsize)
        if order not in ("F", "C"):
            raise ValueError(
                f"Invalid order {order!r}. Please choose from "
                "'C' (row-major, default) or 'F' (column-major)."
            )

        # Convert relevant keys to em-widths
        for setting in rcsetup.EM_KEYS:  # em-width keys
            pair = setting.split("legend.", 1)
            if len(pair) == 1:
                continue
            _, key = pair
            value = kwargs.pop(key, None)
            if isinstance(value, str):
                value = units(value, "em", fontsize=fontsize)
            if value is not None:
                kwargs[key] = value

        # Generate and prepare the legend axes
        if loc in ("fill", "left", "right", "top", "bottom"):
            lax = ax._add_guide_panel(
                loc,
                align,
                width=width,
                space=space,
                pad=pad,
                span=span,
                row=row,
                col=col,
                rows=rows,
                cols=cols,
            )
            kwargs.setdefault("borderaxespad", 0)
            if not frameon:
                kwargs.setdefault("borderpad", 0)
            try:
                kwargs["loc"] = ALIGN_OPTS[lax._panel_side][align]
            except KeyError as exc:
                raise ValueError(
                    f"Invalid align={align!r} for legend loc={loc!r}."
                ) from exc
        else:
            lax = ax
            pad = kwargs.pop("borderaxespad", pad)
            kwargs["loc"] = loc  # simply pass to legend
            kwargs["borderaxespad"] = units(pad, "em", fontsize=fontsize)

        # Handle and text properties that are applied after-the-fact
        # NOTE: Set solid_capstyle to 'butt' so line does not extend past error bounds
        # shading in legend entry. This change is not noticable in other situations.
        kw_frame, kwargs = lax._parse_frame("legend", **kwargs)
        kw_text = {}
        if fontcolor is not None:
            kw_text["color"] = fontcolor
        if fontweight is not None:
            kw_text["weight"] = fontweight
        kw_title = {}
        if titlefontcolor is not None:
            kw_title["color"] = titlefontcolor
        if titlefontweight is not None:
            kw_title["weight"] = titlefontweight
        kw_handle = _pop_props(kwargs, "line")
        kw_handle.setdefault("solid_capstyle", "butt")
        kw_handle.update(handle_kw or {})

        # Parse the legend arguments using axes for auto-handle detection
        # TODO: Update this when we no longer use "filled panels" for outer legends
        pairs, multi = lax._parse_legend_handles(
            handles,
            labels,
            ncol=ncol,
            order=order,
            center=center,
            alphabetize=alphabetize,
            handler_map=handler_map,
        )
        title = _not_none(label=label, title=title)
        kwargs.update(
            {
                "title": title,
                "frameon": frameon,
                "fontsize": fontsize,
                "handler_map": handler_map,
                "title_fontsize": titlefontsize,
            }
        )

        # Add the legend and update patch properties
        # TODO: Add capacity for categorical labels in a single legend like seaborn
        # rather than manual handle overrides with multiple legends.
        if multi:
            objs = lax._parse_legend_centered(pairs, kw_frame=kw_frame, **kwargs)
        else:
            kwargs.update({key: kw_frame.pop(key) for key in ("shadow", "fancybox")})
            objs = [lax._parse_legend_aligned(pairs, ncol=ncol, order=order, **kwargs)]
            objs[0].legendPatch.update(kw_frame)
        for obj in objs:
            if hasattr(lax, "legend_") and lax.legend_ is None:
                lax.legend_ = obj  # make first legend accessible with get_legend()
            else:
                lax.add_artist(obj)

        # Update legend patch and elements
        # WARNING: legendHandles only contains the *first* artist per legend because
        # HandlerBase.legend_artist() called in Legend._init_legend_box() only
        # returns the first artist. Instead we try to iterate through offset boxes.
        for obj in objs:
            obj.set_clip_on(False)  # needed for tight bounding box calculations
            box = getattr(obj, "_legend_handle_box", None)
            for child in guides._iter_children(box):
                if isinstance(child, mtext.Text):
                    kw = kw_text
                else:
                    kw = {
                        key: val
                        for key, val in kw_handle.items()
                        if hasattr(child, "set_" + key)
                    }
                    if hasattr(child, "set_sizes") and "markersize" in kw_handle:
                        kw["sizes"] = np.atleast_1d(kw_handle["markersize"])
                child.update(kw)

        # Register location and return
        if isinstance(objs[0], mpatches.FancyBboxPatch):
            objs = objs[1:]
        obj = objs[0] if len(objs) == 1 else tuple(objs)
        ax._register_guide("legend", obj, (loc, align))  # possibly replace another

        return obj
