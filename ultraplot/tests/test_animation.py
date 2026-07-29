from unittest.mock import MagicMock

import io
import matplotlib
import numpy as np
import pytest
from matplotlib.animation import FuncAnimation
from matplotlib.backend_bases import FigureCanvasBase
from PIL import Image

import ultraplot as uplt
from ultraplot._animation import _BlitManager


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
