#!/usr/bin/env python3
"""
Color figures: the bundled colormaps, the property cycles, and the perceptual
check that tells you whether a map is safe to use.

The colormap tables come from ``ultraplot.demos.CMAP_TABLE``, the same source
``uplt.show_cmaps()`` draws from, so the sheet cannot drift from what is
actually registered.
"""

from __future__ import annotations

import numpy as np

import ultraplot as uplt
from ultraplot.demos import CMAP_TABLE, CYCLE_TABLE

import os

from common import ACCENT, ASSETS, INK, INK_FAINT, save, use_style

GRADIENT = np.linspace(0, 1, 512)[None, :]

#: Families to print, and the label to print them under. Everything registered
#: is listed in CMAP_TABLE; these are the families worth a swatch on one page.
FAMILIES = {
    "uplt": ("UltraPlot", ["UltraPlot sequential", "UltraPlot diverging"]),
    "scientific": (
        "Scientific colour maps (Crameri)",
        [
            "Scientific colour maps sequential",
            "Scientific colour maps diverging",
            "Scientific colour maps cyclic",
        ],
    ),
    "cmocean": (
        "cmOcean",
        ["cmOcean sequential", "cmOcean diverging", "cmOcean cyclic"],
    ),
    "brewer": (
        "ColorBrewer 2.0",
        ["ColorBrewer2.0 sequential", "ColorBrewer2.0 diverging"],
    ),
    "other": (
        "Matplotlib, seaborn, SciVisColor",
        [
            "Matplotlib sequential",
            "Matplotlib cyclic",
            "Seaborn sequential",
            "Seaborn diverging",
            "Other sequential",
            "Other diverging",
            "Grayscale",
        ],
    ),
}


def _swatches(names, path, *, ncols=2, labelwidth=0.34, rowmm=3.3):
    """
    Draw a table of colormap swatches with their names.
    """
    nrows = int(np.ceil(len(names) / ncols))
    pitch = 1 / nrows
    fig = uplt.figure(figwidth="86mm", figheight=f"{nrows * rowmm:.1f}mm")
    ax = fig.subplot()
    ax.format(xticks=[], yticks=[], grid=False, linewidth=0, xlim=(0, 1), ylim=(0, 1))
    ax.patch.set_visible(False)
    for index, name in enumerate(names):
        column, row = divmod(index, nrows)
        left = column / ncols + labelwidth / ncols
        width = (1 / ncols) * (1 - labelwidth) * 0.93
        bottom = 1 - (row + 0.85) * pitch
        bar = ax.inset_axes(
            [left, bottom, width, pitch * 0.66],
            transform=ax.transAxes,
            zoom=False,
        )
        bar = bar[0] if hasattr(bar, "__len__") else bar
        bar.imshow(GRADIENT, aspect="auto", cmap=name)
        bar.format(xticks=[], yticks=[], grid=False, linewidth=0.3)
        ax.text(
            left - 0.012,
            bottom + pitch * 0.33,
            name,
            transform=ax.transAxes,
            ha="right",
            va="center",
            fontsize=5.4,
            family="monospace",
            color=INK,
        )
    save(fig, path)


def colormaps():
    """
    One swatch table per bundled family.
    """
    for key, (_, categories) in FAMILIES.items():
        names = []
        for category in categories:
            names.extend(CMAP_TABLE[category])
        # Three columns keeps even the big families to a short block.
        ncols = 2 if len(names) <= 12 else 3
        _swatches(names, f"cmaps_{key}.png", ncols=ncols)


