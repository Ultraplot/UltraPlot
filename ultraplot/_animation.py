#!/usr/bin/env python3
"""
Helpers for responsive interactive and animated UltraPlot figures.
"""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from weakref import WeakSet

import matplotlib.artist as martist
import matplotlib.axis as maxis
import matplotlib.collections as mcollections
import matplotlib.image as mimage
import matplotlib.lines as mlines
import matplotlib.text as mtext
import matplotlib.transforms as mtransforms
import numpy as np
from matplotlib.backend_bases import DrawEvent


class _SelectiveDrawManager:
    """
    Retain safe draw layers and bypass unchanged Matplotlib traversal.

    Multi-axes figures retain each complete axes as one layer. Single Cartesian
    axes retain the stable draw-order prefix below their first clipped numeric
    line, then redraw that line and every later artist as an exact z-order suffix.
    Unknown stale artists, geometry changes, overlapping layers, unsupported
    artist orders, and export draws fall back to a complete draw. The first display
    is always untouched; a later complete draw primes the retained layers.
    """

    _data_artist_types = (mlines.Line2D, mcollections.Collection, mimage.AxesImage)

    def __init__(self, canvas, figure=None):
        self.canvas = canvas
        self.figure = figure if figure is not None else canvas.figure
        self._backgrounds = {}
        self._regions = {}
        self._signatures = {}
        self._axes = ()
        self._suffix = ()
        self._pending_suffix = ()
        self._cache_mode = None
        self._capture_mode = None
        self._capturing = False
        self._selecting = False
        self._has_drawn = False
        self._suspended = False
        self._closed = False
        self._cache_safe = False
        self._selective_draw_count = 0
        self._full_draw_count = 0
        self._supports_blit = bool(canvas.supports_blit)
        callbacks = self.figure._canvas_callbacks
        self._draw_cid = callbacks.connect("draw_event", self._on_draw)
        self._resize_cid = callbacks.connect("resize_event", self._on_resize)

    @staticmethod
    def _bbox_signature(bbox):
        return tuple(float(value) for value in bbox.bounds)

    def _axes_signature(self, ax):
        return (
            tuple(
                (id(child), float(child.get_zorder())) for child in ax.get_children()
            ),
            tuple(
                (
                    id(line),
                    id(line.get_transform()),
                    bool(line.get_clip_on()),
                    id(line.get_clip_box()),
                    id(line.get_clip_path()),
                )
                for line in ax.lines
            ),
            self._bbox_signature(ax.get_position(original=False)),
            self._bbox_signature(ax.viewLim),
            ax.get_xscale(),
            ax.get_yscale(),
            bool(ax.get_visible()),
            float(ax.get_zorder()),
        )

    def _visible_axes(self):
        return tuple(ax for ax in self.figure.axes if ax.get_visible())

    def _has_explicit_blit_manager(self):
        return bool(tuple(getattr(self.figure, "_blit_managers", ())))

    def _has_animated_artist(self, axes):
        return any(artist.get_animated() for ax in axes for artist in ax.get_children())

    def _has_overlapping_figure_artist(self, suffix):
        """Return whether a later figure artist overlaps the retained suffix."""
        get_renderer = getattr(self.canvas, "get_renderer", None)
        if get_renderer is None:
            return True
        renderer = get_renderer()
        for artist in self.figure.get_children():
            if (
                artist is self.figure.patch
                or artist in self.figure.axes
                or not artist.get_visible()
            ):
                continue
            if isinstance(artist, mtext.Text) and not artist.get_text():
                continue
            try:
                overlay_bbox = artist.get_window_extent(renderer)
            except Exception:
                return True
            for child in suffix:
                if not child.get_visible():
                    continue
                try:
                    child_bbox = child.get_window_extent(renderer)
                except Exception:
                    return True
                overlap = mtransforms.Bbox.intersection(overlay_bbox, child_bbox)
                if overlap is not None and overlap.width > 0 and overlap.height > 0:
                    return True
        return False

    @staticmethod
    def _has_numeric_line_data(line):
        """Return whether line conversion cannot mutate categorical/date axes."""
        try:
            xdata = np.asanyarray(line.get_xdata(orig=True))
            ydata = np.asanyarray(line.get_ydata(orig=True))
        except (TypeError, ValueError):
            return False
        return xdata.dtype.kind in "biufc" and ydata.dtype.kind in "biufc"

    def _resolve_line_suffix(self, ax):
        """Return the exact draw-order suffix starting at the first data line."""
        if (
            getattr(ax, "_name", None) != "cartesian"
            or not ax.axison
            or not ax.get_frame_on()
            or ax.get_rasterization_zorder() is not None
            or any(not line.get_clip_on() for line in ax.lines)
            or any(not self._has_numeric_line_data(line) for line in ax.lines)
        ):
            return ()
        artists = list(ax.get_children())
        if ax.patch not in artists or not ax.lines:
            return ()
        artists.remove(ax.patch)
        artists = sorted(artists, key=lambda artist: artist.get_zorder())
        line_ids = {id(line) for line in ax.lines}
        positions = [
            index for index, artist in enumerate(artists) if id(artist) in line_ids
        ]
        if not positions:
            return ()
        suffix = tuple(artists[min(positions) :])
        if any(
            isinstance(artist, (maxis.Axis, mimage.AxesImage))
            or (hasattr(artist, "_axis_map") and artist is not ax)
            for artist in suffix
        ):
            return ()
        if self._has_overlapping_figure_artist(suffix):
            return ()
        return suffix

    @staticmethod
    def _regions_overlap(regions):
        regions = tuple(regions)
        for idx, left in enumerate(regions):
            for right in regions[idx + 1 :]:
                overlap = mtransforms.Bbox.intersection(left, right)
                if overlap is not None and overlap.width > 0 and overlap.height > 0:
                    return True
        return False

    def _resolve_region(self, ax, renderer, cached_regions):
        # UltraLayout already measured this exact region. Reconstructing it
        # from cached outsets avoids a second tick/text traversal.
        region = cached_regions.get(ax)
        if region is None:
            region = ax.get_tightbbox(renderer)
        if region is None:
            return None
        region = region.padded(2)
        return mtransforms.Bbox.intersection(region, self.figure.bbox)

    @staticmethod
    def _mark_axes_clean(axes):
        """Clear placeholder staleness left behind by ``Axes.draw()``."""
        for ax in axes:
            for child in ax.get_children():
                child.stale = False
            ax.stale = False

    def invalidate(self):
        """Discard all retained axes layers."""
        self._backgrounds.clear()
        self._regions.clear()
        self._signatures.clear()
        self._axes = ()
        self._suffix = ()
        self._pending_suffix = ()
        self._cache_mode = None
        self._capture_mode = None
        self._cache_safe = False

    def _on_resize(self, event):
        if event is None or event.canvas is self.canvas:
            self.invalidate()

    def _on_draw(self, event):
        if event is not None and event.canvas is self.canvas and not self._selecting:
            self._has_drawn = True
        if (
            self._closed
            or self._suspended
            or self._selecting
            or not self._capturing
            or event.canvas is not self.canvas
        ):
            return

        axes = self._visible_axes()
        renderer = event.renderer
        store = getattr(self.figure, "_layout_extent_store", None)
        cached_regions = {} if store is None else store._get_retained_bboxes(axes)
        regions = {
            ax: self._resolve_region(ax, renderer, cached_regions) for ax in axes
        }
        valid = all(region is not None for region in regions.values())
        if valid:
            backgrounds = {
                ax: self.canvas.copy_from_bbox(region) for ax, region in regions.items()
            }
        else:
            backgrounds = {}

        if self._capture_mode == "suffix":
            suffix = self._pending_suffix
            for artist in suffix:
                self.figure.draw_artist(artist)
        else:
            suffix = ()
            # Figure.draw() omitted these temporarily animated axes. Draw them now,
            # in normal axes z-order, before the backend presents the frame.
            for ax in sorted(axes, key=lambda item: item.get_zorder()):
                self.figure.draw_artist(ax)
        # Axes.draw() intentionally leaves some invisible placeholder text stale.
        # Retained drawing needs a clean baseline so a later property mutation can
        # be distinguished from that permanent state.
        self._mark_axes_clean(axes)
        for artist in self.figure.get_children():
            if artist not in axes:
                artist.stale = False

        self._full_draw_count += 1
        self._axes = axes
        self._suffix = suffix
        self._regions = regions if valid else {}
        self._backgrounds = backgrounds
        self._signatures = {ax: self._axes_signature(ax) for ax in axes}
        self._cache_mode = self._capture_mode
        if self._capture_mode == "suffix":
            self._cache_safe = bool(valid and suffix)
        else:
            self._cache_safe = bool(
                valid
                and len(axes) > 1
                and not self._regions_overlap(regions.values())
                and not self._has_explicit_blit_manager()
                and not self._has_animated_artist(axes)
            )
        for ax in axes:
            ax.stale = False

    @contextmanager
    def full_draw_context(self):
        """Temporarily split a full draw into static and axes layers."""
        if (
            self._closed
            or self._suspended
            or not self._supports_blit
            or self._has_explicit_blit_manager()
        ):
            self.invalidate()
            yield
            return

        axes = self._visible_axes()
        if not axes:
            self.invalidate()
            yield
            return
        if not self._has_drawn:
            self.invalidate()
            yield
            return
        if any(ax.get_animated() for ax in axes) or self._has_animated_artist(axes):
            self.invalidate()
            yield
            return

        if len(axes) == 1:
            suffix = self._resolve_line_suffix(axes[0])
            if not suffix:
                self.invalidate()
                yield
                return
            targets = suffix
            self._capture_mode = "suffix"
            self._pending_suffix = suffix
        else:
            targets = axes
            self._capture_mode = "axes"
            self._pending_suffix = ()

        animated = {artist: artist.get_animated() for artist in targets}

        self._capturing = True
        try:
            for artist in targets:
                # This is a transient draw-routing flag, not a user property
                # mutation. Avoid set_animated(), which marks every axes stale
                # and defeats the persistent layout extent cache.
                artist._animated = True
            yield
        finally:
            for artist, state in animated.items():
                artist._animated = state
            self._capturing = False
            self._capture_mode = None
            self._pending_suffix = ()

    def _dirty_axes(self):
        axes = self._visible_axes()
        if axes != self._axes:
            return None
        if any(
            artist.stale for artist in self.figure.get_children() if artist not in axes
        ):
            return None

        dirty = []
        for ax in axes:
            if self._axes_signature(ax) != self._signatures.get(ax):
                return None
            stale_children = [child for child in ax.get_children() if child.stale]
            # Layout/tick cache cleanup can leave the Axes container stale even
            # though every drawable child is clean. Child flags carry the useful
            # paint-level signal; geometry is guarded by the signature above.
            if not stale_children:
                continue
            if self._cache_mode == "suffix":
                if not all(
                    isinstance(child, mlines.Line2D)
                    and child in self._suffix
                    and self._has_numeric_line_data(child)
                    for child in stale_children
                ):
                    return None
            elif not all(
                isinstance(child, self._data_artist_types) for child in stale_children
            ):
                return None
            dirty.append(ax)
        return tuple(dirty)

    def draw_if_possible(self):
        """Use retained axes layers for paint-only data changes."""
        if (
            self._closed
            or self._suspended
            or not self._supports_blit
            or not self._cache_safe
            or self._has_explicit_blit_manager()
            or getattr(self.figure, "_layout_dirty", False)
        ):
            return False

        dirty = self._dirty_axes()
        if not dirty:
            return False

        self._selecting = True
        try:
            for ax in dirty:
                self.canvas.restore_region(self._backgrounds[ax])
            if self._cache_mode == "suffix":
                for artist in self._suffix:
                    self.figure.draw_artist(artist)
            else:
                for ax in sorted(dirty, key=lambda item: item.get_zorder()):
                    self.figure.draw_artist(ax)
            self._mark_axes_clean(dirty)
            for ax in dirty:
                self.canvas.blit(self._regions[ax])
            self.figure.stale = False
            self._selective_draw_count += 1
            DrawEvent("draw_event", self.canvas, self.canvas.get_renderer())._process()
        finally:
            self._selecting = False
        return True

    @contextmanager
    def save_context(self):
        """Suspend retained drawing while producing external output."""
        self._suspended = True
        try:
            yield
        finally:
            self._suspended = False
            self.invalidate()

    def close(self):
        if self._closed:
            return
        callbacks = self.figure._canvas_callbacks
        callbacks.disconnect(self._draw_cid)
        callbacks.disconnect(self._resize_cid)
        self.invalidate()
        self._closed = True


