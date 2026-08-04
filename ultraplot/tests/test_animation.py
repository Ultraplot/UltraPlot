from unittest.mock import MagicMock

import datetime
import io
import matplotlib
import numpy as np
import pytest
from matplotlib import ticker as mticker
from matplotlib import transforms as mtransforms
from matplotlib.animation import FuncAnimation
from matplotlib.backend_bases import FigureCanvasBase, MouseEvent, TimerBase
from PIL import Image

import ultraplot as uplt
from ultraplot._animation import _BlitManager
from ultraplot._layout import _AxisTickCache, _LayoutTransaction


def test_auto_layout_not_called_on_every_frame():
    """
    Test that auto_layout is not called on every frame of a FuncAnimation.
    """
    fig, ax = uplt.subplots()
    fig.auto_layout = MagicMock()

    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)
    (line,) = ax.plot(x, y)

    def update(frame):
        line.set_ydata(np.sin(x + frame / 10.0))
        return (line,)

    ani = FuncAnimation(fig, update, frames=10, blit=False)
    # The animation is not actually run, but the initial draw will call auto_layout once
    fig.canvas.draw()

    assert fig.auto_layout.call_count == 1


def test_draw_idle_skips_auto_layout_after_first_draw():
    """
    draw_idle should not re-run auto_layout after the initial draw.
    """
    fig, ax = uplt.subplots()
    fig.auto_layout = MagicMock()

    fig.canvas.draw()
    assert fig.auto_layout.call_count == 1

    fig.canvas.draw_idle()
    assert fig.auto_layout.call_count == 1


def test_initial_draw_reuses_tick_updates():
    """
    Layout and render phases should share identical tick computations.
    """
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=False)
    for ax in axs:
        ax.plot([0, 1, 2], [0, 1, 0])
    axs.format(xlabel="Coordinate", ylabel="Response", suptitle="Tick cache")

    fig.canvas.draw()

    stats = fig._last_axis_tick_cache_stats
    assert stats["hits"] > 0
    assert stats["misses"] > 0
    assert stats["bypasses"] == 0
    assert stats["evictions"] == 0
    assert "_axis_tick_cache" not in fig.__dict__
    assert "_layout_transaction" not in fig.__dict__
    for ax in fig.axes:
        for axis in ax._axis_map.values():
            assert "_update_ticks" not in axis.__dict__


def test_tick_cache_preserves_rendered_pixels():
    """
    Caching tick updates must produce the exact uncached raster output.
    """

    def _draw(disable):
        fig, axs = uplt.subplots(nrows=2, ncols=2, share=False)
        x = np.linspace(0, 2 * np.pi, 100)
        for index, ax in enumerate(axs):
            ax.plot(x, np.sin(x + index))
        axs.format(
            xlabel="Coordinate",
            ylabel="Response",
            suptitle="Pixel comparison",
            grid=True,
        )
        fig._disable_axis_tick_cache = disable
        fig._disable_layout_extent_cache = disable
        fig.canvas.draw()
        return np.asarray(fig.canvas.buffer_rgba()).copy()

    expected = _draw(True)
    actual = _draw(False)

    assert np.array_equal(actual, expected)


@pytest.mark.parametrize("kind", ("log", "date", "categorical", "shared"))
def test_layout_caches_preserve_specialized_tick_pixels(kind):
    """
    Built-in non-linear, unit-aware, categorical, and shared ticks stay exact.
    """

    def _draw(disable):
        if kind == "shared":
            fig, axs = uplt.subplots(ncols=2, share=True)
        else:
            fig, ax = uplt.subplots()
            axs = [ax]
        if kind == "log":
            axs[0].semilogx([1, 10, 100, 1000], [0, 1, 0, 1])
        elif kind == "date":
            dates = [datetime.date(2025, 1, day) for day in range(1, 8)]
            axs[0].plot(dates, np.arange(len(dates)))
        elif kind == "categorical":
            axs[0].bar(["alpha", "beta", "gamma"], [1, 3, 2])
        else:
            for index, ax in enumerate(axs):
                ax.plot([0, 1, 2], np.asarray([0, 1, 0]) + index)
        fig._disable_axis_tick_cache = disable
        fig._disable_layout_extent_cache = disable
        fig.canvas.draw()
        return np.asarray(fig.canvas.buffer_rgba()).copy()

    expected = _draw(True)
    actual = _draw(False)

    assert np.array_equal(actual, expected)


def test_layout_caches_bypass_non_cartesian_axes():
    """
    Projection-specific tick and bbox implementations use their native paths.
    """
    fig, ax = uplt.subplots(proj="polar")
    ax.plot(np.linspace(0, 2 * np.pi, 20), np.linspace(0, 1, 20))

    fig.canvas.draw()

    stats = fig._last_axis_tick_cache_stats
    assert stats["bypasses"] > 0
    assert fig._last_layout_extent_stats == {"hits": 0, "misses": 0}


def test_tick_cache_invalidates_changed_axis_geometry():
    """
    Limits and pixel geometry are part of the draw-local cache key.
    """
    fig, ax = uplt.subplots()
    axis = ax.xaxis
    with _AxisTickCache(fig) as cache:
        axis._update_ticks()
        axis._update_ticks()
        assert (cache.hits, cache.misses) == (1, 1)

        ax.set_xlim(0, 10)
        axis._update_ticks()
        assert (cache.hits, cache.misses) == (1, 2)

        position = ax.get_position()
        ax.set_position(
            [position.x0, position.y0, 0.5 * position.width, position.height]
        )
        axis._update_ticks()
        assert (cache.hits, cache.misses) == (1, 3)

        ax.set_position(position)
        axis._update_ticks()
        assert (cache.hits, cache.misses) == (2, 3)


def test_tick_cache_bypasses_custom_tickers():
    """
    Unknown locator and formatter implementations may have stateful calls.
    """

    class CustomFormatter(mticker.Formatter):
        def __call__(self, value, pos=None):
            return f"{value:g}"

    fig, ax = uplt.subplots()
    ax.xaxis.set_major_formatter(CustomFormatter())
    with _AxisTickCache(fig) as cache:
        ax.xaxis._update_ticks()
        ax.xaxis._update_ticks()

    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.bypasses == 2


def test_tick_cache_lru_is_bounded():
    """
    Cycling through many geometries must not grow the draw-local cache.
    """
    fig, ax = uplt.subplots()
    with _AxisTickCache(fig) as cache:
        for stop in range(2, 9):
            ax.set_xlim(0, stop)
            ax.xaxis._update_ticks()
        states = cache._cache[ax.xaxis]

    assert len(states) == cache._MAX_STATES_PER_AXIS
    assert cache.evictions == 3