def cycles():
    """
    The registered property cycles, as their actual colors.
    """
    names = [
        name
        for category in (
            "Matplotlib stylesheets",
            "Other qualitative",
            "ColorBrewer2.0 qualitative",
        )
        for name in CYCLE_TABLE[category]
    ][:11]
    fig = uplt.figure(figwidth="86mm", figheight=f"{len(names) * 3.4:.0f}mm")
    ax = fig.subplot()
    ax.format(
        xticks=[],
        yticks=[],
        grid=False,
        linewidth=0,
        xlim=(0, 12),
        ylim=(0, len(names)),
    )
    ax.patch.set_visible(False)
    for row, name in enumerate(names):
        colors = uplt.get_colors(name)
        y = len(names) - row - 1
        for index, color in enumerate(colors[:12]):
            ax.bar(index + 0.5, 0.62, bottom=y + 0.2, width=0.92, color=color, lw=0)
        ax.text(
            -0.35,
            y + 0.5,
            name,
            ha="right",
            va="center",
            fontsize=5.4,
            family="monospace",
            color=INK,
        )
    save(fig, "cycles.png")


def luminance():
    """
    Why perceptual uniformity is checkable: luminance against position.
    """
    fig, ax = uplt.subplots(figwidth="58mm", figheight="34mm")
    position = np.linspace(0, 1, 128)
    for name, color, dash in (
        ("batlow", ACCENT, "-"),
        ("fire", "#b6394f", "-"),
        ("viridis", "#3c6d56", "-"),
        ("jet", INK_FAINT, "--"),
    ):
        cmap = uplt.Colormap(name)
        lum = [uplt.to_xyz(cmap(value), space="hcl")[2] for value in position]
        ax.plot(position, lum, color=color, lw=1.2, ls=dash, label=name)
    ax.format(
        xlim=(0, 1),
        ylim=(0, 105),
        xticks=[],
        yticks=[0, 50, 100],
        ylabel="luminance",
        labelsize=6,
        ticklabelsize=5.5,
        grid=True,
    )
    ax.legend(loc="lr", ncols=1, frame=False, fontsize=5.6, handlelength=1.3)
    save(fig, "luminance.png")


def norms():
    """
    The same field under a continuous norm, discrete levels, and a pinned
    diverging centre.
    """
    state = np.random.default_rng(4)
    y, x = np.mgrid[0:40, 0:40]
    field = np.sin(x / 6) * np.cos(y / 7) * 4 + state.normal(0, 0.4, (40, 40))
    fig, axs = uplt.subplots(ncols=3, figwidth="86mm", figheight="30mm", wspace="2mm")
    axs[0].pcolormesh(field, cmap="roma", discrete=False)
    axs[1].pcolormesh(field, cmap="roma", levels=9)
    axs[2].pcolormesh(field, cmap="roma", values=uplt.arange(-4, 4, 1), extend="both")
    for ax, label in zip(axs, ("discrete=False", "levels=9", "values=arange(-4, 4)")):
        ax.format(
            xticks=[],
            yticks=[],
            grid=False,
            title=label,
            titlesize=5.4,
            titleloc="l",
            titlepad=1.5,
        )
    save(fig, "norms.png")


def palette():
    """
    Emit the page palette as Typst data.

    The rails on the page and the swatches in the figures are the same batlow
    samples, and writing them from here is what keeps them that way.
    """
    from matplotlib.colors import to_hex

    cmap = uplt.Colormap("batlow")
    stops = [to_hex(cmap(value)) for value in np.linspace(0, 1, 16)]
    rails = [to_hex(cmap(value)) for value in (0.0, 0.22, 0.42, 0.66, 0.88)]
    path = os.path.join(ASSETS, "palette.typ")
    os.makedirs(ASSETS, exist_ok=True)
    with open(path, "w") as handle:
        handle.write("// Generated by parts/color.py — do not edit.\n")
        handle.write("#let batlow = (\n")
        for stop in stops:
            handle.write(f'  rgb("{stop}"),\n')
        handle.write(")\n\n#let rails = (\n")
        for rail in rails:
            handle.write(f'  rgb("{rail}"),\n')
        handle.write(")\n")
    print("  assets/palette.typ")


def main():
    use_style()
    palette()
    colormaps()
    cycles()
    luminance()
    norms()


if __name__ == "__main__":
    main()
