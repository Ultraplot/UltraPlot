#!/usr/bin/env python3
"""
Helpers for responsive interactive and animated UltraPlot figures.
"""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
import time
from weakref import WeakSet

import matplotlib.artist as martist
import matplotlib.axis as maxis
import matplotlib.collections as mcollections
import matplotlib.image as mimage
import matplotlib.lines as mlines
import matplotlib.text as mtext
import matplotlib.transforms as mtransforms
import numpy as np
from matplotlib.backend_bases import DrawEvent, TimerBase
from matplotlib.ticker import MaxNLocator, NullLocator


class _NavigationInteractionManager:
    """Temporarily simplify dense scenes during interactive navigation."""

    _frame_interval = 1 / 60
    _line_limit = 2_000
    _scatter_limit = 2_000

    def __init__(self, canvas, figure, selective):
        self.canvas = canvas
        self.figure = figure
        self.selective = selective
        self._state = None
        self._building_state = None
        self._closed = False
        self._draw_pending = False
        self._draw_requested = False
        self._frame_timer = None
        self._idle_draw = None
        self._last_frame_started = 0.0
        callbacks = figure._canvas_callbacks
        self._press_cid = callbacks.connect("button_press_event", self._on_press)
        self._release_cid = callbacks.connect("button_release_event", self._on_release)
        self._draw_cid = callbacks.connect("draw_event", self._on_draw)
        self._close_cid = callbacks.connect("close_event", self._on_close)

    @staticmethod
    def _is_three_axes(ax):
        return getattr(ax, "_name", None) == "three"

    @staticmethod
    def _subset_indices(arrays, limit):
        size = min(len(array) for array in arrays)
        if size <= limit:
            return None
        indices = list(np.linspace(0, size - 1, limit, dtype=int))
        for array in arrays:
            values = np.asanyarray(array)
            if values.dtype.kind not in "biufc":
                continue
            try:
                indices.extend((int(np.nanargmin(values)), int(np.nanargmax(values))))
            except ValueError:
                pass
        return np.unique(np.clip(indices, 0, size - 1))

    @staticmethod
    def _shared_view_axes(ax):
        grouper = getattr(ax, "_shared_axes", {}).get("view")
        if grouper is None:
            return (ax,)
        return tuple(
            item
            for item in grouper.get_siblings(ax)
            if getattr(item, "_name", None) == "three"
        )

    @staticmethod
    def _simplify_locators(axis, state):
        """Reduce tick work for plain numeric axes and retain exact locators."""
        major = axis.get_major_locator()
        minor = axis.get_minor_locator()
        state["locators"].append((axis, major, minor))
        axis.set_minor_locator(NullLocator())
        # Converter-backed axes include dates, categories, and custom units. Their
        # specialized tick semantics matter more than a temporary frame-rate gain.
        get_converter = getattr(axis, "get_converter", None)
        converter = get_converter() if get_converter is not None else axis.converter
        if axis.get_scale() == "linear" and converter is None:
            axis.set_major_locator(MaxNLocator(nbins=3, min_n_ticks=3))

    def _cancel_scheduled_draw(self):
        """Cancel a queued navigation frame without affecting exact draws."""
        if self._frame_timer is not None:
            self._frame_timer.stop()
        self._frame_timer = None
        self._idle_draw = None
        self._draw_pending = False
        self._draw_requested = False

    def _submit_draw(self):
        """Submit the newest coalesced view to the backend event loop."""
        self._frame_timer = None
        if self._closed or self._state is None or not self._draw_requested:
            return False
        draw, self._idle_draw = self._idle_draw, None
        self._draw_requested = False
        self._draw_pending = True
        self._last_frame_started = time.monotonic()
        draw()
        return False

    def _schedule_draw(self):
        """Schedule the next frame on a stable 60 Hz cadence."""
        delay = max(
            0.0,
            self._frame_interval - (time.monotonic() - self._last_frame_started),
        )
        timer = self.canvas.new_timer(interval=max(1, int(np.ceil(1_000 * delay))))
        # Non-interactive canvases use TimerBase's inert implementation. Preserve
        # their normal synchronous draw_idle behavior instead of swallowing draws.
        if type(timer)._timer_start is TimerBase._timer_start:
            return False
        timer.single_shot = True
        timer.add_callback(self._submit_draw)
        self._frame_timer = timer
        timer.start()
        return True

    def request_draw(self, draw):
        """Coalesce rapid navigation updates and retain only the newest view."""
        if self._closed or self._state is None:
            return False
        self._idle_draw = draw
        self._draw_requested = True
        if self._draw_pending or self._frame_timer is not None:
            return True
        return self._schedule_draw()

    def _simplify_axes(self, ax):
        from mpl_toolkits.mplot3d.art3d import Path3DCollection

        state = {
            "ax": ax,
            "grid3d": getattr(ax, "_draw_grid", True),
            "locators": [],
            "lines": [],
            "scatters": [],
            "surfaces": [],
        }
        self._building_state = state
        ax._draw_grid = False
        for axis in ax._axis_map.values():
            self._simplify_locators(axis, state)

        for line in ax.lines:
            get_data = getattr(line, "get_data_3d", None)
            set_data = getattr(line, "set_data_3d", None)
            if get_data is None or set_data is None:
                continue
            try:
                data = tuple(np.asanyarray(array) for array in get_data())
                indices = self._subset_indices(data, self._line_limit)
            except (IndexError, TypeError, ValueError):
                continue
            if indices is None:
                continue
            state["lines"].append((line, data, "3d"))
            set_data(*(array[indices] for array in data))

        # Iterate over a snapshot because surface previews temporarily replace
        # their exact collections in the axes child list.
        for artist in tuple(ax.collections):
            proxy = getattr(artist, "_ultraplot_lod_proxy", None)
            if proxy is not None and proxy is not True:
                attached = proxy.axes is ax
                try:
                    child_index = ax._children.index(artist)
                except ValueError:
                    child_index = None
                state["surfaces"].append(
                    (
                        artist,
                        proxy,
                        artist.get_visible(),
                        proxy.get_visible(),
                        attached,
                        child_index,
                    )
                )
                if not attached:
                    ax.add_collection(proxy, autolim=False)
                # Axes3D projects collections before testing visibility, so merely
                # hiding the exact surface still pays its full depth-sort cost.
                # Detach it for the gesture and restore its child position later.
                artist.remove()
                proxy.set_visible(True)
                continue
            if not isinstance(artist, Path3DCollection):
                continue
            offsets = getattr(artist, "_offsets3d", None)
            if offsets is None:
                continue
            arrays = tuple(np.asanyarray(array) for array in offsets)
            indices = self._subset_indices(arrays, self._scatter_limit)
            if indices is None:
                continue
            attributes = {}
            for name in (
                "_offsets3d",
                "_sizes",
                "_sizes3d",
                "_linewidths",
                "_linewidths3d",
                "_facecolors",
                "_edgecolors",
                "_depthshade",
                "_offset_zordered",
                "_z_markers_idx",
            ):
                if hasattr(artist, name):
                    attributes[name] = getattr(artist, name)
            state["scatters"].append((artist, attributes))
            artist._offsets3d = tuple(array[indices] for array in arrays)
            for name in (
                "_sizes",
                "_sizes3d",
                "_linewidths",
                "_linewidths3d",
                "_facecolors",
                "_edgecolors",
            ):
                values = getattr(artist, name, None)
                if values is None:
                    continue
                values = np.asanyarray(values)
                if values.ndim and len(values) == len(arrays[0]):
                    setattr(artist, name, values[indices])
            artist._depthshade = False
            artist._offset_zordered = None
            artist._z_markers_idx = slice(None)
            artist.stale = True
        ax.stale = True
        self._building_state = None
        return state

    def _simplify_two_axes(self, ax):
        """Reduce dense 2D data while the toolbar pan gesture is active."""
        state = {
            "ax": ax,
            "grid3d": None,
            "locators": [],
            "lines": [],
            "scatters": [],
            "surfaces": [],
        }
        self._building_state = state
        for axis in (ax.xaxis, ax.yaxis):
            self._simplify_locators(axis, state)
        for line in ax.lines:
            try:
                data = (
                    np.asanyarray(line.get_xdata(orig=True)),
                    np.asanyarray(line.get_ydata(orig=True)),
                )
                indices = self._subset_indices(data, self._line_limit)
            except (IndexError, TypeError, ValueError):
                continue
            if indices is None:
                continue
            state["lines"].append((line, data, "2d"))
            line.set_data(*(array[indices] for array in data))
        for artist in ax.collections:
            if not isinstance(artist, mcollections.PathCollection):
                continue
            offsets = np.asanyarray(artist.get_offsets())
            if offsets.ndim != 2 or offsets.shape[1] != 2:
                continue
            indices = self._subset_indices(
                (offsets[:, 0], offsets[:, 1]), self._scatter_limit
            )
            if indices is None:
                continue
            attributes = {}
            for name in (
                "_offsets",
                "_sizes",
                "_linewidths",
                "_facecolors",
                "_edgecolors",
            ):
                if hasattr(artist, name):
                    attributes[name] = getattr(artist, name)
            state["scatters"].append((artist, attributes))
            artist.set_offsets(offsets[indices])
            for name in ("_sizes", "_linewidths", "_facecolors", "_edgecolors"):
                values = getattr(artist, name, None)
                if values is None:
                    continue
                values = np.asanyarray(values)
                if values.ndim and len(values) == len(offsets):
                    setattr(artist, name, values[indices])
            artist.stale = True
        ax.stale = True
        self._building_state = None
        return state

    @staticmethod
    def _shared_two_axes(ax):
        axes = {ax}
        for grouper in (ax.get_shared_x_axes(), ax.get_shared_y_axes()):
            axes.update(grouper.get_siblings(ax))
        return tuple(
            item
            for item in ax.figure.axes
            if item in axes
            and getattr(item, "_name", None) in ("cartesian", "cartopy", "basemap")
        )

    def activate(self, ax):
        """Activate preview quality for the navigated axes and shared siblings."""
        is_three = self._is_three_axes(ax)
        is_two = getattr(ax, "_name", None) in ("cartesian", "cartopy", "basemap")
        if self._closed or self._state is not None or not (is_three or is_two):
            return False
        states = []
        try:
            axes = self._shared_view_axes(ax) if is_three else self._shared_two_axes(ax)
            for item in axes:
                simplify = self._simplify_axes if is_three else self._simplify_two_axes
                states.append(simplify(item))
        except Exception:
            if self._building_state is not None:
                states.append(self._building_state)
            self._restore_states(states)
            self._building_state = None
            return False
        self._state = states
        self._last_frame_started = 0.0
        self.selective.invalidate()
        return True

    @staticmethod
    def _restore_states(states):
        for state in reversed(states):
            ax = state["ax"]
            if state["grid3d"] is not None:
                ax._draw_grid = state["grid3d"]
            for axis, major, minor in state["locators"]:
                axis.set_major_locator(major)
                axis.set_minor_locator(minor)
            for line, data, dimensions in state["lines"]:
                if dimensions == "3d":
                    line.set_data_3d(*data)
                else:
                    line.set_data(*data)
            for artist, attributes in state["scatters"]:
                for name, value in attributes.items():
                    setattr(artist, name, value)
                artist.stale = True
            for (
                artist,
                proxy,
                visible,
                proxy_visible,
                attached,
                child_index,
            ) in state["surfaces"]:
                if artist.axes is not ax:
                    ax.add_collection(artist, autolim=False)
                if child_index is not None:
                    try:
                        ax._children.remove(artist)
                    except ValueError:
                        pass
                    ax._children.insert(min(child_index, len(ax._children)), artist)
                artist.set_visible(visible)
                proxy.set_visible(proxy_visible)
                if not attached and proxy.axes is ax:
                    proxy.remove()
            ax.stale = True

    def deactivate(self, *, redraw=True):
        """Restore exact artists and formatting after interactive rotation."""
        if self._state is None:
            return False
        self._cancel_scheduled_draw()
        states, self._state = self._state, None
        self._restore_states(states)
        self.selective.invalidate()
        if redraw:
            self.canvas.draw_idle()
        return True

    @contextmanager
    def full_quality_context(self):
        """Temporarily restore exact artists for save/export operations."""
        active_ax = None if self._state is None else self._state[0]["ax"]
        if active_ax is not None:
            self.deactivate(redraw=False)
        try:
            yield
        finally:
            if active_ax is not None and not self._closed:
                self.activate(active_ax)

    def _on_press(self, event):
        ax = event.inaxes
        if self._is_three_axes(ax):
            buttons = (*ax._rotate_btn, *ax._pan_btn, *ax._zoom_btn)
            if event.button in buttons:
                self.activate(ax)
        elif getattr(ax, "_name", None) in ("cartesian", "cartopy", "basemap") and str(
            ax.get_navigate_mode()
        ).upper().endswith("PAN"):
            self.activate(ax)

    def _on_release(self, event):
        self.deactivate(redraw=True)

    def _on_draw(self, event):
        if self._state is None or not self._draw_pending:
            return
        self._draw_pending = False
        if self._draw_requested and self._frame_timer is None:
            self._schedule_draw()

    def _on_close(self, event):
        self.close()

    def close(self):
        if self._closed:
            return
        self.deactivate(redraw=False)
        callbacks = self.figure._canvas_callbacks
        callbacks.disconnect(self._press_cid)
        callbacks.disconnect(self._release_cid)
        callbacks.disconnect(self._draw_cid)
        callbacks.disconnect(self._close_cid)
        self._closed = True


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
        self._figure_background = None
        self._regions = {}
        self._signatures = {}
        self._camera_signatures = {}
        self._view_signatures = {}
        self._axes = ()
        self._suffixes = {}
        self._pending_suffixes = {}
        self._pending_regions = {}
        self._cache_mode = None
        self._capture_mode = None
        self._capturing = False
        self._selecting = False
        self._has_drawn = False
        self._suspended = False
        self._closed = False
        self._cache_safe = False
        self._canvas_signature = None
        self._drawn_view_signature = None
        self._selective_draw_count = 0
        self._full_draw_count = 0
        self._supports_blit = bool(canvas.supports_blit)
        callbacks = self.figure._canvas_callbacks
        self._draw_cid = callbacks.connect("draw_event", self._on_draw)
        self._resize_cid = callbacks.connect("resize_event", self._on_resize)
        self._navigation_preview = _NavigationInteractionManager(
            canvas, self.figure, self
        )

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
            bool(ax.get_visible()),
            float(ax.get_zorder()),
        )

    def _axes_view_signature(self, ax):
        """Return paint-only limits, scales, and projection camera state."""
        return (
            self._bbox_signature(ax.viewLim),
            ax.get_xscale(),
            ax.get_yscale(),
            self._camera_signature(ax),
        )

    def _current_canvas_signature(self):
        """Return framebuffer properties that invalidate copied pixel regions."""
        get_renderer = getattr(self.canvas, "get_renderer", None)
        if get_renderer is None:
            return None
        try:
            renderer = get_renderer()
        except Exception:
            return None
        return (
            float(self.figure.dpi),
            self._bbox_signature(self.figure.bbox),
            float(renderer.width),
            float(renderer.height),
            float(getattr(self.canvas, "device_pixel_ratio", 1)),
        )

    def _view_signature(self, axes=None):
        """Return the view state last presented by a complete canvas draw."""
        axes = self._visible_axes() if axes is None else axes
        return tuple(
            (
                id(ax),
                self._axes_view_signature(ax),
            )
            for ax in axes
        )

    @staticmethod
    def _camera_signature(ax):
        """Return 3D camera and limits, or ``None`` for ordinary 2D axes."""
        if getattr(ax, "_name", None) != "three":
            return None
        try:
            return (
                float(ax.elev),
                float(ax.azim),
                float(ax.roll),
                int(ax._vertical_axis),
                tuple(float(value) for value in ax.get_xlim3d()),
                tuple(float(value) for value in ax.get_ylim3d()),
                tuple(float(value) for value in ax.get_zlim3d()),
                float(ax._focal_length),
                tuple(float(value) for value in ax.get_box_aspect()),
            )
        except (AttributeError, TypeError, ValueError):
            return None

    def _visible_axes(self):
        return tuple(ax for ax in self.figure.axes if ax.get_visible())

    def _has_explicit_blit_manager(self):
        return bool(tuple(getattr(self.figure, "_blit_managers", ())))

    def _has_animated_artist(self, axes):
        return any(artist.get_animated() for ax in axes for artist in ax.get_children())

    def _has_overlapping_figure_artist(self, targets):
        """Return whether a figure artist overlaps retained artists or regions."""
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
            for target in targets:
                if isinstance(target, martist.Artist):
                    if not target.get_visible():
                        continue
                    try:
                        target_bbox = target.get_window_extent(renderer)
                    except Exception:
                        return True
                else:
                    target_bbox = target
                overlap = mtransforms.Bbox.intersection(overlay_bbox, target_bbox)
                if overlap is not None and overlap.width > 0 and overlap.height > 0:
                    return True
        return False

    @staticmethod
    def _bbox_contains(outer, inner, tolerance=1e-6):
        return (
            inner.x0 >= outer.x0 - tolerance
            and inner.y0 >= outer.y0 - tolerance
            and inner.x1 <= outer.x1 + tolerance
            and inner.y1 <= outer.y1 + tolerance
        )

    def _suffix_fits_region(self, suffix, region, renderer):
        """Return whether restoring *region* clears every suffix paint extent."""
        for artist in suffix:
            if not artist.get_visible():
                continue
            try:
                extent = artist.get_window_extent(renderer)
            except Exception:
                return False
            # Invisible placeholder labels commonly have zero-area extents just
            # outside the axes tight bbox. They cannot damage any pixels.
            if extent.width <= 0 or extent.height <= 0:
                continue
            if artist.get_path_effects():
                return False
            if artist.get_clip_on():
                clip_box = artist.get_clip_box()
                if clip_box is not None:
                    extent = mtransforms.Bbox.intersection(extent, clip_box)
                    if extent is None:
                        continue
                if artist.get_clip_path() is not None:
                    # Arbitrary clip paths cannot be bounded reliably here.
                    return False
            if not self._bbox_contains(region, extent):
                return False
        return True

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
        self._figure_background = None
        self._regions.clear()
        self._signatures.clear()
        self._camera_signatures.clear()
        self._view_signatures.clear()
        self._axes = ()
        self._suffixes = {}
        self._pending_suffixes = {}
        self._pending_regions = {}
        self._cache_mode = None
        self._capture_mode = None
        self._cache_safe = False
        self._canvas_signature = None

    def _on_resize(self, event):
        if event is None or event.canvas is self.canvas:
            self.invalidate()

    def _on_draw(self, event):
        if event is not None and event.canvas is self.canvas and not self._selecting:
            self._has_drawn = True
            self._drawn_view_signature = self._view_signature()
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
        regions = self._pending_regions or {
            ax: self._resolve_region(ax, renderer, cached_regions) for ax in axes
        }
        valid = all(region is not None for region in regions.values())
        if valid:
            backgrounds = {
                ax: self.canvas.copy_from_bbox(region) for ax, region in regions.items()
            }
        else:
            backgrounds = {}

        figure_background = None
        if self._capture_mode == "axes":
            figure_background = self.canvas.copy_from_bbox(self.figure.bbox)

        if self._capture_mode == "suffix":
            suffixes = self._pending_suffixes
            for ax in sorted(axes, key=lambda item: item.get_zorder()):
                for artist in suffixes[ax]:
                    self.figure.draw_artist(artist)
        else:
            suffixes = {}
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
        self._suffixes = suffixes
        self._regions = regions if valid else {}
        self._backgrounds = backgrounds
        self._figure_background = figure_background
        self._signatures = {ax: self._axes_signature(ax) for ax in axes}
        self._camera_signatures = {ax: self._camera_signature(ax) for ax in axes}
        self._view_signatures = {ax: self._axes_view_signature(ax) for ax in axes}
        self._canvas_signature = self._current_canvas_signature()
        self._cache_mode = self._capture_mode
        if self._capture_mode == "suffix":
            self._cache_safe = bool(
                valid
                and len(suffixes) == len(axes)
                and self._canvas_signature is not None
                and not self._regions_overlap(regions.values())
                and all(
                    self._suffix_fits_region(suffixes[ax], regions[ax], renderer)
                    for ax in axes
                )
            )
        else:
            self._cache_safe = bool(
                valid
                and self._canvas_signature is not None
                and len(axes) > 1
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

        # A changing view is normally an interactive pan. Rebuilding retained
        # layers on every motion frame adds work that the next frame discards.
        # Draw it normally; an unchanged later draw can prime the cache again.
        view_signature = self._view_signature(axes)
        if (
            self._drawn_view_signature is not None
            and view_signature != self._drawn_view_signature
        ):
            self.invalidate()
            yield
            return

        suffixes = {ax: self._resolve_line_suffix(ax) for ax in axes}
        if all(suffixes.values()):
            renderer = self.canvas.get_renderer()
            store = getattr(self.figure, "_layout_extent_store", None)
            cached_regions = {} if store is None else store._get_retained_bboxes(axes)
            regions = {
                ax: self._resolve_region(ax, renderer, cached_regions) for ax in axes
            }
            if any(region is None for region in regions.values()) or (
                len(axes) > 1 and self._regions_overlap(regions.values())
            ):
                self.invalidate()
                yield
                return
            targets = tuple(
                artist
                for ax in sorted(axes, key=lambda item: item.get_zorder())
                for artist in suffixes[ax]
            )
            self._capture_mode = "suffix"
            self._pending_suffixes = suffixes
            self._pending_regions = regions
        elif len(axes) == 1:
            self.invalidate()
            yield
            return
        else:
            renderer = self.canvas.get_renderer()
            store = getattr(self.figure, "_layout_extent_store", None)
            cached_regions = {} if store is None else store._get_retained_bboxes(axes)
            regions = {
                ax: self._resolve_region(ax, renderer, cached_regions) for ax in axes
            }
            if any(
                region is None for region in regions.values()
            ) or self._has_overlapping_figure_artist(regions.values()):
                self.invalidate()
                yield
                return
            targets = axes
            self._capture_mode = "axes"
            self._pending_suffixes = {}
            self._pending_regions = regions

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
            self._pending_suffixes = {}
            self._pending_regions = {}

    def _dirty_axes(self):
        axes = self._visible_axes()
        if axes != self._axes:
            return None
        if any(
            artist.stale for artist in self.figure.get_children() if artist not in axes
        ):
            return None

        dirty = []
        view_dirty = []
        for ax in axes:
            view_changed = self._axes_view_signature(ax) != self._view_signatures.get(
                ax
            )
            if view_changed and self._cache_mode != "axes":
                return None
            if (
                view_changed
                and getattr(ax, "_name", None) == "three"
                and len(axes) <= 2
            ):
                # Measuring a rotated 3D extent requires one preliminary axes
                # draw. With at most two axes this cannot beat a complete draw.
                return None
            if self._axes_signature(ax) != self._signatures.get(ax):
                return None
            stale_children = [child for child in ax.get_children() if child.stale]
            # Layout/tick cache cleanup can leave the Axes container stale even
            # though every drawable child is clean. Child flags carry the useful
            # paint-level signal; geometry is guarded by the signature above.
            if view_changed:
                dirty.append(ax)
                view_dirty.append(ax)
                continue
            if not stale_children:
                continue
            if self._cache_mode == "suffix":
                suffix = self._suffixes.get(ax, ())
                if not all(
                    isinstance(child, mlines.Line2D)
                    and child in suffix
                    and self._has_numeric_line_data(child)
                    for child in stale_children
                ):
                    return None
            elif not all(
                isinstance(child, self._data_artist_types) for child in stale_children
            ):
                return None
            dirty.append(ax)
        return tuple(dirty), tuple(view_dirty)

    def _damage_closure(self, dirty, damage):
        """Expand damage to intersecting axes and preserve figure-level order."""
        damage = damage.padded(2)
        damage = mtransforms.Bbox.intersection(damage, self.figure.bbox)
        if damage is not None:
            damage = mtransforms.Bbox.from_extents(
                np.floor(damage.x0),
                np.floor(damage.y0),
                np.ceil(damage.x1),
                np.ceil(damage.y1),
            )
        if damage is None or self._has_overlapping_figure_artist((damage,)):
            return None

        redraw = set(dirty)
        changed = True
        while changed:
            changed = False
            for ax in self._axes:
                if ax in redraw:
                    continue
                # Retained regions include two safety pixels. Only propagate
                # through overlap with the actual painted extent, otherwise
                # adjacent subplot padding forms an unnecessary redraw chain.
                painted_region = self._regions[ax].padded(-2)
                overlap = mtransforms.Bbox.intersection(damage, painted_region)
                if overlap is not None and overlap.width > 0 and overlap.height > 0:
                    redraw.add(ax)
                    damage = mtransforms.Bbox.union([damage, self._regions[ax]])
                    changed = True
        return damage, tuple(
            ax
            for ax in sorted(self._axes, key=lambda item: item.get_zorder())
            if ax in redraw
        )

    def _view_damage(self, dirty, renderer):
        """Resolve exact damage after view changes and axes needing repaint."""
        new_regions = {}
        needs_measurement_draw = any(
            getattr(ax, "_name", None) == "three" for ax in dirty
        )
        measurement_background = (
            self.canvas.copy_from_bbox(self.figure.bbox)
            if needs_measurement_draw
            else None
        )
        try:
            for ax in dirty:
                if getattr(ax, "_name", None) == "three":
                    # Axis3D tick positions are updated only by draw(). Draw once
                    # to measure the new camera extent, then undo that probe.
                    self.figure.draw_artist(ax)
                region = self._resolve_region(ax, renderer, {})
                if region is None:
                    return None
                new_regions[ax] = region
        finally:
            if measurement_background is not None:
                self.canvas.restore_region(measurement_background)
        damage = mtransforms.Bbox.union(
            [self._regions[ax] for ax in dirty] + [new_regions[ax] for ax in dirty]
        )
        resolved = self._damage_closure(dirty, damage)
        if resolved is None:
            return None
        damage, redraw = resolved
        return damage, redraw, new_regions

    def draw_if_possible(self):
        """Use retained axes layers for paint-only data changes."""
        canvas_signature = self._current_canvas_signature()
        canvas_changed = (
            self._canvas_signature is not None
            and canvas_signature != self._canvas_signature
        )
        if (
            self._closed
            or self._suspended
            or not self._supports_blit
            or not self._cache_safe
            or self._has_explicit_blit_manager()
            or getattr(self.figure, "_layout_dirty", False)
            or canvas_changed
        ):
            if canvas_changed:
                self.invalidate()
            return False

        dirty_state = self._dirty_axes()
        if dirty_state is None:
            return False
        dirty, view_dirty = dirty_state
        if not dirty:
            return False

        self._selecting = True
        try:
            renderer = self.canvas.get_renderer()
            if view_dirty:
                if self._figure_background is None:
                    return False
                resolved = self._view_damage(view_dirty, renderer)
                if resolved is None:
                    return False
                damage, redraw, new_regions = resolved
                # Each exact region buffer has backend-correct integer bounds.
                # Restoring every axes in the overlap closure clears old paint;
                # pixels in newly exposed areas already contain the static frame.
                for ax in redraw:
                    self.canvas.restore_region(self._backgrounds[ax])
                for ax in redraw:
                    self.figure.draw_artist(ax)
                for ax, region in new_regions.items():
                    self._regions[ax] = region
                blit_regions = (damage,)
                painted = redraw
            elif self._cache_mode == "suffix":
                for ax in dirty:
                    self.canvas.restore_region(self._backgrounds[ax])
                for ax in sorted(dirty, key=lambda item: item.get_zorder()):
                    for artist in self._suffixes[ax]:
                        self.figure.draw_artist(artist)
                blit_regions = tuple(self._regions[ax] for ax in dirty)
                painted = dirty
            else:
                damage = mtransforms.Bbox.union([self._regions[ax] for ax in dirty])
                resolved = self._damage_closure(dirty, damage)
                if resolved is None:
                    return False
                damage, redraw = resolved
                for ax in redraw:
                    self.canvas.restore_region(self._backgrounds[ax])
                for ax in redraw:
                    self.figure.draw_artist(ax)
                blit_regions = (damage,)
                painted = redraw
            self._mark_axes_clean(painted)
            for ax in painted:
                # Complete 3D axes draws can update collection zorders and other
                # renderer-facing state. Refresh signatures from the exact frame.
                self._signatures[ax] = self._axes_signature(ax)
                self._camera_signatures[ax] = self._camera_signature(ax)
                self._view_signatures[ax] = self._axes_view_signature(ax)
            self._drawn_view_signature = self._view_signature()
            for region in blit_regions:
                self.canvas.blit(region)
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
            with self._navigation_preview.full_quality_context():
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
        self._navigation_preview.close()
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