def test_tick_cache_includes_child_axes():
    """
    Colorbar child axes created during layout should share tick computations.
    """
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.colorbar("magma", loc="r")
    ax._add_queued_guides()
    child_axes = [
        child
        for child in fig._iter_axes(hidden=True, children=True)
        if child not in fig.axes
    ]
    assert child_axes

    with _AxisTickCache(fig) as cache:
        child_axes[0].xaxis._update_ticks()
        child_axes[0].xaxis._update_ticks()
        assert (cache.hits, cache.misses) == (1, 1)

    assert "_update_ticks" not in child_axes[0].xaxis.__dict__


def test_layout_transaction_restores_after_exception():
    """
    Temporary hooks and active stores must be cleaned up after draw failures.
    """
    fig, axs = uplt.subplots()
    axis = axs[0].xaxis

    with pytest.raises(RuntimeError, match="draw failed"):
        with _LayoutTransaction(fig) as transaction:
            assert fig._layout_transaction is transaction
            assert "_update_ticks" in axis.__dict__
            assert transaction.extents._active
            raise RuntimeError("draw failed")

    assert "_layout_transaction" not in fig.__dict__
    assert "_axis_tick_cache" not in fig.__dict__
    assert "_update_ticks" not in axis.__dict__
    assert not fig._layout_extent_store._active


def test_layout_invalidation_has_one_lifecycle():
    """
    Normal invalidation preserves reusable state; reset discards it.
    """
    fig, _ = uplt.subplots()
    fig.canvas.draw()
    store = fig._layout_extent_store

    fig._invalidate_layout()
    assert fig._layout_dirty
    assert fig._layout_initialized
    assert fig._layout_extent_store is store

    fig._invalidate_layout(reset=True)
    assert fig._layout_dirty
    assert not fig._layout_initialized
    assert "_layout_extent_store" not in fig.__dict__


def test_layout_extent_store_reuses_unmodified_axes():
    """
    A one-axes title edit should only remeasure that axes.
    """
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=False)
    axs.format(abc="a.")
    axs[1].plot([0, 1], [0, 1], label="Default axes legend")
    axs[1].legend()
    fig.canvas.draw()

    axs[0].format(title="Changed")
    fig.canvas.draw()

    stats = fig._last_layout_extent_stats
    assert stats == {"hits": 3, "misses": 1}


def test_layout_extent_store_preserves_incremental_pixels():
    """
    Relative outsets must exactly match an uncached geometry update.
    """

    def _draw(disable):
        fig, axs = uplt.subplots(nrows=2, ncols=2, share=False)
        for ax in axs:
            ax.plot([0, 1, 2], [0, 1, 0])
        axs.format(abc="a.")
        axs[1].plot([0, 1], [1, 0], label="Legend entry")
        axs[1].legend()
        fig._disable_layout_extent_cache = disable
        fig.canvas.draw()
        axs[0].format(title="A longer changed title")
        fig.canvas.draw()
        return np.asarray(fig.canvas.buffer_rgba()).copy()

    expected = _draw(True)
    actual = _draw(False)

    assert np.array_equal(actual, expected)


def test_layout_extent_store_tracks_subset_title_changes():
    """
    Shared subset-title state participates in axes extent cache keys.
    """
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=False)
    axs[0, :].format(title="First")
    fig.canvas.draw()

    axs[0, :].format(title="A substantially longer shared title")
    fig.canvas.draw()

    stats = fig._last_layout_extent_stats
    assert stats["misses"] >= 2


@pytest.mark.parametrize(
    "kwargs",
    (
        {"xgrid": True},
        {"gridcolor": "red"},
        {"xtickcolor": "red"},
        {"xticklabelcolor": "red"},
        {"xlabelcolor": "red"},
        {"xlinewidth": 1.5},
    ),
)
def test_paint_only_format_does_not_invalidate_layout(kwargs):
    """
    Paint-only Cartesian formatting should reuse the initialized layout.
    """
    fig, ax = uplt.subplots()
    fig.canvas.draw()
    assert not fig._layout_dirty

    ax.format(**kwargs)

    assert not fig._layout_dirty


@pytest.mark.parametrize(
    "kwargs",
    (
        {"title": "Changed"},
        {"xlabel": "Changed"},
        {"xticklabelsize": 14},
        {"xlim": (0, 2)},
        {"xlocator": 0.5},
    ),
)
def test_geometry_format_invalidates_layout(kwargs):
    """
    Text, tick geometry, limits, and locators must still invalidate layout.
    """
    fig, ax = uplt.subplots()
    fig.canvas.draw()
    assert not fig._layout_dirty

    ax.format(**kwargs)

    assert fig._layout_dirty


def test_figure_paint_only_format_does_not_invalidate_layout():
    """
    Figure-wide routing should preserve paint-only invalidation decisions.
    """
    fig, _ = uplt.subplots(ncols=2)
    fig.canvas.draw()

    fig.format(xgrid=True, ygrid=True)

    assert not fig._layout_dirty


def test_blit_manager_updates_without_full_redraw():
    """
    After capturing a background, updates should use draw_artist and blit.
    """
    fig, ax = uplt.subplots()
    (line,) = ax.plot([0, 1, 2], [0, 1, 0])
    manager = fig._blit_manager(line)
    assert isinstance(manager, _BlitManager)
    assert manager.supports_blit
    assert line.get_animated()

    manager.update()
    assert manager._background is not None

    original_draw = fig.canvas.draw
    original_blit = fig.canvas.blit
    fig.canvas.draw = MagicMock(wraps=original_draw)
    fig.canvas.blit = MagicMock(wraps=original_blit)
    line.set_ydata([1, 0, 1])
    assert manager.update()

    fig.canvas.draw.assert_not_called()
    fig.canvas.blit.assert_called_once()
    manager.close(redraw=False)
    assert not line.get_animated()


def test_blit_manager_matches_full_draw():
    """
    A blitted artist update should match a subsequent complete Agg draw.
    """
    fig, ax = uplt.subplots()
    (line,) = ax.plot([0.2, 1, 1.8], [0.2, 0.8, 0.2])
    ax.format(xlim=(0, 2), ylim=(0, 1))
    manager = fig._blit_manager(line)
    manager.update()

    line.set_ydata([0.8, 0.2, 0.8])
    manager.update()
    blitted = np.asarray(fig.canvas.buffer_rgba()).copy()

    manager.close(redraw=False)
    fig.canvas.draw()
    complete = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert np.array_equal(blitted, complete)


