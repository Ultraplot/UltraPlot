#!/usr/bin/env python3
"""Private helpers for responsive interactive figure navigation."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import time

import matplotlib.collections as mcollections
import numpy as np
from matplotlib.backend_bases import TimerBase
from matplotlib.ticker import MaxNLocator, NullLocator

_MISSING = object()


def _preview_enabled():
    """Return the current runtime setting for approximate navigation frames."""
    # Keep this local to avoid config -> figure -> animation import cycles.
    from .config import rc_ultraplot

    return rc_ultraplot["navigation.preview"]


def _state_equal(left, right):
    """Return whether an artist property still matches our preview value."""
    if left is right:
        return True
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        return len(left) == len(right) and all(
            _state_equal(item_left, item_right)
            for item_left, item_right in zip(left, right)
        )
    try:
        return bool(
            np.array_equal(np.asanyarray(left), np.asanyarray(right), equal_nan=True)
        )
    except (TypeError, ValueError):
        try:
            return bool(left == right)
        except (TypeError, ValueError):
            return False


@dataclass
class _LocatorPreviewState:
    """Exact and temporary locators for one axis."""

    axis: object
    original_major: object
    original_minor: object
    preview_major: object
    preview_minor: object

    def restore(self):
        if self.axis.get_major_locator() is self.preview_major:
            self.axis.set_major_locator(self.original_major)
        if self.axis.get_minor_locator() is self.preview_minor:
            self.axis.set_minor_locator(self.original_minor)


@dataclass
class _LinePreviewState:
    """Exact and sampled data for one line artist."""

    artist: object
    original: tuple
    preview: tuple
    dimensions: str

    def restore(self):
        if self.dimensions == "3d":
            current = tuple(np.asanyarray(item) for item in self.artist.get_data_3d())
            restored = tuple(
                original if _state_equal(item, preview) else item
                for item, original, preview in zip(current, self.original, self.preview)
            )
            if not _state_equal(current, restored):
                self.artist.set_data_3d(*restored)
        else:
            current = (
                np.asanyarray(self.artist.get_xdata(orig=True)),
                np.asanyarray(self.artist.get_ydata(orig=True)),
            )
            restored = tuple(
                original if _state_equal(item, preview) else item
                for item, original, preview in zip(current, self.original, self.preview)
            )
            if not _state_equal(current, restored):
                self.artist.set_data(*restored)


@dataclass
class _ScatterPreviewState:
    """Exact and sampled private collection fields for one scatter artist."""

    artist: object
    original: dict
    preview: dict

    def restore(self):
        for name, preview in self.preview.items():
            current = getattr(self.artist, name, _MISSING)
            if current is _MISSING:
                continue
            if name == "_offsets3d" and isinstance(current, tuple):
                restored = tuple(
                    original if _state_equal(item, preview_item) else item
                    for item, original, preview_item in zip(
                        current, self.original[name], preview
                    )
                )
                if not _state_equal(current, restored):
                    setattr(self.artist, name, restored)
            elif _state_equal(current, preview):
                setattr(self.artist, name, self.original[name])
        self.artist.stale = True


@dataclass
class _SurfacePreviewState:
    """Temporary surface proxy attachment and draw-suppression state."""

    artist: object
    proxy: object
    ax: object
    proxy_attached: bool
    proxy_visible: bool
    hidden_marker: object

    def restore(self):
        if getattr(self.artist, "_ultraplot_navigation_hidden", _MISSING) is True:
            if self.hidden_marker is _MISSING:
                delattr(self.artist, "_ultraplot_navigation_hidden")
            else:
                self.artist._ultraplot_navigation_hidden = self.hidden_marker
        if self.proxy.get_visible():
            self.proxy.set_visible(self.proxy_visible)
        if not self.proxy_attached and self.proxy.axes is self.ax:
            self.proxy.remove()


@dataclass
class _AxesPreviewState:
    """All temporary navigation state owned for one axes."""

    ax: object
    grid_marker: object = _MISSING
    locators: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    scatters: list = field(default_factory=list)
    surfaces: list = field(default_factory=list)
    restored: bool = False

    def restore(self):
        if self.restored:
            return
        if getattr(self.ax, "_ultraplot_navigation_hide_grid", _MISSING) is True:
            if self.grid_marker is _MISSING:
                delattr(self.ax, "_ultraplot_navigation_hide_grid")
            else:
                self.ax._ultraplot_navigation_hide_grid = self.grid_marker
        for state in self.locators:
            state.restore()
        for state in self.lines:
            state.restore()
        for state in self.scatters:
            state.restore()
        for state in self.surfaces:
            state.restore()
        self.ax.stale = True
        self.restored = True


@dataclass
class _SurfaceProxyRecipe:
    """Lazy recipe for a coarse surface used only during navigation."""

    arrays: tuple
    args: tuple
    kwargs: dict
    geometry_signature: tuple
    facecolor_signature: tuple
    proxy: object = None


def _surface_geometry_signature(surface):
    vector = getattr(surface, "_vec", None)
    return (id(vector), getattr(vector, "shape", None))


def _surface_facecolor_signature(surface):
    colors = getattr(surface, "_facecolor3d", None)
    return (id(colors), getattr(colors, "shape", None))


def _register_surface_preview(surface, X, Y, Z, args, kwargs):
    """Attach a lazy coarse-surface recipe without constructing another artist."""
    try:
        arrays = tuple(np.asanyarray(array) for array in (X, Y, Z))
        if any(array.ndim != 2 for array in arrays):
            return
        rows, cols = arrays[2].shape
        if rows * cols <= 625:
            return
        row_idx = np.unique(np.linspace(0, rows - 1, min(10, rows), dtype=int))
        col_idx = np.unique(np.linspace(0, cols - 1, min(10, cols), dtype=int))
        sampled = tuple(
            np.array(array[np.ix_(row_idx, col_idx)], copy=True) for array in arrays
        )
        preview_kwargs = dict(kwargs)
        for key in ("rcount", "ccount", "rstride", "cstride"):
            preview_kwargs.pop(key, None)
        facecolors = preview_kwargs.get("facecolors")
        if facecolors is not None:
            facecolors = np.asanyarray(facecolors)
            if facecolors.shape[:2] == (rows, cols):
                preview_kwargs["facecolors"] = np.array(
                    facecolors[np.ix_(row_idx, col_idx)], copy=True
                )
            else:
                preview_kwargs.pop("facecolors")
        surface._ultraplot_lod_recipe = _SurfaceProxyRecipe(
            arrays=sampled,
            args=tuple(args),
            kwargs=preview_kwargs,
            geometry_signature=_surface_geometry_signature(surface),
            facecolor_signature=_surface_facecolor_signature(surface),
        )
    except (AttributeError, IndexError, TypeError, ValueError):
        return


def _sync_surface_proxy(surface, proxy):
    """Copy safe presentation properties from an exact surface to its proxy."""
    proxy.set_alpha(surface.get_alpha())
    proxy.set_zorder(surface.get_zorder())
    proxy.set_cmap(surface.get_cmap())
    proxy.set_norm(surface.norm)
    proxy.set_clim(*surface.get_clim())
    for getter_name, setter_name in (
        ("get_edgecolor", "set_edgecolor"),
        ("get_linewidth", "set_linewidth"),
        ("get_antialiased", "set_antialiased"),
    ):
        getter = getattr(surface, getter_name, None)
        setter = getattr(proxy, setter_name, None)
        if getter is None or setter is None:
            continue
        value = np.asanyarray(getter())
        if value.ndim == 0 or len(value) <= 1:
            setter(value)


def _prepare_surface_preview(surface):
    """Synchronize an attached proxy and return whether to suppress the exact one."""
    recipe = getattr(surface, "_ultraplot_lod_recipe", None)
    if recipe is None or recipe.proxy is None or recipe.proxy.axes is not surface.axes:
        return False
    if _surface_geometry_signature(surface) != recipe.geometry_signature:
        recipe.proxy.set_visible(False)
        return False
    if _surface_facecolor_signature(surface) != recipe.facecolor_signature:
        colors = np.asanyarray(getattr(surface, "_facecolor3d", ()))
        if colors.ndim != 2 or len(colors) != 1:
            recipe.proxy.set_visible(False)
            return False
        recipe.proxy.set_facecolor(colors)
    _sync_surface_proxy(surface, recipe.proxy)
    recipe.proxy.set_visible(surface.get_visible())
    return surface.get_visible()


def _resolve_surface_proxy(surface):
    """Create or return a valid lazy surface proxy for an exact collection."""
    recipe = getattr(surface, "_ultraplot_lod_recipe", None)
    ax = surface.axes
    if (
        recipe is None
        or ax is None
        or _surface_geometry_signature(surface) != recipe.geometry_signature
    ):
        return None
    if recipe.proxy is not None:
        _sync_surface_proxy(surface, recipe.proxy)
        return recipe.proxy

    from mpl_toolkits.mplot3d import Axes3D

    kwargs = dict(recipe.kwargs)

    limits = (ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d())
    autoscale = ax.get_autoscale_on()
    proxy = None
    try:
        proxy = Axes3D.plot_surface(ax, *recipe.arrays, *recipe.args, **kwargs)
        proxy.set_visible(False)
        proxy._ultraplot_lod_proxy = True
        proxy.remove()
        recipe.proxy = proxy
        _sync_surface_proxy(surface, proxy)
        return proxy
    except (AttributeError, IndexError, TypeError, ValueError):
        if proxy is not None and proxy.axes is ax:
            proxy.remove()
        return None
    finally:
        ax.set_xlim3d(*limits[0], auto=autoscale)
        ax.set_ylim3d(*limits[1], auto=autoscale)
        ax.set_zlim3d(*limits[2], auto=autoscale)


class _FramePacer:
    """Coalesce GUI draws and submit the newest view near a 60 Hz cadence."""

    _interval = 1 / 60

    def __init__(self, canvas, is_active):
        self.canvas = canvas
        self._is_active = is_active
        self._draw_pending = False
        self._draw_requested = False
        self._timer = None
        self._idle_draw = None
        self._last_frame_started = 0.0

    def cancel(self):
        if self._timer is not None:
            self._timer.stop()
        self._timer = None
        self._idle_draw = None
        self._draw_pending = False
        self._draw_requested = False

    def _submit(self):
        self._timer = None
        if not self._is_active() or not self._draw_requested:
            return False
        draw, self._idle_draw = self._idle_draw, None
        self._draw_requested = False
        self._draw_pending = True
        self._last_frame_started = time.monotonic()
        draw()
        return False

    def _schedule(self):
        delay = max(0.0, self._interval - (time.monotonic() - self._last_frame_started))
        timer = self.canvas.new_timer(interval=max(1, round(1_000 * delay)))
        if type(timer)._timer_start is TimerBase._timer_start:
            return False
        timer.single_shot = True
        timer.add_callback(self._submit)
        self._timer = timer
        timer.start()
        return True

    def request(self, draw):
        if not self._is_active():
            return False
        self._idle_draw = draw
        self._draw_requested = True
        if self._draw_pending or self._timer is not None:
            return True
        return self._schedule()

    def acknowledge(self):
        if not self._is_active() or not self._draw_pending:
            return
        self._draw_pending = False
        if self._draw_requested and self._timer is None:
            self._schedule()


class _NavigationInteractionManager:
    """Temporarily simplify dense scenes during interactive navigation."""

    _line_limit = 2_000
    _scatter_limit = 2_000

    def __init__(self, canvas, figure, selective):
        self.canvas = canvas
        self.figure = figure
        self.selective = selective
        self._state = None
        self._building_state = None
        self._closed = False
        self._pacer = _FramePacer(canvas, self._is_active)
        # FigureCanvasBase invokes Figure.set_canvas() before assigning its own
        # ``figure`` attribute, so the public canvas connector is not available
        # during this constructor. Keep this compatibility detail isolated here.
        callbacks = figure._canvas_callbacks
        self._press_cid = callbacks.connect("button_press_event", self._on_press)
        self._release_cid = callbacks.connect("button_release_event", self._on_release)
        self._draw_cid = callbacks.connect("draw_event", self._on_draw)
        self._close_cid = callbacks.connect("close_event", self._on_close)

    def _is_active(self):
        return not self._closed and self._state is not None

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

    @staticmethod
    def _simplify_locator(axis, state):
        original_major = axis.get_major_locator()
        original_minor = axis.get_minor_locator()
        locator_state = _LocatorPreviewState(
            axis,
            original_major,
            original_minor,
            original_major,
            original_minor,
        )
        state.locators.append(locator_state)
        axis.set_minor_locator(NullLocator())
        locator_state.preview_minor = axis.get_minor_locator()
        get_converter = getattr(axis, "get_converter", None)
        converter = get_converter() if get_converter is not None else axis.converter
        if axis.get_scale() == "linear" and converter is None:
            axis.set_major_locator(MaxNLocator(nbins=3, min_n_ticks=3))
            locator_state.preview_major = axis.get_major_locator()

    def _simplify_line(self, line, dimensions, state):
        try:
            if dimensions == "3d":
                original = tuple(np.asanyarray(array) for array in line.get_data_3d())
            else:
                original = (
                    np.asanyarray(line.get_xdata(orig=True)),
                    np.asanyarray(line.get_ydata(orig=True)),
                )
            indices = self._subset_indices(original, self._line_limit)
        except (IndexError, TypeError, ValueError):
            return
        if indices is None:
            return
        preview = tuple(array[indices] for array in original)
        line_state = _LinePreviewState(line, original, preview, dimensions)
        state.lines.append(line_state)
        if dimensions == "3d":
            line.set_data_3d(*preview)
        else:
            line.set_data(*preview)

    def _simplify_scatter(self, artist, arrays, indices, names, state):
        original = {
            name: getattr(artist, name) for name in names if hasattr(artist, name)
        }
        preview = dict(original)
        offset_name = "_offsets3d" if len(arrays) == 3 else "_offsets"
        preview[offset_name] = (
            tuple(array[indices] for array in arrays)
            if len(arrays) == 3
            else np.column_stack(tuple(array[indices] for array in arrays))
        )
        for name in (
            "_sizes",
            "_sizes3d",
            "_linewidths",
            "_linewidths3d",
            "_facecolors",
            "_edgecolors",
        ):
            values = original.get(name)
            if values is None:
                continue
            values = np.asanyarray(values)
            if values.ndim and len(values) == len(arrays[0]):
                preview[name] = values[indices]
        if len(arrays) == 3:
            preview["_depthshade"] = False
            preview["_offset_zordered"] = None
            preview["_z_markers_idx"] = slice(None)
        scatter_state = _ScatterPreviewState(artist, original, preview)
        state.scatters.append(scatter_state)
        for name, value in preview.items():
            setattr(artist, name, value)
        artist.stale = True

    def _simplify_three_axes(self, ax):
        from mpl_toolkits.mplot3d.art3d import Path3DCollection

        state = _AxesPreviewState(ax)
        self._building_state = state
        state.grid_marker = getattr(ax, "_ultraplot_navigation_hide_grid", _MISSING)
        ax._ultraplot_navigation_hide_grid = True
        for axis in ax._axis_map.values():
            self._simplify_locator(axis, state)
        for line in ax.lines:
            if hasattr(line, "get_data_3d") and hasattr(line, "set_data_3d"):
                self._simplify_line(line, "3d", state)

        for artist in tuple(ax.collections):
            if hasattr(artist, "_ultraplot_lod_recipe"):
                if not artist.get_visible():
                    continue
                proxy = _resolve_surface_proxy(artist)
                if proxy is None:
                    continue
                attached = proxy.axes is ax
                surface_state = _SurfacePreviewState(
                    artist,
                    proxy,
                    ax,
                    attached,
                    proxy.get_visible(),
                    getattr(artist, "_ultraplot_navigation_hidden", _MISSING),
                )
                state.surfaces.append(surface_state)
                if not attached:
                    ax.add_collection(proxy, autolim=False)
                artist._ultraplot_navigation_hidden = True
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
            names = (
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
            )
            self._simplify_scatter(artist, arrays, indices, names, state)
        ax.stale = True
        self._building_state = None
        return state

    def _simplify_two_axes(self, ax):
        state = _AxesPreviewState(ax)
        self._building_state = state
        for axis in (ax.xaxis, ax.yaxis):
            self._simplify_locator(axis, state)
        for line in ax.lines:
            self._simplify_line(line, "2d", state)
        for artist in ax.collections:
            if not isinstance(artist, mcollections.PathCollection):
                continue
            offsets = np.asanyarray(artist.get_offsets())
            if offsets.ndim != 2 or offsets.shape[1] != 2:
                continue
            arrays = (offsets[:, 0], offsets[:, 1])
            indices = self._subset_indices(arrays, self._scatter_limit)
            if indices is None:
                continue
            names = ("_offsets", "_sizes", "_linewidths", "_facecolors", "_edgecolors")
            self._simplify_scatter(artist, arrays, indices, names, state)
        ax.stale = True
        self._building_state = None
        return state

    def activate(self, ax):
        """Activate preview quality for the navigated axes and shared siblings."""
        is_three = self._is_three_axes(ax)
        is_two = getattr(ax, "_name", None) in ("cartesian", "cartopy", "basemap")
        if (
            self._closed
            or self._state is not None
            or not _preview_enabled()
            or not (is_three or is_two)
        ):
            return False
        states = []
        try:
            axes = self._shared_view_axes(ax) if is_three else self._shared_two_axes(ax)
            simplify = (
                self._simplify_three_axes if is_three else self._simplify_two_axes
            )
            for item in axes:
                states.append(simplify(item))
        except Exception:
            if self._building_state is not None:
                states.append(self._building_state)
            for state in reversed(states):
                state.restore()
            self._building_state = None
            return False
        self._state = states
        self.selective.invalidate()
        return True

    def deactivate(self, *, redraw=True):
        """Restore exact artists and formatting after interactive navigation."""
        if self._state is None:
            return False
        self._pacer.cancel()
        states, self._state = self._state, None
        for state in reversed(states):
            state.restore()
        self.selective.invalidate()
        if redraw:
            self.canvas.draw_idle()
        return True

    def request_draw(self, draw):
        if self._state is not None and not _preview_enabled():
            self.deactivate(redraw=False)
            return False
        return self._pacer.request(draw)

    @contextmanager
    def full_quality_context(self):
        active_ax = None if self._state is None else self._state[0].ax
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
        self._pacer.acknowledge()

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
