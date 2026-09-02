#!/usr/bin/env python3
"""
Layout figures: axis sharing, mosaic grids, title and panel-letter placement.
"""

from __future__ import annotations

import numpy as np

import ultraplot as uplt

from common import ACCENT, INK_FAINT, RULE, SUNK, bare, save, use_style


def sharing():
    """
    The same four panels with sharing off and on.

    Sharing is a figure-level setting, so this is two figures rather than one:
    the Typst page sets them side by side. It opens the sheet because it is the
    feature that changes what a multi-panel figure looks like before you have
    formatted anything.
    """
    state = np.random.default_rng(51423)
    x = np.linspace(0, 10, 120)
    series = [
        np.sin(x + shift) * scale
        for shift, scale in zip(range(4), (1.0, 0.8, 1.2, 0.9))
    ]

    for share, name in ((False, "sharing_off.png"), (True, "sharing_on.png")):
        fig, axs = uplt.subplots(
            nrows=2,
            ncols=2,
            figwidth="60mm",
            figheight="42mm",
            share=share,
            span=share,
        )
        for index, ax in enumerate(axs):
            ax.plot(x, series[index] + state.normal(0, 0.03, x.size), lw=1)
        axs.format(
            xlim=(0, 10),
            ylim=(-1.35, 1.35),
            xlabel="time (s)",
            ylabel="signal (mV)",
            labelsize=5.5,
            ticklabelsize=4.8,
            grid=False,
        )
        save(fig, name)


def mosaic():
    """
    A layout array rendered as the grid it produces.
    """
    fig, axs = uplt.subplots(
        [[1, 1, 2], [3, 4, 2]],
        figwidth="60mm",
        figheight="32mm",
        hspace="2mm",
        wspace="2mm",
    )
    for index, ax in enumerate(axs, start=1):
        bare(ax, facecolor=SUNK, edgecolor=RULE)
        ax.text(
            0.5,
            0.5,
            str(index),
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=9,
            color=INK_FAINT,
            family="monospace",
        )
    save(fig, "mosaic.png")


def titles():
    """
    Every title and panel-letter slot, filled with its own keyword.
    """
    fig, ax = uplt.subplots(figwidth="60mm", figheight="32mm")
    bare(ax, facecolor=SUNK, edgecolor=RULE)
    ax.format(
        abc="a.",
        abcloc="ul",
        abcsize=7,
        title="title",
        titlesize=6.5,
        ltitle="ltitle",
        rtitle="rtitle",
        titlepad=2,
    )
    for label, (px, py, ha, va) in {
        "ultitle": (0.035, 0.93, "left", "top"),
        "urtitle": (0.965, 0.93, "right", "top"),
        "lltitle": (0.035, 0.07, "left", "bottom"),
        "lrtitle": (0.965, 0.07, "right", "bottom"),
    }.items():
        ax.text(
            px,
            py,
            label,
            transform=ax.transAxes,
            ha=ha,
            va=va,
            fontsize=6,
            family="monospace",
            color=INK_FAINT,
        )
    ax.text(
        0.5,
        0.45,
        "abc='a.'  abcloc='ul'",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=6,
        family="monospace",
        color=ACCENT,
    )
    save(fig, "titles.png")


def panels():
    """
    An axes with outer panels and an inset, showing what each slot costs.
    """
    fig, ax = uplt.subplots(figwidth="66mm", figheight="36mm")
    state = np.random.default_rng(1)
    data = state.normal(size=(300, 2))
    ax.scatter(data[:, 0], data[:, 1], s=3, alpha=0.5, color=ACCENT)
    right = ax.panel_axes("r", width="7mm")
    top = ax.panel_axes("t", width="7mm")
    right.histh(data[:, 1], bins=18, color=ACCENT, alpha=0.6, lw=0)
    top.hist(data[:, 0], bins=18, color=ACCENT, alpha=0.6, lw=0)
    inset = ax.inset_axes([0.03, 0.03, 0.3, 0.3], zoom=False)
    inset.scatter(data[:, 0], data[:, 1], s=1, alpha=0.5, color=ACCENT)
    for child in (right, top, inset):
        bare(child)
    ax.format(xlabel="x", ylabel="y", labelsize=5.5, ticklabelsize=4.8, grid=False)
    save(fig, "panels.png")


def main():
    use_style()
    sharing()
    mosaic()
    titles()
    panels()


if __name__ == "__main__":
    main()
