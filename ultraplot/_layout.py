"""
Private helpers for reducing repeated layout work.

The objects in this module are deliberately scoped to a single canvas draw.
They do not change matplotlib's persistent axis state or public API.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

import matplotlib.transforms as mtransforms
import numpy as np

_MISSING = object()


def _is_internal_ticker(obj):
    """Return whether a locator or formatter is safe for draw-local reuse."""
    module = type(obj).__module__
    return (
        module == "matplotlib"
        or module.startswith("matplotlib.")
        or module == "ultraplot.ticker"
    )


def _interval_key(values):
    """Convert a numerical interval to an immutable exact cache key."""
    return tuple(np.asarray(values).reshape(-1).tolist())


@dataclass(frozen=True)
class _AxisTickState:
    """State that can affect ``Axis._update_ticks`` within one canvas draw."""

    view_interval: tuple
    data_interval: tuple
    axes_size: tuple
    dpi: float
    scale: str
    major_locator: int
    major_formatter: int
    minor_locator: int
    minor_formatter: int
    converter: int
    units: int


@dataclass
class _AxisTickResult:
    """Cached ticks and formatter locations for one axis state."""

    ticks: list
    major_locs: np.ndarray | tuple
    minor_locs: np.ndarray | tuple


class _AxisTickCache:
    """
    Cache repeated tick updates during one layout-and-render transaction.

    Tight bounding-box calculation and the final axes draw repeatedly call
    ``Axis._update_ticks`` with identical state. The method runs locators,
    formatters, tick positioning, and visibility filtering each time. This
    manager replaces the method on individual axes for the duration of a
    canvas draw and restores the original instance state afterwards.

    Custom third-party locators and formatters conservatively bypass the
    cache because they may rely on repeated side effects.
    """

    _MAX_STATES_PER_AXIS = 4

    def __init__(self, figure):
        self.figure = figure
        self._cache = {}
        self._patched = {}
        self.hits = 0
        self.misses = 0
        self.bypasses = 0
        self.evictions = 0

    def __enter__(self):
        self.figure._axis_tick_cache = self
        self.refresh()
        return self

    def __exit__(self, *args):
        for axis, previous in self._patched.items():
            if previous is _MISSING:
                axis.__dict__.pop("_update_ticks", None)
            else:
                axis.__dict__["_update_ticks"] = previous
        self._patched.clear()
        self.figure.__dict__.pop("_axis_tick_cache", None)
        self.figure._last_axis_tick_cache_stats = {
            "hits": self.hits,
            "misses": self.misses,
            "bypasses": self.bypasses,
            "evictions": self.evictions,
        }

    def refresh(self):
        """Patch axes added while queued guides and panels are materialized."""
        for axes in self.figure.axes:
            axis_map = getattr(axes, "_axis_map", {})
            for axis in axis_map.values():
                if axis is not None and axis not in self._patched:
                    self._patch(axis)

    def _patch(self, axis):
        previous = axis.__dict__.get("_update_ticks", _MISSING)
        original = axis._update_ticks
        self._patched[axis] = previous

        def _cached_update_ticks():
            if not self._is_cacheable(axis):
                self.bypasses += 1
                return original()
            state = self._get_state(axis)
            states = self._cache.setdefault(axis, OrderedDict())
            result = states.pop(state, None)
            if result is not None:
                self.hits += 1
                states[state] = result
                self._restore_formatter_locs(axis, result)
                return result.ticks
            self.misses += 1
            ticks = original()
            result = _AxisTickResult(
                ticks=ticks,
                major_locs=self._copy_formatter_locs(axis.major.formatter),
                minor_locs=self._copy_formatter_locs(axis.minor.formatter),
            )
            states[state] = result
            if len(states) > self._MAX_STATES_PER_AXIS:
                states.popitem(last=False)
                self.evictions += 1
            return ticks

        axis._update_ticks = _cached_update_ticks

    @staticmethod
    def _is_cacheable(axis):
        if getattr(axis.axes, "_name", None) != "cartesian":
            return False
        ticker_objects = (
            axis.major.locator,
            axis.major.formatter,
            axis.minor.locator,
            axis.minor.formatter,
        )
        return all(_is_internal_ticker(obj) for obj in ticker_objects)

    @staticmethod
    def _get_state(axis):
        axes = axis.axes
        figure = axes.get_figure(root=True)
        get_converter = getattr(axis, "get_converter", None)
        converter = get_converter() if get_converter is not None else None
        get_units = getattr(axis, "get_units", None)
        units = get_units() if get_units is not None else None
        return _AxisTickState(
            view_interval=_interval_key(axis.get_view_interval()),
            data_interval=_interval_key(axis.get_data_interval()),
            axes_size=(axes.bbox.width, axes.bbox.height),
            dpi=float(figure.dpi),
            scale=axis.get_scale(),
            major_locator=id(axis.major.locator),
            major_formatter=id(axis.major.formatter),
            minor_locator=id(axis.minor.locator),
            minor_formatter=id(axis.minor.formatter),
            converter=id(converter),
            units=id(units),
        )

    @staticmethod
    def _copy_formatter_locs(formatter):
        locs = getattr(formatter, "locs", ())
        try:
            return np.array(locs, copy=True)
        except Exception:
            return tuple(locs)

    @staticmethod
    def _restore_formatter_locs(axis, result):
        for formatter, locs in (
            (axis.major.formatter, result.major_locs),
            (axis.minor.formatter, result.minor_locs),
        ):
            setter = getattr(formatter, "set_locs", None)
            if setter is not None:
                setter(locs)


@dataclass(frozen=True)
class _AxesExtentState:
    """Geometry that can alter outsets relative to an axes rectangle."""

    bbox_size: tuple
    bbox_position: tuple
    dpi: float
    axis_states: tuple
    decorations: tuple
    subset_titles: tuple


@dataclass
class _AxesExtentRecord:
    """One relative tight-bbox measurement."""

    version: int
    state: _AxesExtentState
    outsets: tuple


class _ExtentReductionTree:
    """Small mutable min/max tree for the union of axes extents."""

    def __init__(self, axes):
        self.axes = tuple(axes)
        self._indices = {axis: index for index, axis in enumerate(self.axes)}
        capacity = 1
        while capacity < max(1, len(self.axes)):
            capacity *= 2
        self._capacity = capacity
        self._values = np.empty((2 * capacity, 4), dtype=float)
        self.clear()

    def clear(self):
        self._values[:, :2] = np.inf
        self._values[:, 2:] = -np.inf

    def update(self, axis, bbox):
        index = self._indices.get(axis)
        if index is None:
            return
        node = self._capacity + index
        if bbox is None:
            self._values[node] = (np.inf, np.inf, -np.inf, -np.inf)
        else:
            self._values[node] = (bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax)
        node //= 2
        while node:
            left = self._values[2 * node]
            right = self._values[2 * node + 1]
            self._values[node, :2] = np.minimum(left[:2], right[:2])
            self._values[node, 2:] = np.maximum(left[2:], right[2:])
            node //= 2

    def get_bbox(self):
        xmin, ymin, xmax, ymax = self._values[1]
        if not np.all(np.isfinite((xmin, ymin, xmax, ymax))):
            return None
        return mtransforms.Bbox.from_extents(xmin, ymin, xmax, ymax)


class _LayoutExtentStore:
    """
    Persist relative axes outsets and dependency versions between layouts.

    Absolute axes positions are solver outputs. Tick labels, axis labels, and
    titles are better represented as four overhangs around those positions.
    Standard Cartesian axes can therefore move without repeating renderer text
    measurements. Position-sensitive axes and extra artists automatically add
    the absolute origin to their state key.
    """

    def __init__(self, figure):
        self.figure = figure
        self._records = {}
        self._versions = {}
        self._tree = None
        self._topology = {}
        self._active = False
        self.hits = 0
        self.misses = 0

    def __enter__(self):
        self._active = True
        self.hits = 0
        self.misses = 0
        axes = self.refresh()
        for axis in axes:
            if axis.stale:
                self._versions[axis] += 1
        return self

    def refresh(self):
        """Synchronize axes added by queued guide and panel creation."""
        axes = tuple(self.figure.axes)
        if self._tree is None or self._tree.axes != axes:
            self._tree = _ExtentReductionTree(axes)
            self._topology.clear()
            current = set(axes)
            self._records = {
                key: value for key, value in self._records.items() if key[0] in current
            }
            self._versions = {
                axis: version
                for axis, version in self._versions.items()
                if axis in current
            }
        for axis in axes:
            if axis not in self._versions:
                self._versions[axis] = 1
        return axes

    def __exit__(self, *args):
        self._rebase_records()
        self._active = False
        self.figure._last_layout_extent_stats = {
            "hits": self.hits,
            "misses": self.misses,
        }

    def get_tightbbox(
        self,
        axes,
        renderer,
        *,
        include_subset_titles=True,
        use_cache=True,
    ):
        """Return an exact or reconstructed tight bbox in display units."""
        if not self._active or not use_cache or not self._is_cacheable_axes(axes):
            bbox = self._measure_tightbbox(axes, renderer, include_subset_titles)
            self.update_union(axes, bbox)
            return bbox

        version = self._versions.setdefault(axes, 1)
        state = self._get_state(axes, include_subset_titles)
        cache_key = (axes, bool(include_subset_titles))
        record = self._records.get(cache_key)
        if record is not None and record.version == version and record.state == state:
            self.hits += 1
            bbox = self._bbox_from_outsets(axes.bbox, record.outsets)
            axes._tight_bbox = bbox
        else:
            self.misses += 1
            bbox = self._measure_tightbbox(axes, renderer, include_subset_titles)
            if bbox is not None:
                self._records[cache_key] = _AxesExtentRecord(
                    version=version,
                    state=self._get_state(axes, include_subset_titles),
                    outsets=self._get_outsets(axes.bbox, bbox),
                )
        self.update_union(axes, bbox)
        return bbox

    def clear_union(self):
        if self._tree is not None:
            self._tree.clear()

    def update_union(self, axes, bbox):
        if self._tree is not None:
            self._tree.update(axes, bbox)

    def get_union(self):
        return None if self._tree is None else self._tree.get_bbox()

    def get_subplot_ranges(self, axes, along, across):
        """Return compact topology arrays used by boundary reductions."""
        key = (tuple(axes), along, across)
        cached = self._topology.get(key)
        if cached is not None:
            return cached
        along_ranges = np.asarray(
            [axis._range_subplotspec(along) for axis in axes], dtype=int
        )
        across_ranges = np.asarray(
            [axis._range_subplotspec(across) for axis in axes], dtype=int
        )
        result = (along_ranges, across_ranges)
        self._topology[key] = result
        return result

    def invalidate_topology(self):
        """Discard structural row/column range lookups."""
        self._topology.clear()

    def _get_state(self, axes, include_subset_titles=True):
        bbox = axes.bbox
        position_sensitive = self._is_position_sensitive(axes)
        axis_states = []
        for axis in getattr(axes, "_axis_map", {}).values():
            if axis is None:
                continue
            get_converter = getattr(axis, "get_converter", None)
            converter = get_converter() if get_converter is not None else None
            get_units = getattr(axis, "get_units", None)
            units = get_units() if get_units is not None else None
            axis_states.append(
                (
                    _interval_key(axis.get_view_interval()),
                    _interval_key(axis.get_data_interval()),
                    axis.get_scale(),
                    id(axis.major.locator),
                    id(axis.major.formatter),
                    id(axis.minor.locator),
                    id(axis.minor.formatter),
                    id(converter),
                    id(units),
                    _interval_key(getattr(axis.major.formatter, "locs", ())),
                    _interval_key(getattr(axis.minor.formatter, "locs", ())),
                )
            )
        return _AxesExtentState(
            bbox_size=(bbox.width, bbox.height),
            bbox_position=(bbox.x0, bbox.y0) if position_sensitive else (),
            dpi=float(axes.get_figure(root=True).dpi),
            axis_states=tuple(axis_states),
            decorations=self._get_decoration_state(axes),
            subset_titles=self._get_subset_title_state(axes, include_subset_titles),
        )

    def _rebase_records(self):
        """
        Rebase reusable outsets onto final post-render axes dimensions.

        UltraLayout may make a small solver adjustment after measuring an axes.
        The final render updates locator/formatter locations for that geometry.
        If those locations and every non-size dependency are unchanged, the
        relative outsets remain valid for the next layout transaction.
        """
        for (axes, include_subset_titles), record in self._records.items():
            if axes not in self._versions:
                continue
            if record.version != self._versions[axes]:
                continue
            if self._is_position_sensitive(axes):
                continue
            state = self._get_state(axes, include_subset_titles)
            if (
                record.state.dpi == state.dpi
                and record.state.axis_states == state.axis_states
                and record.state.decorations == state.decorations
                and record.state.subset_titles == state.subset_titles
            ):
                record.state = state

    @staticmethod
    def _get_decoration_state(axes):
        texts = []
        core_texts = (
            getattr(axes, "title", None),
            getattr(axes, "_left_title", None),
            getattr(axes, "_right_title", None),
            getattr(getattr(axes, "xaxis", None), "label", None),
            getattr(getattr(axes, "yaxis", None), "label", None),
        )
        extra_texts = tuple(
            text for text in getattr(axes, "texts", ()) if text.get_text()
        )
        for text in (*core_texts, *extra_texts):
            if text is None:
                continue
            texts.append(
                (
                    id(text),
                    text.get_visible(),
                    text.get_in_layout(),
                    text.get_text(),
                    text.get_rotation(),
                    hash(text.get_fontproperties()),
                )
            )
        legend = getattr(axes, "legend_", None)
        if legend is None:
            legend_state = ()
        else:
            legend_state = (
                id(legend),
                legend.get_visible(),
                legend.get_in_layout(),
                id(getattr(legend, "_bbox_to_anchor", None)),
                tuple(text.get_text() for text in legend.get_texts()),
            )
        extra_ids = tuple(
            id(artist)
            for artists in (
                getattr(axes, "artists", ()),
                getattr(axes, "tables", ()),
            )
            for artist in artists
            if artist.get_visible() and artist.get_in_layout()
        )
        return tuple(texts), legend_state, extra_ids

    def _get_subset_title_state(self, axes, include_subset_titles):
        if not include_subset_titles:
            return ()
        figure = axes.get_figure(root=True)
        groups = getattr(figure, "_subset_title_dict", {})
        state = []
        parent = getattr(axes, "_panel_parent", None) or axes
        for group in groups.values():
            group_axes = tuple(
                getattr(item, "_panel_parent", None) or item
                for item in group["axes"]
                if item is not None and item.figure is figure
            )
            if parent not in group_axes:
                continue
            artist = group["artist"]
            state.append(
                (
                    tuple(id(item) for item in group_axes),
                    artist.get_visible(),
                    artist.get_text(),
                    artist.get_position(),
                    artist.get_ha(),
                    artist.get_va(),
                    artist.get_rotation(),
                    hash(artist.get_fontproperties()),
                    group.get("pad"),
                    group.get("y"),
                )
            )
        return tuple(state)

    @staticmethod
    def _is_position_sensitive(axes):
        if getattr(axes, "_name", None) != "cartesian":
            return True
        legend = getattr(axes, "legend_", None)
        if legend is not None and getattr(legend, "_bbox_to_anchor", None) is not None:
            return True
        collections = (
            getattr(axes, "artists", ()),
            getattr(axes, "tables", ()),
        )
        if any(
            artist.get_visible() and artist.get_in_layout()
            for artists in collections
            for artist in artists
        ):
            return True
        relative_texts = set(getattr(axes, "_title_dict", {}).values())
        for text in getattr(axes, "texts", ()):
            if not (
                text.get_visible() and text.get_in_layout() and bool(text.get_text())
            ):
                continue
            if text in relative_texts:
                continue
            transform = text.get_transform()
            if not (
                transform.contains_branch(axes.transAxes)
                or transform.contains_branch(axes.transData)
            ):
                return True
        return False

    @staticmethod
    def _is_cacheable_axes(axes):
        if getattr(axes, "_name", None) != "cartesian":
            return False
        return all(
            axis is None
            or all(
                _is_internal_ticker(obj)
                for obj in (
                    axis.major.locator,
                    axis.major.formatter,
                    axis.minor.locator,
                    axis.minor.formatter,
                )
            )
            for axis in getattr(axes, "_axis_map", {}).values()
        )

    @staticmethod
    def _get_outsets(axes_bbox, tight_bbox):
        return (
            axes_bbox.xmin - tight_bbox.xmin,
            tight_bbox.xmax - axes_bbox.xmax,
            axes_bbox.ymin - tight_bbox.ymin,
            tight_bbox.ymax - axes_bbox.ymax,
        )

    @staticmethod
    def _bbox_from_outsets(axes_bbox, outsets):
        left, right, bottom, top = outsets
        return mtransforms.Bbox.from_extents(
            axes_bbox.xmin - left,
            axes_bbox.ymin - bottom,
            axes_bbox.xmax + right,
            axes_bbox.ymax + top,
        )

    @staticmethod
    def _measure_tightbbox(axes, renderer, include_subset_titles):
        try:
            return axes.get_tightbbox(
                renderer, include_subset_titles=include_subset_titles
            )
        except TypeError:
            return axes.get_tightbbox(renderer)
