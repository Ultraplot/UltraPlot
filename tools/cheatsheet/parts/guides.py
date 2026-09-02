#!/usr/bin/env python3
"""
Colorbar, legend, and statistical-indicator figures.
"""

from __future__ import annotations

import numpy as np

import ultraplot as uplt

from common import save, use_style


def guides():
    """
    Outer guides on three sides plus an inset legend, all on one axes.

    Each outer guide takes its own gridspec slot, which is why the map itself
    stays exactly as wide as it started.
    """
    state = np.random.default_rng(51423)
    y, x = np.mgrid[0:40, 0:40]
    field = np.sin(x / 6) * np.cos(y / 7) + state.normal(0, 0.08, (40, 40))

    fig, ax = uplt.subplots(figwidth="104mm", figheight="50mm")
    mesh = ax.pcolormesh(field, cmap="batlow", levels=9)
    lines = ax.plot(
        np.linspace(0, 39, 40),
        np.column_stack(
            [
                12 + 8 * np.sin(np.linspace(0, 6, 40)),
                26 + 6 * np.cos(np.linspace(0, 6, 40)),
            ]
        ),
        labels=["first", "second"],
        lw=1.4,
        cycle=("white", "gray2"),
    )
    ax.colorbar(
        mesh, loc="r", label="loc='r'", width="3mm", labelsize=5.5, ticklabelsize=5
    )
    ax.colorbar(
        mesh,
        loc="b",
        label="loc='b'",
        width="3mm",
        length=0.7,
        labelsize=5.5,
        ticklabelsize=5,
    )
    ax.legend(
        lines,
        loc="t",
        ncols=2,
        frame=False,
        fontsize=5.5,
        title="loc='t'",
        titlefontsize=5.5,
    )
    ax.legend(
        lines,
        loc="ul",
        ncols=1,
        fontsize=5.2,
        title="loc='ul'",
        titlefontsize=5.2,
        framealpha=0.85,
    )
    ax.format(xticks=[], yticks=[], grid=False)
    save(fig, "guides.png")


def semantic():
    """
    The three legends that describe an encoding rather than an artist.
    """
    state = np.random.default_rng(7)
    size = state.uniform(8, 120, 90)
    value = state.uniform(0, 1, 90)
    fig, ax = uplt.subplots(figwidth="104mm", figheight="44mm")
    ax.scatter(
        state.normal(size=90),
        state.normal(size=90),
        s=size,
        c=value,
        cmap="viko",
        alpha=0.75,
        lw=0,
    )
    ax.numlegend(
        levels=[0, 0.25, 0.5, 0.75, 1.0],
        cmap="viko",
        fmt="{:.2f}",
        loc="r",
        ncols=1,
        title="numlegend",
        fontsize=5.2,
        titlefontsize=5.4,
        frame=False,
    )
    ax.sizelegend(
        [10, 60, 120],
        labels=["S", "M", "L"],
        loc="b",
        ncols=3,
        title="sizelegend",
        fontsize=5.2,
        titlefontsize=5.4,
        frame=False,
    )
    ax.format(xticks=[], yticks=[], grid=False)
    save(fig, "semantic.png")


def statistics():
    """
    One dataset of raw samples, four ways of showing its spread.
    """
    state = np.random.default_rng(51423)
    x = np.linspace(0, 10, 20)
    runs = np.sin(x)[None, :] + state.normal(0, 0.35, (120, x.size))

    fig, axs = uplt.subplots(
        ncols=4,
        figwidth="120mm",
        figheight="30mm",
        wspace="3mm",
        share=True,
    )
    axs[0].plot(x, runs, mean=True, bars=True, barcolor="gray7", barlw=0.6, lw=1.4)
    axs[1].plot(x, runs, mean=True, boxes=True, boxcolor="gray7", boxlw=2.0, lw=1.4)
    axs[2].plot(x, runs, mean=True, shadestd=1, lw=1.4)
    axs[3].plot(x, runs, mean=True, shadestd=1, fadepctile=(5, 95), lw=1.4)
    for ax, label in zip(
        axs,
        ("bars=True", "boxes=True", "shadestd=1", "shade + fadepctile"),
    ):
        ax.format(
            title=label,
            titlesize=5.4,
            titleloc="l",
            titlepad=1.5,
            xticks=[],
            yticks=[],
            grid=False,
        )
    save(fig, "statistics.png")


def main():
    use_style()
    guides()
    semantic()
    statistics()


if __name__ == "__main__":
    main()
