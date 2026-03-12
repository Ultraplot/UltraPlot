#!/usr/bin/env python3
"""
Layout query helpers used by Figure.
"""

import matplotlib.axes as maxes
import numpy as np

from .. import axes as paxes
from . import _not_none, context
from ..utils import _Crawler, _get_subplot_layout


class FigureLayout:
    """
    Geometry and renderer helpers for figure-level layout operations.
    """

    def __init__(self, figure):
        self.figure = figure

    def get_align_axes(self, side):
        """
        Return the main axes along the edge of the figure.

        For 'left'/'right': select one extreme axis per row (leftmost/rightmost).
        For 'top'/'bottom': select one extreme axis per column (topmost/bottommost).
        """
        figure = self.figure
        axs = tuple(figure._subplot_dict.values())
        if not axs:
            return []
        if side not in ("left", "right", "top", "bottom"):
            raise ValueError(f"Invalid side {side!r}.")

        grid = _get_subplot_layout(
            figure._gridspec, list(figure._iter_axes(panels=False, hidden=False))
        )[0]
        if side == "left":
            options = grid
        elif side == "right":
            options = grid[:, ::-1]
        elif side == "top":
            options = grid.T
        else:  # bottom
            options = grid.T[:, ::-1]

        numbers = set()
        for option in options:
            idx = np.flatnonzero([item is not None for item in option])
            if idx.size > 0:
                numbers.add(option[idx.min()].number)

        axs = []
        for axi in figure._iter_axes():
            if axi.number in numbers and axi not in axs:
                axs.append(axi)
        return axs

    def get_border_axes(
        self, *, same_type=False, force_recalculate=False
    ) -> dict[str, list[paxes.Axes]]:
        """
        Identify axes located on the outer boundaries of the GridSpec layout.
        """
        figure = self.figure
        cached = getattr(figure, "_cached_border_axes", None)
        if not isinstance(cached, dict) or not all(
            isinstance(key, bool) for key in cached
        ):
            cached = {}
        if not force_recalculate and same_type in cached:
            return cached[same_type]

        border_axes = dict(
            left=[],
            right=[],
            top=[],
            bottom=[],
        )
        gs = figure.gridspec
        if gs is None:
            return border_axes

        all_axes = list(figure._iter_axes(panels=True))

        nrows, ncols = gs.nrows, gs.ncols
        if nrows == 0 or ncols == 0 or not all_axes:
            return border_axes

        gs = figure.axes[0].get_gridspec()
        shape = (gs.nrows_total, gs.ncols_total)
        grid = np.zeros(shape, dtype=object)
        grid.fill(None)
        grid_axis_type = np.zeros(shape, dtype=int)
        seen_axis_type = {}
        ax_type_mapping = {}

        for axi in figure._iter_axes(panels=True, hidden=True):
            gs = axi.get_subplotspec()
            x, y = np.unravel_index(gs.num1, shape)
            xleft, xright, yleft, yright = gs._get_rows_columns()
            xspan = xright - xleft + 1
            yspan = yright - yleft + 1
            axis_type = getattr(axi, "_ultraplot_axis_type", None)
            if axis_type is None:
                axis_type = type(axi)
                if isinstance(axi, paxes.GeoAxes):
                    axis_type = axi.projection
            if same_type:
                type_number = 1
            else:
                if axis_type not in seen_axis_type:
                    seen_axis_type[axis_type] = len(seen_axis_type)
                type_number = seen_axis_type[axis_type]
            ax_type_mapping[axi] = type_number
            if axi.get_visible():
                grid[x : x + xspan, y : y + yspan] = axi
            grid_axis_type[x : x + xspan, y : y + yspan] = type_number

        for axi in all_axes:
            axis_type = ax_type_mapping[axi]
            number = axi.number
            if number is None:
                number = -axi._panel_parent.number
            crawler = _Crawler(
                ax=axi,
                grid=grid,
                target=number,
                axis_type=axis_type,
                grid_axis_type=grid_axis_type,
            )
            for direction, is_border in crawler.find_edges():
                if is_border and axi not in border_axes[direction]:
                    border_axes[direction].append(axi)

        cached[same_type] = border_axes
        figure._cached_border_axes = cached
        return border_axes

    def get_align_coord(self, side, axs, align="center", includepanels=False):
        """
        Return the figure coordinate for spanning labels or super titles.
        """
        figure = self.figure
        if not all(isinstance(ax, paxes.Axes) for ax in axs):
            raise RuntimeError("Axes must be ultraplot axes.")
        if not all(isinstance(ax, maxes.SubplotBase) for ax in axs):
            raise RuntimeError("Axes must be subplots.")

        axis_name = "y" if side in ("left", "right") else "x"
        axs = [ax._panel_parent or ax for ax in axs]
        if includepanels:
            axs = [_ for ax in axs for _ in ax._iter_axes(panels=True, children=False)]
        ranges = np.array([ax._range_subplotspec(axis_name) for ax in axs])
        min_, max_ = ranges[:, 0].min(), ranges[:, 1].max()
        ax_lo = axs[np.where(ranges[:, 0] == min_)[0][0]]
        ax_hi = axs[np.where(ranges[:, 1] == max_)[0][0]]
        box_lo = ax_lo.get_subplotspec().get_position(figure)
        box_hi = ax_hi.get_subplotspec().get_position(figure)
        if axis_name == "x":
            if align == "left":
                pos = box_lo.x0
            elif align == "right":
                pos = box_hi.x1
            else:
                pos = 0.5 * (box_lo.x0 + box_hi.x1)
        else:
            pos = 0.5 * (box_lo.y1 + box_hi.y0)
        ax = axs[(np.argmin(ranges[:, 0]) + np.argmax(ranges[:, 1])) // 2]
        ax = ax._panel_parent or ax
        return pos, ax

    def get_offset_coord(self, side, axs, renderer, *, pad=None, extra=None):
        """
        Return the figure coordinate for offsetting super labels and super titles.
        """
        figure = self.figure
        axis_name = "x" if side in ("left", "right") else "y"
        coords = []
        objs = tuple(
            _
            for ax in axs
            for _ in ax._iter_axes(panels=True, children=True, hidden=True)
        )
        objs = objs + (extra or ())
        for obj in objs:
            bbox = obj.get_tightbbox(renderer)
            attr = axis_name + ("max" if side in ("top", "right") else "min")
            coord = getattr(bbox, attr)
            coord = (coord, 0) if side in ("left", "right") else (0, coord)
            coord = figure.transFigure.inverted().transform(coord)
            coord = coord[0] if side in ("left", "right") else coord[1]
            coords.append(coord)
        width, height = figure.get_size_inches()
        if pad is None:
            pad = figure._suplabel_pad[side] / 72
            pad = pad / width if side in ("left", "right") else pad / height
        return min(coords) - pad if side in ("left", "bottom") else max(coords) + pad

    def get_renderer(self):
        """
        Get a renderer at all costs. See Matplotlib's tight_layout.py.
        """
        figure = self.figure
        renderer = getattr(figure, "_cachedRenderer", None)
        if renderer is not None:
            return renderer

        canvas = figure.canvas
        if canvas and hasattr(canvas, "get_renderer"):
            return canvas.get_renderer()

        from matplotlib.backends.backend_agg import FigureCanvasAgg

        canvas = FigureCanvasAgg(figure)
        return canvas.get_renderer()

    def is_same_size(self, figsize, eps=None):
        """
        Test if the figure size is unchanged up to some tolerance in inches.
        """
        figure = self.figure
        eps = _not_none(eps, 0.01)
        figsize_active = figure.get_size_inches()
        if figsize is None:
            return True
        return np.all(np.isclose(figsize, figsize_active, rtol=0, atol=eps))

    def set_size_inches(self, w, h=None, *, forward=True, internal=False, eps=None):
        """
        Set the figure size while preserving UltraPlot layout state.
        """
        figure = self.figure
        figsize = w if h is None else (w, h)
        if not np.all(np.isfinite(figsize)):
            raise ValueError(f"Figure size must be finite, not {figsize}.")

        attrs = ("_is_idle_drawing", "_is_drawing", "_draw_pending")
        backend = any(getattr(figure.canvas, attr, None) for attr in attrs)
        internal = internal or figure._is_adjusting
        samesize = self.is_same_size(figsize, eps)
        ctx = context._empty_context()
        if not backend and not internal and not samesize:
            ctx = figure._context_adjusting()
            figure._figwidth, figure._figheight = figsize
            figure._refwidth = figure._refheight = None

        with ctx:
            super(type(figure), figure).set_size_inches(figsize, forward=forward)
        if not samesize:
            figure.gridspec.update()
            if not backend and not internal:
                figure._layout_dirty = True

    def iter_axes(self, hidden=False, children=False, panels=True):
        """
        Iterate over UltraPlot axes and selected panels in the figure.
        """
        figure = self.figure
        if panels is False:
            panels = ()
        elif panels is True or panels is None:
            panels = ("left", "right", "bottom", "top")
        elif isinstance(panels, str):
            panels = (panels,)
        if not set(panels) <= {"left", "right", "bottom", "top"}:
            raise ValueError(f"Invalid sides {panels!r}.")
        axs = (
            *figure._subplot_dict.values(),
            *(ax for side in panels for ax in figure._panel_dict[side]),
        )
        for ax in axs:
            if not hidden and ax._panel_hidden:
                continue
            yield from ax._iter_axes(hidden=hidden, children=children, panels=panels)
