from matplotlib import lines as mlines
from matplotlib import legend as mlegend
from matplotlib import legend_handler as mhandler
from matplotlib import patches as mpatches

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