class _BlitManager:
    """
    Manage efficient updates of a small set of changing artists.

    The manager caches the static canvas background, restores it for each
    update, redraws only the managed artists, and blits the affected region.
    Backends without blitting support safely fall back to ``draw_idle()``.

    Parameters
    ----------
    canvas : `~matplotlib.backend_bases.FigureCanvasBase`
        Canvas containing the artists.
    artists : iterable of `~matplotlib.artist.Artist`, optional
        Artists that will change between updates.
    bbox : `~matplotlib.transforms.Bbox` or object with a ``bbox`` attribute, optional
        Region to cache and blit. By default, the union of the managed artists'
        axes bounding boxes is used. Figure-level artists fall back to the full
        figure bounding box.

    Notes
    -----
    Managed artists are drawn above the cached static background, matching
    Matplotlib's standard blitting behavior.
    """

    def __init__(self, canvas, artists: Iterable[martist.Artist] = (), bbox=None):
        if canvas.figure is None:
            raise RuntimeError("Cannot manage blitting for a canvas without a figure.")
        self.canvas = canvas
        self.figure = canvas.figure
        self._artists = []
        self._animated = {}
        self._bbox = bbox
        self._background = None
        self._closed = False
        self._suspended = False
        self._supports_blit = bool(canvas.supports_blit)
        self._draw_cid = canvas.mpl_connect("draw_event", self._on_draw)
        self._resize_cid = canvas.mpl_connect("resize_event", self._on_resize)
        managers = getattr(self.figure, "_blit_managers", None)
        if managers is None:
            managers = self.figure._blit_managers = WeakSet()
        managers.add(self)
        for artist in artists:
            self.add_artist(artist)

    @property
    def artists(self):
        """Managed artists as an immutable tuple."""
        return tuple(self._artists)

    @property
    def supports_blit(self):
        """Whether the associated canvas supports blitting."""
        return self._supports_blit

    def _resolve_bbox(self):
        bbox = self._bbox
        if bbox is not None:
            return getattr(bbox, "bbox", bbox)

        axes = []
        for artist in self._artists:
            axis = getattr(artist, "axes", None)
            if axis is None:
                return self.figure.bbox
            if axis not in axes:
                axes.append(axis)
        if not axes:
            return self.figure.bbox
        return mtransforms.Bbox.union([axis.bbox for axis in axes])

    def _draw_artists(self):
        for artist in sorted(self._artists, key=lambda item: item.get_zorder()):
            self.figure.draw_artist(artist)

    def _on_draw(self, event):
        if self._closed or self._suspended or not self._supports_blit:
            return
        if event is not None and event.canvas is not self.canvas:
            return
        self._background = self.canvas.copy_from_bbox(self._resolve_bbox())
        self._draw_artists()

    def _on_resize(self, event):
        if event is None or event.canvas is self.canvas:
            self.invalidate()

    def add_artist(self, artist: martist.Artist):
        """
        Add an artist to the managed update set.

        Returns
        -------
        _BlitManager
            This manager, to permit chained calls.
        """
        if self._closed:
            raise RuntimeError("Cannot add artists to a closed _BlitManager.")
        if not isinstance(artist, martist.Artist):
            raise TypeError(
                f"Expected a matplotlib Artist, got {type(artist).__name__}."
            )
        if artist.figure is not self.figure:
            raise RuntimeError("The artist must belong to the manager's figure.")
        if artist in self._artists:
            return self
        self._artists.append(artist)
        self._animated[artist] = artist.get_animated()
        if self._supports_blit:
            artist.set_animated(True)
        self.invalidate()
        return self

    def remove_artist(self, artist: martist.Artist):
        """
        Stop managing an artist and restore its original animated state.

        Returns
        -------
        _BlitManager
            This manager, to permit chained calls.
        """
        if artist not in self._artists:
            return self
        self._artists.remove(artist)
        artist.set_animated(self._animated.pop(artist))
        self.invalidate()
        return self

    def invalidate(self):
        """Discard the cached background before the next update."""
        self._background = None

    @contextmanager
    def _save_context(self):
        """Temporarily restore original artist states for a complete export."""
        if self._closed:
            yield
            return
        self._suspended = True
        current = {artist: artist.get_animated() for artist in self._artists}
        try:
            for artist in self._artists:
                artist.set_animated(self._animated[artist])
            yield
        finally:
            for artist, animated in current.items():
                artist.set_animated(animated)
            self._suspended = False
            self.invalidate()

    def update(self, *, flush=False):
        """
        Redraw the managed artists.

        Parameters
        ----------
        flush : bool, default: False
            Whether to immediately process pending GUI events after blitting.

        Returns
        -------
        bool
            ``True`` when the blitting fast path was used, otherwise ``False``.
        """
        if self._closed:
            raise RuntimeError("Cannot update a closed _BlitManager.")
        if not self._supports_blit:
            self.canvas.draw_idle()
            if flush:
                self.canvas.flush_events()
            return False

        if self._background is None:
            # The draw_event callback captures the static background and draws
            # the animated artists before the backend presents the frame.
            self.canvas.draw()
        else:
            bbox = self._resolve_bbox()
            self.canvas.restore_region(self._background)
            self._draw_artists()
            self.canvas.blit(bbox)
        if flush:
            self.canvas.flush_events()
        return True

    def close(self, *, redraw=True):
        """
        Disconnect callbacks and restore the artists' animated states.

        Parameters
        ----------
        redraw : bool, default: True
            Whether to schedule a normal full redraw after restoring the artists.
        """
        if self._closed:
            return
        self.canvas.mpl_disconnect(self._draw_cid)
        self.canvas.mpl_disconnect(self._resize_cid)
        for artist in tuple(self._artists):
            artist.set_animated(self._animated[artist])
        self._artists.clear()
        self._animated.clear()
        self._background = None
        self._closed = True
        managers = getattr(self.figure, "_blit_managers", ())
        managers.discard(self)
        if redraw:
            self.canvas.draw_idle()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
