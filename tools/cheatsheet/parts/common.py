#!/usr/bin/env python3
"""
Shared style and helpers for the cheatsheet figure parts.

Each part script renders one asset with UltraPlot and drops it in ``assets/``.
The Typst document is what assembles them, so nothing here knows about page
layout — only about drawing one small, self-contained figure well.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import numpy as np

import ultraplot as uplt

#: Where the rendered assets land, relative to the cheatsheet directory.
ASSETS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
)

#: Section rails, sampled along ``batlow`` so the sheet is colored by the thing
#: it documents. Kept in step with the palette in ``cheatsheet.typ``.
RAILS = ["#011959", "#144d62", "#3c6d56", "#828231", "#b0455a"]

INK = "#101720"
INK_SOFT = "#47535f"
INK_FAINT = "#7e8c99"
PANEL = "#ffffff"
SUNK = "#eef1f5"
RULE = "#c9d2dc"
ACCENT = "#3b638c"

#: Assets are rendered at this resolution. Typst scales them down to their box,
#: so oversampling keeps small strokes crisp in print.
DPI = 300


def use_style(fontsize=7):
    """
    Apply the cheatsheet's drawing style to the global rc state.
    """
    uplt.rc.update(
        {
            "font.size": fontsize,
            "figure.facecolor": PANEL,
            "savefig.facecolor": PANEL,
            "axes.facecolor": PANEL,
            "text.color": INK,
            "axes.labelcolor": INK_SOFT,
            "tick.labelcolor": INK_SOFT,
            "axes.edgecolor": RULE,
            "axes.linewidth": 0.6,
            "tick.width": 0.5,
            "tick.len": 2.0,
            "grid.alpha": 0.25,
            "cycle": "colorblind",
        }
    )


def save(fig, name, *, dpi=DPI, transparent=False):
    """
    Write one asset and report it, so ``build.py`` output reads as a manifest.
    """
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.save(path, dpi=dpi, transparent=transparent)
    uplt.close(fig)
    print(f"  {os.path.relpath(path, os.path.dirname(ASSETS))}")
    return path


# ---------------------------------------------------------------- icons
#
# One visual language for every thumbnail. Icons are read at a glance, often at
# 10 mm, so they share a small vocabulary of shapes and a fixed set of colour
# roles: the reader learns the vocabulary once and then only sees what differs
# between two commands.

#: Deterministic sample data, built once so two icons of the same shape are
#: literally the same data.
_STATE = np.random.default_rng(51423)

#: A single smooth wave: the shape for anything that draws a line.
WAVE_X = np.linspace(0, 2 * np.pi, 80)
WAVE = np.sin(WAVE_X)

#: Three phase-shifted waves, for anything that draws several series.
WAVES = np.column_stack([np.sin(WAVE_X + shift) for shift in (0, 0.9, 1.8)])

#: A point cloud, for scatter-shaped commands.
CLOUD = _STATE.normal(size=(60, 2))

#: Five categories, for bar-shaped commands. Sorted so the shape reads as a
#: ranking rather than as noise.
CATEGORIES = list("ABCDE")
VALUES = np.sort(_STATE.uniform(0.35, 1.0, 5))[::-1]

#: Signed values, for the commands that colour by sign.
SIGNED = np.array([0.9, 0.45, -0.3, -0.75, 0.6])

#: Raw samples, for the commands that reduce a distribution.
SAMPLES = np.sin(WAVE_X)[None, :] + _STATE.normal(0, 0.3, (80, WAVE_X.size))

#: Colour roles. One accent for a single series, the qualitative cycle for
#: several, a sequential map for magnitude and a diverging one for sign.
ICON_LINE = ACCENT
ICON_STRUCTURE = "gray6"
ICON_SEQUENTIAL = "batlow"
ICON_DENSITY = "fire"
ICON_DIVERGING = "roma"

#: Stroke and marker sizes that survive being scaled to 10 mm.
ICON_LW = 1.7
ICON_MS = 11.0

#: Data margin inside an icon. Small, so the drawing reaches the edges: the
#: tile on the page supplies the frame, and empty padding inside it just makes
#: the icon look smaller than the space it occupies.
ICON_MARGIN = 0.035


def smooth_field(n=48, scale=1.0, ripple=0.35):
    """
    A smooth two-dimensional field: two peaks and two troughs, no noise.

    Noise makes a contour icon look like a maze at thumbnail size, so the field
    the 2D icons share is deliberately clean. ``ripple`` adds a second, finer
    wave that gives the filled commands more to show; the line commands pass
    ``ripple=0`` and get plain nested rings.
    """
    y, x = np.mgrid[0:n, 0:n]
    return scale * (
        np.sin(2 * np.pi * x / n) * np.cos(2 * np.pi * y / n)
        + ripple * np.sin(4 * np.pi * y / n)
    )


def peak_field(n=64):
    """
    One broad peak and one shallow dip: the archetypal contour shape.

    A periodic field contoured at icon size reads as a maze; concentric rings
    around a peak read as a contour map at a glance.
    """
    axis = np.linspace(-2.2, 2.2, n)
    x, y = np.meshgrid(axis, axis)
    return np.exp(-((x + 0.5) ** 2 + (y - 0.3) ** 2) / 1.1) - 0.55 * np.exp(
        -((x - 1.2) ** 2 + (y + 1.1) ** 2) / 0.5
    )


def rotational_field(n=16, extent=2.0):
    """
    A rotation, for the vector-field commands: x, y, u, v.
    """
    axis = np.linspace(-extent, extent, n)
    x, y = np.meshgrid(axis, axis)
    return x, y, -y, x


@contextmanager
def without_new_text(ax):
    """
    Drop only the text a command adds, leaving the axes' own titles alone.

    Some commands label themselves — the ribbon names its periods, the radar
    names its spokes — and at icon size those labels are noise. Removing every
    text would take UltraPlot's own title artists with it, and the next
    ``format`` call would then fail on them.
    """
    before = {id(text) for text in ax.texts}
    yield
    for text in list(ax.texts):
        if id(text) not in before:
            text.remove()


def bare(ax, **kwargs):
    """
    Strip an axes to its data: no ticks, no labels, thin frame.

    Icons are read at a glance and at thumbnail size, so anything that isn't
    the shape of the plot type is noise.
    """
    kwargs.setdefault("linewidth", 0.5)
    ax.format(
        xticks=[],
        yticks=[],
        xlabel="",
        ylabel="",
        title="",
        grid=False,
        **kwargs,
    )
    return ax