def test_blit_manager_savefig_includes_managed_artist():
    """
    Saving should temporarily restore normal artist drawing and z-order.
    """
    fig, ax = uplt.subplots()
    (line,) = ax.plot([0.2, 1, 1.8], [0.2, 0.8, 0.2], color="red", lw=4)
    ax.format(xlim=(0, 2), ylim=(0, 1))

    baseline_buffer = io.BytesIO()
    fig.savefig(baseline_buffer, format="png")
    baseline_buffer.seek(0)
    baseline = np.asarray(Image.open(baseline_buffer)).copy()

    manager = fig._blit_manager(line)
    manager.update()
    managed_buffer = io.BytesIO()
    fig.savefig(managed_buffer, format="png")
    managed_buffer.seek(0)
    managed = np.asarray(Image.open(managed_buffer)).copy()

    assert np.array_equal(managed, baseline)
    assert line.get_animated()
    manager.close(redraw=False)


def test_blit_manager_invalidates_on_resize():
    """
    Resize events must discard pixel-sized background caches.
    """
    fig, ax = uplt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    manager = fig._blit_manager(line)
    manager.update()
    assert manager._background is not None

    manager._on_resize(None)

    assert manager._background is None
    manager.close(redraw=False)


def test_blit_manager_falls_back_for_unsupported_canvas():
    """
    Non-blitting canvases should retain normal artists and request idle draws.
    """
    fig, ax = uplt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    canvas = FigureCanvasBase(fig)
    canvas.draw_idle = MagicMock()
    manager = _BlitManager(canvas, [line])

    assert not manager.supports_blit
    assert not line.get_animated()
    assert not manager.update()
    canvas.draw_idle.assert_called_once()
    manager.close(redraw=False)


def test_blit_manager_rejects_artist_from_another_figure():
    fig1, _ = uplt.subplots()
    _fig2, ax2 = uplt.subplots()
    (line,) = ax2.plot([0, 1], [0, 1])

    with pytest.raises(RuntimeError, match="must belong"):
        fig1._blit_manager(line)


def test_selective_draw_full_layer_matches_normal_draw():
    """Splitting a full draw into static and axes layers must preserve pixels."""
    fig, axs = uplt.subplots(ncols=2)
    for index, ax in enumerate(axs):
        ax.plot([0, 0.5, 1], [0.2, 0.8 - 0.1 * index, 0.3])
        ax.format(xlabel=f"x {index}", ylabel=f"y {index}", title=f"axis {index}")
    fig.format(suptitle="Layer fidelity")
    manager = fig._selective_draw_manager

    with manager.save_context():
        fig.canvas.draw()
        normal = np.asarray(fig.canvas.buffer_rgba()).copy()
    fig.canvas.draw()
    layered = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert np.array_equal(layered, normal)


@pytest.mark.parametrize("overlay", ("text", "patch"))
def test_selective_draw_falls_back_for_overlapping_figure_artist(overlay):
    """Figure-level overlays must retain their normal ordering above axes."""
    fig, axs = uplt.subplots(ncols=2)
    for ax in axs:
        ax.plot([0, 1], [0.2, 0.8], lw=5)
    if overlay == "text":
        fig.text(0.32, 0.5, "OVERLAY", fontsize=28, zorder=20)
    else:
        from matplotlib.patches import Rectangle

        artist = Rectangle(
            (0.2, 0.25),
            0.3,
            0.5,
            transform=fig.transFigure,
            color="red",
            alpha=0.35,
            zorder=20,
        )
        fig.add_artist(artist)
    fig.canvas.draw()
    manager = fig._selective_draw_manager

    with manager.save_context():
        fig.canvas.draw()
        normal = np.asarray(fig.canvas.buffer_rgba()).copy()
    fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert manager._cache_mode is None
    assert np.array_equal(retained, normal)


@pytest.mark.parametrize("ncols", (1, 2))
def test_selective_draw_defers_cache_until_after_initial_display(ncols):
    """The first display should have no retained-layer setup overhead."""
    fig, _axs = uplt.subplots(ncols=ncols)
    for ax in fig.axes:
        ax.plot([0, 1], [0, 1])
    manager = fig._selective_draw_manager

    fig.canvas.draw()
    assert manager._cache_mode is None
    assert manager._full_draw_count == 0

    fig.canvas.draw()
    assert manager._cache_mode == "suffix"
    assert manager._full_draw_count == 1


def test_selective_draw_redraws_only_changed_axes():
    """A paint-only line update should bypass every unchanged axes."""
    fig, axs = uplt.subplots(ncols=2)
    lines = [ax.plot([0, 0.5, 1], [0.2, 0.8, 0.3])[0] for ax in axs]
    fig.canvas.draw()
    fig.canvas.draw()  # Prime retained axes layers after the initial display.
    manager = fig._selective_draw_manager
    unchanged_draw = axs[1].draw
    axs[1].draw = MagicMock(wraps=unchanged_draw)

    lines[0].set_ydata([0.8, 0.2, 0.7])
    fig.canvas.draw()

    assert manager._selective_draw_count == 1
    axs[1].draw.assert_not_called()


def test_selective_draw_multi_axes_suffix_matches_complete_draw():
    """Each dirty axes should redraw only its exact artist suffix."""
    fig, axs = uplt.subplots(ncols=2)
    x = np.linspace(0, 2 * np.pi, 500)
    lines = []
    for index, ax in enumerate(axs):
        ax.scatter(x[::20], np.cos(x[::20]), s=6, zorder=1)
        lines.append(ax.plot(x, np.sin(x + index), zorder=2)[0])
        ax.format(title=f"Axis {index}", grid=True)
    fig.canvas.draw()
    fig.canvas.draw()
    manager = fig._selective_draw_manager
    axis_draws = [ax.xaxis.draw for ax in axs]
    for ax, draw in zip(axs, axis_draws):
        ax.xaxis.draw = MagicMock(wraps=draw)

    lines[0].set_ydata(np.cos(x))
    fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert manager._cache_mode == "suffix"
    assert manager._selective_draw_count == 1
    for ax in axs:
        ax.xaxis.draw.assert_not_called()
    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()
    assert np.array_equal(retained, complete)


