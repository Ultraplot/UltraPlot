from unittest.mock import MagicMock

import matplotlib
import numpy as np
import pytest
from matplotlib.animation import FuncAnimation

import ultraplot as uplt


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
