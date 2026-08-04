from unittest.mock import MagicMock

import datetime
import io
import matplotlib
import numpy as np
import pytest
from matplotlib import ticker as mticker
from matplotlib.animation import FuncAnimation
from matplotlib.backend_bases import FigureCanvasBase
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
    assert manager._cache_mode == ("suffix" if ncols == 1 else "axes")
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