def test_selective_draw_multi_axes_suffix_updates_multiple_dirty_axes():
    """Simultaneous line changes should restore and redraw every dirty suffix."""
    fig, axs = uplt.subplots(ncols=2)
    x = np.linspace(0, 2 * np.pi, 500)
    lines = [ax.plot(x, np.sin(x + index))[0] for index, ax in enumerate(axs)]
    fig.canvas.draw()
    fig.canvas.draw()
    manager = fig._selective_draw_manager

    for index, line in enumerate(lines):
        line.set_ydata(np.cos(x + index))
    fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert manager._selective_draw_count == 1
    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()
    assert np.array_equal(retained, complete)


def test_selective_draw_multi_axes_uses_axes_mode_without_safe_suffixes():
    """A figure must not mix suffix and whole-axes retained layers."""
    fig, axs = uplt.subplots(ncols=2)
    axs[0].plot([0, 1], [0, 1])
    axs[1].scatter([0, 1], [1, 0])
    fig.canvas.draw()
    fig.canvas.draw()

    assert fig._selective_draw_manager._cache_mode == "axes"


def test_selective_draw_stays_fast_across_consecutive_frames():
    """Placeholder staleness must not force alternating full redraws."""
    fig, axs = uplt.subplots(ncols=2)
    x = np.linspace(0, 2 * np.pi, 100)
    line = axs[0].plot(x, np.sin(x))[0]
    axs[1].plot(x, np.cos(x))
    fig.canvas.draw()
    fig.canvas.draw()  # Prime retained axes layers after the initial display.
    manager = fig._selective_draw_manager

    for frame in range(4):
        line.set_ydata(np.sin(x + frame / 10))
        fig.canvas.draw()

    assert manager._selective_draw_count == 4
    assert manager._full_draw_count == 1


def test_selective_draw_single_axes_line_suffix_matches_complete_draw():
    """A retained line suffix should skip axes while preserving exact pixels."""
    fig, ax = uplt.subplots()
    x = np.linspace(0, 2 * np.pi, 200)
    ax.scatter(x[::8], np.cos(x[::8]), s=8, zorder=1)
    ax.plot(x, 0.4 * np.cos(x), color="orange", zorder=2)
    line = ax.plot(x, np.sin(x), color="cerulean", zorder=2)[0]
    ax.text(0.03, 0.96, "Annotation", transform=ax.transAxes, va="top", zorder=3.2)
    ax.format(title="Retained suffix", xlabel="x", ylabel="y", grid=True)
    fig.canvas.draw()
    manager = fig._selective_draw_manager
    axis_draw = ax.xaxis.draw
    ax.xaxis.draw = MagicMock(wraps=axis_draw)

    line.set_ydata(np.sin(x + 0.1))
    fig.canvas.draw()  # Prime the retained suffix on the first redraw.
    ax.xaxis.draw.reset_mock()
    for frame in range(4):
        line.set_ydata(np.sin(x + frame / 10))
        fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert manager._cache_mode == "suffix"
    assert manager._selective_draw_count == 4
    assert manager._full_draw_count == 1
    ax.xaxis.draw.assert_not_called()

    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()
    assert np.array_equal(retained, complete)


def test_selective_draw_single_axes_savefig_matches_unretained_output():
    """Saving must restore ordinary ordering after retained suffix updates."""
    fig, ax = uplt.subplots()
    line = ax.plot([0, 1, 2], [0.8, 0.2, 0.7], color="red", lw=3)[0]
    ax.format(xlim=(0, 2), ylim=(0, 1), title="Export fidelity")

    expected_buffer = io.BytesIO()
    fig.savefig(expected_buffer, format="png")
    expected_buffer.seek(0)
    expected = np.asarray(Image.open(expected_buffer)).copy()

    fig.canvas.draw()  # Prime the retained suffix after the initial save.
    line.set_ydata([0.2, 0.8, 0.3])
    fig.canvas.draw()
    line.set_ydata([0.8, 0.2, 0.7])
    fig.canvas.draw()
    assert fig._selective_draw_manager._selective_draw_count == 2

    retained_buffer = io.BytesIO()
    fig.savefig(retained_buffer, format="png")
    retained_buffer.seek(0)
    retained = np.asarray(Image.open(retained_buffer)).copy()

    assert np.array_equal(retained, expected)


def test_selective_draw_invalidates_on_dpi_change_without_resize():
    """Copied pixel regions must never survive a silent DPI change."""
    fig, ax = uplt.subplots()
    line = ax.plot([0, 1, 2], [0.2, 0.8, 0.3], lw=4)[0]
    fig.canvas.draw()
    fig.canvas.draw()
    manager = fig._selective_draw_manager
    assert manager._cache_safe

    fig.set_dpi(fig.dpi * 1.5)
    line.set_ydata([0.8, 0.2, 0.7])
    fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()
    assert np.array_equal(retained, complete)


def test_selective_draw_rejects_suffix_outside_damage_region():
    """Unclipped translucent suffix artists must not accumulate outside cache."""
    from matplotlib.patches import Rectangle

    fig, ax = uplt.subplots()
    x = np.linspace(0, 1, 100)
    line = ax.plot(x, x, zorder=2)[0]
    patch = Rectangle(
        (-0.2, 0.3),
        1.4,
        0.4,
        transform=ax.transAxes,
        clip_on=False,
        in_layout=False,
        alpha=0.2,
        color="red",
        zorder=3,
    )
    ax.add_patch(patch)
    fig.canvas.draw()
    manager = fig._selective_draw_manager

    for offset in (0.1, 0.2, 0.3):
        line.set_ydata(x + offset)
        fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert not manager._cache_safe
    assert manager._selective_draw_count == 0
    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()
    assert np.array_equal(retained, complete)


def test_selective_draw_does_not_recapture_during_pan_frames():
    """Changing views should not rebuild a cache discarded by the next motion."""
    fig, ax = uplt.subplots()
    line = ax.plot(np.linspace(0, 10, 1000), np.sin(np.linspace(0, 10, 1000)))[0]
    fig.canvas.draw()
    fig.canvas.draw()
    manager = fig._selective_draw_manager
    assert manager._cache_safe
    full_count = manager._full_draw_count

    for left in (1, 2, 3):
        ax.set_xlim(left, left + 5)
        fig.canvas.draw()

    assert manager._cache_mode is None
    assert manager._full_draw_count == full_count

    line.set_ydata(np.cos(np.linspace(0, 10, 1000)))
    fig.canvas.draw()  # Stable view primes retention once after navigation.
    line.set_ydata(np.sin(np.linspace(0, 10, 1000)))
    fig.canvas.draw()
    assert manager._selective_draw_count == 1


def test_selective_draw_retains_unchanged_three_axes_during_rotation():
    """A rotated 3D subplot should preserve exact pixels and distant axes."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, proj="3d", share=False)
    t = np.linspace(0, 6 * np.pi, 500)
    for index, ax in enumerate(axs):
        ax.plot(np.cos(t), np.sin(t), t + index)
    fig.canvas.draw()
    fig.canvas.draw()
    manager = fig._selective_draw_manager
    distant_draw = axs[-1].draw
    axs[-1].draw = MagicMock(wraps=distant_draw)

    axs[0].view_init(elev=35, azim=55, roll=5)
    fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert manager._selective_draw_count == 1
    axs[-1].draw.assert_not_called()
    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()
    assert np.array_equal(retained, complete)


def test_selective_draw_three_axes_rotation_falls_back_when_not_profitable():
    """Measuring a rotated extent must not slow down a two-axes figure."""
    fig, axs = uplt.subplots(ncols=2, proj="3d", share=False)
    for ax in axs:
        ax.plot([0, 1], [0, 1], [0, 1])
    fig.canvas.draw()
    fig.canvas.draw()
    manager = fig._selective_draw_manager

    axs[0].view_init(elev=40, azim=20)
    fig.canvas.draw()

    assert manager._selective_draw_count == 0
    assert manager._cache_mode is None


def test_selective_draw_axes_mode_handles_view_limit_changes():
    """Whole-axes retention should support 2D and geographic-style view changes."""
    fig, axs = uplt.subplots(ncols=3)
    for ax in axs:
        ax.scatter([0, 1, 2], [0, 1, 0])
    fig.canvas.draw()
    fig.canvas.draw()
    manager = fig._selective_draw_manager

    axs[0].set_xlim(0.25, 1.75)
    fig.canvas.draw()
    retained = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert manager._selective_draw_count == 1
    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()
    assert np.array_equal(retained, complete)


def test_three_d_interaction_preview_restores_exact_artist_state():
    """Dense preview artists and decorations must be completely reversible."""
    fig, ax = uplt.subplots(proj="3d")
    ax = fig.axes[0]
    t = np.linspace(0, 8 * np.pi, 5_000)
    line = ax.plot(np.cos(t), np.sin(t), t)[0]
    scatter = ax.scatter(np.cos(t), np.sin(t), t, s=np.linspace(1, 3, len(t)))
    values = np.linspace(-2, 2, 30)
    xx, yy = np.meshgrid(values, values)
    surface = ax.plot_surface(xx, yy, np.sin(xx * yy), rcount=30, ccount=30)
    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview
    line_data = tuple(np.asanyarray(array).copy() for array in line.get_data_3d())
    offsets = tuple(np.asanyarray(array).copy() for array in scatter._offsets3d)
    locators = tuple(
        (axis.get_major_locator(), axis.get_minor_locator())
        for axis in ax._axis_map.values()
    )
    grid = ax._draw_grid
    recipe = surface._ultraplot_lod_recipe
    assert recipe.proxy is None
    assert surface.axes is ax and surface in ax.collections

    assert preview.activate(ax)
    proxy = recipe.proxy
    assert len(line.get_data_3d()[0]) <= preview._line_limit + 2
    assert len(scatter._offsets3d[0]) <= preview._scatter_limit + 2
    assert surface.axes is ax and surface.get_visible()
    assert surface._ultraplot_navigation_hidden
    assert proxy.get_visible() and proxy.axes is ax
    assert ax._draw_grid is grid
    assert ax._ultraplot_navigation_hide_grid
    assert all(
        isinstance(axis.get_minor_locator(), mticker.NullLocator)
        for axis in ax._axis_map.values()
    )

    assert preview.deactivate(redraw=False)
    assert all(
        np.array_equal(expected, actual)
        for expected, actual in zip(line_data, line.get_data_3d())
    )
    assert all(
        np.array_equal(expected, actual)
        for expected, actual in zip(offsets, scatter._offsets3d)
    )
    assert surface.get_visible() and surface.axes is ax
    assert not hasattr(surface, "_ultraplot_navigation_hidden")
    assert not proxy.get_visible()
    assert proxy.axes is None
    assert ax._draw_grid is grid
    assert not hasattr(ax, "_ultraplot_navigation_hide_grid")
    assert all(
        axis.get_major_locator() is major and axis.get_minor_locator() is minor
        for axis, (major, minor) in zip(ax._axis_map.values(), locators)
    )


def test_three_d_interaction_preview_exports_full_quality():
    """Saving during rotation must temporarily restore the exact dense scene."""
    fig, ax = uplt.subplots(proj="3d")
    ax = fig.axes[0]
    t = np.linspace(0, 8 * np.pi, 5_000)
    line = ax.plot(np.cos(t), np.sin(t), t)[0]
    fig.canvas.draw()

    expected_buffer = io.BytesIO()
    fig.savefig(expected_buffer, format="png")
    expected_buffer.seek(0)
    expected = np.asarray(Image.open(expected_buffer)).copy()

    preview = fig._selective_draw_manager._navigation_preview
    assert preview.activate(ax)
    assert len(line.get_data_3d()[0]) < len(t)
    preview_buffer = io.BytesIO()
    fig.savefig(preview_buffer, format="png")
    preview_buffer.seek(0)
    exported = np.asarray(Image.open(preview_buffer)).copy()

    assert np.array_equal(exported, expected)
    assert preview._state is not None
    assert len(line.get_data_3d()[0]) < len(t)
    preview.deactivate(redraw=False)


def test_two_d_interaction_preview_restores_exact_artist_state():
    """Toolbar pan preview should reversibly reduce dense 2D artists."""
    fig, _ = uplt.subplots()
    ax = fig.axes[0]
    x = np.linspace(0, 100, 5_000)
    line = ax.plot(x, np.sin(x))[0]
    scatter = ax.scatter(x, np.cos(x), s=np.linspace(1, 3, len(x)))
    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview
    line_data = tuple(np.asanyarray(array).copy() for array in line.get_data())
    offsets = np.asanyarray(scatter.get_offsets()).copy()
    locators = tuple(
        (axis.get_major_locator(), axis.get_minor_locator())
        for axis in (ax.xaxis, ax.yaxis)
    )

    assert preview.activate(ax)
    assert len(line.get_xdata()) <= preview._line_limit + 2
    assert len(scatter.get_offsets()) <= preview._scatter_limit + 2
    assert isinstance(ax.xaxis.get_minor_locator(), mticker.NullLocator)
    assert isinstance(ax.yaxis.get_minor_locator(), mticker.NullLocator)

    assert preview.deactivate(redraw=False)
    assert all(
        np.array_equal(expected, actual)
        for expected, actual in zip(line_data, line.get_data())
    )
    assert np.array_equal(offsets, scatter.get_offsets())
    assert all(
        axis.get_major_locator() is major and axis.get_minor_locator() is minor
        for axis, (major, minor) in zip((ax.xaxis, ax.yaxis), locators)
    )


@pytest.mark.parametrize("projection", (None, "3d"))
def test_navigation_preview_rc_disables_approximation(projection):
    """The runtime rc setting should preserve exact interactive frames."""
    kwargs = {} if projection is None else {"proj": projection}
    fig, _ = uplt.subplots(**kwargs)
    ax = fig.axes[0]
    values = np.linspace(0, 10, 5_000)
    if projection is None:
        line = ax.plot(values, np.sin(values))[0]
    else:
        line = ax.plot(np.cos(values), np.sin(values), values)[0]

    def get_size():
        data = line.get_xdata() if projection is None else line.get_data_3d()[0]
        return len(data)

    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview

    with uplt.rc.context({"navigation.preview": False}):
        assert not preview.activate(ax)
        assert get_size() == len(values)

    assert preview.activate(ax)
    assert get_size() < len(values)
    with uplt.rc.context({"navigation.preview": False}):
        assert not preview.request_draw(fig.canvas.draw_idle)
        assert preview._state is None
        assert get_size() == len(values)


@pytest.mark.parametrize("projection", (None, "3d"))
def test_navigation_preview_preserves_updates_during_gesture(projection):
    """Release must not overwrite artist or locator changes made while active."""
    kwargs = {} if projection is None else {"proj": projection}
    fig, _ = uplt.subplots(**kwargs)
    ax = fig.axes[0]
    values = np.linspace(0, 10, 5_000)
    if projection is None:
        line = ax.plot(values, np.sin(values))[0]
        scatter = ax.scatter(values, np.cos(values), s=1)
        axes = (ax.xaxis, ax.yaxis)
    else:
        line = ax.plot(np.cos(values), np.sin(values), values)[0]
        scatter = ax.scatter(np.cos(values), np.sin(values), values, s=1)
        axes = tuple(ax._axis_map.values())
    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview
    assert preview.activate(ax)

    updated = np.linspace(0, 12, 6_000)
    if projection is None:
        line.set_data(updated, np.sin(updated))
        scatter.set_offsets(np.column_stack((updated, np.cos(updated))))
    else:
        line.set_data_3d(np.cos(updated), np.sin(updated), updated)
        scatter._offsets3d = (np.cos(updated), np.sin(updated), updated)
    locator = mticker.MaxNLocator(nbins=7)
    axes[0].set_major_locator(locator)
    line.set_color("red")
    if projection == "3d":
        ax.grid(False)

    assert preview.deactivate(redraw=False)
    line_size = (
        len(line.get_xdata()) if projection is None else len(line.get_data_3d()[0])
    )
    scatter_size = (
        len(scatter.get_offsets()) if projection is None else len(scatter._offsets3d[0])
    )
    assert line_size == scatter_size == len(updated)
    assert axes[0].get_major_locator() is locator
    assert line.get_color() == "red"
    if projection == "3d":
        assert not ax._draw_grid


def test_navigation_preview_preserves_partial_line_update():
    """Updating only y data must restore exact x data without losing new y data."""
    fig, _ = uplt.subplots()
    ax = fig.axes[0]
    values = np.linspace(0, 10, 5_000)
    line = ax.plot(values, np.sin(values))[0]
    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview
    assert preview.activate(ax)

    updated_y = np.cos(values)
    line.set_ydata(updated_y)
    assert preview.deactivate(redraw=False)
    assert np.array_equal(line.get_xdata(), values)
    assert np.array_equal(line.get_ydata(), updated_y)


def test_three_d_hidden_surface_stays_hidden_during_preview():
    """Navigation must not expose a surface hidden by the user."""
    fig, _ = uplt.subplots(proj="3d")
    ax = fig.axes[0]
    values = np.linspace(-2, 2, 30)
    xx, yy = np.meshgrid(values, values)
    surface = ax.plot_surface(xx, yy, np.sin(xx * yy), rcount=30, ccount=30)
    surface.set_visible(False)
    fig.canvas.draw()
    recipe = surface._ultraplot_lod_recipe
    preview = fig._selective_draw_manager._navigation_preview

    assert preview.activate(ax)
    assert not surface.get_visible() and surface in ax.collections
    assert recipe.proxy is None
    assert preview.deactivate(redraw=False)
    assert not surface.get_visible() and surface in ax.collections


def test_three_d_surface_preview_tracks_active_updates():
    """Surface visibility and style changes should reach the active proxy."""
    fig, _ = uplt.subplots(proj="3d")
    ax = fig.axes[0]
    values = np.linspace(-2, 2, 30)
    xx, yy = np.meshgrid(values, values)
    surface = ax.plot_surface(xx, yy, np.sin(xx * yy), rcount=30, ccount=30)
    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview
    assert preview.activate(ax)
    proxy = surface._ultraplot_lod_recipe.proxy

    surface.set_alpha(0.25)
    surface.set_facecolor("blue")
    surface.set_visible(False)
    fig.canvas.draw()
    assert proxy.get_alpha() == 0.25
    assert np.allclose(proxy._facecolor3d, [[0.0, 0.0, 1.0, 0.25]])
    assert not proxy.get_visible()

    assert preview.deactivate(redraw=False)
    assert surface.get_alpha() == 0.25
    assert np.allclose(surface._facecolor3d, [[0.0, 0.0, 1.0, 0.25]])
    assert not surface.get_visible()


def test_three_d_surface_geometry_change_disables_stale_proxy():
    """Changed surface geometry should fall back to the exact collection."""
    fig, _ = uplt.subplots(proj="3d")
    ax = fig.axes[0]
    values = np.linspace(-2, 2, 30)
    xx, yy = np.meshgrid(values, values)
    surface = ax.plot_surface(xx, yy, np.sin(xx * yy), rcount=30, ccount=30)
    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview
    assert preview.activate(ax)
    proxy = surface._ultraplot_lod_recipe.proxy

    surface.set_verts([np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.5]])])
    fig.canvas.draw()
    assert surface.get_visible()
    assert not proxy.get_visible()

    assert preview.deactivate(redraw=False)
    assert surface.get_visible() and surface in ax.collections


@pytest.mark.parametrize("projection", (None, "3d"))
def test_navigation_preview_tracks_mouse_press_and_release(projection):
    """Canvas callbacks should activate previews and always restore on release."""
    kwargs = {} if projection is None else {"proj": projection}
    fig, _ = uplt.subplots(**kwargs)
    ax = fig.axes[0]
    values = np.linspace(0, 10, 5_000)
    if projection is None:
        line = ax.plot(values, np.sin(values))[0]
        ax.set_navigate_mode("PAN")
        original_size = len(line.get_xdata())
    else:
        line = ax.plot(np.cos(values), np.sin(values), values)[0]
        original_size = len(line.get_data_3d()[0])
    fig.canvas.draw()
    x, y = ax.transAxes.transform((0.5, 0.5))

    MouseEvent("button_press_event", fig.canvas, x, y, button=1)._process()
    preview = fig._selective_draw_manager._navigation_preview
    assert preview._state is not None

    MouseEvent("button_release_event", fig.canvas, x, y, button=1)._process()
    assert preview._state is None
    size = len(line.get_xdata()) if projection is None else len(line.get_data_3d()[0])
    assert size == original_size


def test_navigation_preview_coalesces_fast_draw_idle_requests():
    """Rapid motion updates should present only the newest scheduled frame."""

    class TestTimer(TimerBase):
        def _timer_start(self):
            self.started = True

        def _timer_stop(self):
            self.started = False

    fig, ax = uplt.subplots()
    ax = fig.axes[0]
    values = np.linspace(0, 10, 5_000)
    ax.plot(values, np.sin(values))
    fig.canvas.draw()
    preview = fig._selective_draw_manager._navigation_preview
    assert preview.activate(ax)

    timers = []

    def new_timer(interval):
        timer = TestTimer(interval=interval)
        timers.append(timer)
        return timer

    fig.canvas.new_timer = new_timer
    draws = []
    cid = fig.canvas.mpl_connect("draw_event", lambda event: draws.append(event))
    fig.canvas.draw_idle()
    ax.set_xlim(1, 9)
    fig.canvas.draw_idle()

    assert len(timers) == 1
    assert not draws
    timers[0]._on_timer()
    # Agg draws synchronously; GUI backends enqueue the submitted idle draw.
    assert not preview._pacer._draw_requested
    assert preview._pacer._draw_pending or len(draws) == 1

    fig.canvas.mpl_disconnect(cid)
    preview.deactivate(redraw=False)


@pytest.mark.parametrize("kind", ("scatter", "low_line", "unclipped", "overlay"))
def test_selective_draw_single_axes_falls_back_when_suffix_is_unsafe(kind):
    """Single-axes retention requires a clipped line above the axes layer."""
    fig, ax = uplt.subplots()
    if kind == "scatter":
        artist = ax.scatter([0, 1], [0, 1])
    else:
        artist = ax.plot([0, 1], [0, 1], zorder=1 if kind == "low_line" else 2)[0]
        if kind == "unclipped":
            artist.set_clip_on(False)
        elif kind == "overlay":
            fig.text(0.5, 0.5, "Figure overlay", zorder=10)
    fig.canvas.draw()
    manager = fig._selective_draw_manager

    if kind == "scatter":
        artist.set_offsets([[0, 1], [1, 0]])
    else:
        artist.set_ydata([1, 0])
    fig.canvas.draw()

    assert manager._cache_mode is None
    assert manager._selective_draw_count == 0


@pytest.mark.parametrize("kind", ("line", "scatter"))
def test_selective_draw_matches_complete_data_draw(kind):
    """Retained line and collection updates must match a complete Agg draw."""
    fig, axs = uplt.subplots(ncols=2)
    axs[1].plot([0, 1], [1, 0])
    if kind == "line":
        artist = axs[0].plot([0, 0.5, 1], [0.2, 0.8, 0.3])[0]
    else:
        artist = axs[0].scatter([0, 0.5, 1], [0.2, 0.8, 0.3])
    fig.canvas.draw()
    fig.canvas.draw()  # Prime retained axes layers after the initial display.
    manager = fig._selective_draw_manager

    if kind == "line":
        artist.set_ydata([0.8, 0.2, 0.7])
    else:
        artist.set_offsets([[0, 0.8], [0.5, 0.2], [1, 0.7]])
    fig.canvas.draw()
    selective = np.asarray(fig.canvas.buffer_rgba()).copy()

    with manager.save_context():
        fig.canvas.draw()
        complete = np.asarray(fig.canvas.buffer_rgba()).copy()

    assert manager._selective_draw_count == 1
    assert np.array_equal(selective, complete)


@pytest.mark.parametrize("change", ("limits", "text", "structure"))
def test_selective_draw_falls_back_for_unsafe_changes(change):
    """Geometry, text, and artist-tree changes must retain full-draw semantics."""
    fig, axs = uplt.subplots(ncols=2)
    ax = axs[0]
    ax.plot([0, 1], [0, 1])
    axs[1].plot([0, 1], [1, 0])
    fig.canvas.draw()
    manager = fig._selective_draw_manager
    full_count = manager._full_draw_count

    if change == "limits":
        ax.set_xlim(-1, 2)
    elif change == "text":
        ax.set_title("Changed")
    else:
        ax.plot([0, 1], [1, 0])
    fig.canvas.draw()

    assert manager._selective_draw_count == 0
    assert manager._full_draw_count == full_count + (change != "limits")


def test_layout_array_no_crash():
    """
    Test that using layout_array with FuncAnimation does not crash.
    """
    layout = [[1, 1], [2, 3]]
    fig, axs = uplt.subplots(array=layout)

    def update(frame):
        for ax in axs:
            ax.clear()
            ax.plot(np.sin(np.linspace(0, 2 * np.pi) + frame / 10.0))

    ani = FuncAnimation(fig, update, frames=10)
    # The test passes if no exception is raised
    fig.canvas.draw()


def test_animation_save_only_tightens_first_frame(tmp_path):
    """
    Saving an animation should not rerun tight layout on every frame after the
    first saved frame, or frame geometry can shift between outputs.
    """
    matplotlib.use("Agg")
    state = np.random.RandomState(51423)

    fig, axs = uplt.subplots(nrows=1, ncols=2, width="14cm")
    mappables = []
    for ax in axs:
        m = ax.heatmap(state.rand(10, 10), cmap="dusk")
        ax.colorbar(m, loc="t", tickdir="out", label="Axes Colorbars")
        mappables.append(m)

    axs.format(
        abc="(a)",
        abcloc="ul",
        xlabel="xlabel",
        ylabel="ylabel",
        toplabels=("Left Axes", "Right Axes"),
        urtitle="1",
        suptitle="Test Animation",
    )

    auto_layout_calls = []
    original_auto_layout = fig.auto_layout

    def wrapped_auto_layout(*args, **kwargs):
        auto_layout_calls.append(kwargs.get("tight", None))
        return original_auto_layout(*args, **kwargs)

    fig.auto_layout = wrapped_auto_layout

    def update(frame):
        for m in mappables:
            m.set_array(state.rand(10, 10))
        axs.format(urtitle=f"{frame + 1}")
        return mappables

    ani = FuncAnimation(fig, update, frames=3, interval=150)
    ani.save(tmp_path / "test_animation.gif", writer="pillow")

    assert auto_layout_calls
    assert auto_layout_calls[0] is not False
    assert auto_layout_calls[1:] == [False] * (len(auto_layout_calls) - 1)


def test_selective_draw_region_covers_unclipped_stroke_overhang():
    """Thick unclipped strokes paint past the tight bbox and must not ghost."""
    fig, axs = uplt.subplots(ncols=2, figsize=(6, 3), tight=False)
    lines = []
    for index, ax in enumerate(axs):
        ax.plot([0, 1, 2], [0.2, 0.8, 0.3])
        ax.format(xlim=(0, 2), ylim=(0, 1))
        # Line2D.get_window_extent() ignores linewidth, so this paints well
        # outside the measured region it is captured with.
        lines.append(ax.plot([0, 2], [-3, 4], clip_on=False, color="red", lw=20)[0])
    for _ in range(3):
        fig.canvas.draw()
    manager = fig._selective_draw_manager
    assert manager._cache_mode == "axes"

    for value in (6.0, 1.5, 9.0, 0.5):
        lines[0].set_ydata([-value, value])
        fig.canvas.draw()
        retained = np.asarray(fig.canvas.buffer_rgba()).copy()

        with manager.save_context():
            fig.canvas.draw()
            complete = np.asarray(fig.canvas.buffer_rgba()).copy()
        assert np.array_equal(retained, complete)

        for _ in range(2):
            fig.canvas.draw()


def test_paint_only_format_flushes_pending_layout_changes():
    """format() must still pick up layout changes made through plain setters."""
    fig, axs = uplt.subplots(ncols=2, refwidth=1.8)
    for index, ax in enumerate(axs):
        ax.plot([0, 1, 2], [0.2, 0.8, 0.3])
    fig.canvas.draw()

    axs[0].set_ylabel("a very long y axis label")
    axs[0].format(xcolor="red")  # paint-only on its own
    assert fig._layout_dirty
    fig.canvas.draw()

    expected, expected_axs = uplt.subplots(ncols=2, refwidth=1.8)
    for index, ax in enumerate(expected_axs):
        ax.plot([0, 1, 2], [0.2, 0.8, 0.3])
    expected_axs[0].set_ylabel("a very long y axis label")
    expected_axs[0].format(xcolor="red")
    expected.canvas.draw()

    assert fig.get_size_inches() == pytest.approx(expected.get_size_inches())
    assert axs[0].get_position().bounds == pytest.approx(
        expected_axs[0].get_position().bounds
    )


def test_paint_only_format_keeps_layout_clean_when_nothing_pending():
    """A paint-only format() on a clean figure must not force a relayout."""
    fig, ax = uplt.subplots()
    ax.plot([0, 1, 2], [0.2, 0.8, 0.3])
    fig.canvas.draw()
    assert not fig._layout_dirty

    ax.format(xcolor="red")
    assert not fig._layout_dirty


def test_selective_draw_reuses_regions_for_unchanged_axes():
    """An unchanged axes must not repeat its tight bbox measurement."""
    fig, axs = uplt.subplots(ncols=2, nrows=2, refwidth=1.0)
    lines = [ax.plot([0, 1, 2], [0.2, 0.8, 0.3])[0] for ax in axs]
    for _ in range(4):
        fig.canvas.draw()

    calls = []
    for ax in axs:
        original = ax.get_tightbbox
        ax.get_tightbbox = MagicMock(wraps=original)
        calls.append(ax.get_tightbbox)

    fig.canvas.draw()
    assert not any(call.called for call in calls)

    manager = fig._selective_draw_manager
    # An unchanged axes resolves from the memo, which requires a usable
    # signature matching the stored one.
    for ax in axs:
        signature = manager._region_signature(ax)
        assert signature is not None
        assert manager._resolved_regions[ax][0] == signature

    # A changed axes must not be served from the memo. Which cache then supplies
    # the measurement is deliberately not asserted: the layout extent store can
    # legitimately satisfy it without a fresh Axes.get_tightbbox() call.
    lines[0].set_ydata([0.8, 0.2, 0.7])
    assert manager._region_signature(axs[0]) is None
    assert manager._region_signature(axs[1]) is not None


def test_regions_overlap_matches_exhaustive_comparison():
    """The sweep must agree with a direct all-pairs rectangle comparison."""
    from ultraplot._animation import _SelectiveDrawManager

    def exhaustive(regions):
        regions = tuple(regions)
        for index, left in enumerate(regions):
            for right in regions[index + 1 :]:
                overlap = mtransforms.Bbox.intersection(left, right)
                if overlap is not None and overlap.width > 0 and overlap.height > 0:
                    return True
        return False

    state = np.random.RandomState(0)
    for trial in range(400):
        count = state.randint(0, 8)
        if trial % 3 == 0:  # a single column keeps every x span open at once
            boxes = [
                mtransforms.Bbox.from_extents(0, index * 2, 10, index * 2 + width)
                for index, width in enumerate(state.randint(0, 3, count))
            ]
        else:
            boxes = [
                mtransforms.Bbox.from_extents(x0, y0, x0 + w, y0 + h)
                for x0, y0, w, h in state.randint(0, 6, (count, 4))
            ]
        assert _SelectiveDrawManager._regions_overlap(boxes) == exhaustive(boxes)
