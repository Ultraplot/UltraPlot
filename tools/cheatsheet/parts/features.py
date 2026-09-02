#!/usr/bin/env python3
"""
One small icon per UltraPlot feature that matplotlib does not have.

The plot-type icons in ``icons.py`` answer "what can I draw"; these answer
"what does UltraPlot add". The list follows the sections of ``docs/why.rst``,
so it stays tied to the project's own account of what it is for.

Each icon is drawn by the feature it illustrates: the sharing icon really has
sharing switched on, the outer-colorbar icon really allocates a gridspec slot.
Anything that cannot be drawn honestly at this size is left out rather than
faked.
"""

from __future__ import annotations

import numpy as np

import ultraplot as uplt

from common import ACCENT, INK, INK_FAINT, RULE, SUNK, bare, save, use_style

#: Icons are square and rendered large; Typst scales them into the page.
SIZE = "26mm"

RNG = np.random.default_rng(51423)
X = np.linspace(0, 10, 120)


def _field(n=28):
    y, x = np.mgrid[0:n, 0:n]
    return np.sin(x / 4.0) * np.cos(y / 5.0)


def _mark(ax, text, *, x=0.5, y=0.5, size=6.5, color=ACCENT, **kwargs):
    """
    Write the keyword an icon is about, in the page's monospace.
    """
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        family="monospace",
        fontsize=size,
        color=color,
        **kwargs,
    )


# --------------------------------------------------------------- layout


def feature_format(fig, axs):
    """One call sets titles, labels, limits and ticks."""
    ax = axs[0]
    ax.plot(X, np.sin(X), lw=1.4)
    ax.format(
        title="title",
        xlabel="x label",
        ylabel="y label",
        abc="a.",
        abcloc="ul",
        titlesize=6,
        labelsize=6,
        abcsize=6,
        ticklabelsize=5,
        xlocator=5,
        ylocator=1,
        grid=True,
    )


def feature_sharing(fig, axs):
    """Ticks and labels appear once per row and column, not per panel."""
    for index, ax in enumerate(axs):
        ax.plot(X, np.sin(X + index), lw=1)
    axs.format(
        xlabel="x",
        ylabel="y",
        labelsize=6,
        ticklabelsize=4.5,
        xlocator=5,
        ylocator=1,
        grid=False,
    )


def feature_spanning(fig, axs):
    """One label spans the panels it describes."""
    for ax in axs:
        ax.plot(X, np.sin(X), lw=1)
    axs.format(
        xlabel="one spanning label",
        ylabel="y",
        labelsize=5.5,
        ticklabelsize=4.5,
        xlocator=5,
        ylocator=1,
        grid=False,
    )


def feature_edge_labels(fig, axs):
    """Row and column headers belong to the figure, not to an axes."""
    for ax in axs:
        bare(ax, facecolor=SUNK, edgecolor=RULE)
    axs.format(
        toplabels=("col", "col"),
        leftlabels=("row", "row"),
        toplabelsize=5.5,
        leftlabelsize=5.5,
    )


def feature_abc(fig, axs):
    """Panel letters are placed for you, in any of nine slots."""
    for index, ax in enumerate(axs):
        bare(ax, facecolor=SUNK, edgecolor=RULE)
        ax.format(abc="a.", abcloc=("ul", "ur", "ll", "lr")[index], abcsize=7)


def feature_corner_titles(fig, axs):
    """Six corner-title keywords, no manual text placement."""
    ax = bare(axs[0], facecolor=SUNK, edgecolor=RULE)
    ax.format(
        ultitle="ul",
        urtitle="ur",
        lltitle="ll",
        lrtitle="lr",
        titlesize=5.5,
    )
    _mark(ax, "…title", size=6)


def feature_mosaic(fig, axs):
    """A layout array is the layout."""
    for index, ax in enumerate(axs, start=1):
        bare(ax, facecolor=SUNK, edgecolor=RULE)
        ax.text(
            0.5,
            0.5,
            str(index),
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=7,
            color=INK_FAINT,
            family="monospace",
        )


def feature_units(fig, axs):
    """Sizes and spaces are given in real units."""
    ax = bare(axs[0], facecolor=SUNK, edgecolor=RULE)
    ax.annotate(
        "",
        xy=(0.08, 0.5),
        xytext=(0.92, 0.5),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "<->", "color": ACCENT, "lw": 0.9},
    )
    _mark(ax, "'55mm'", y=0.63)
    _mark(ax, "refwidth", y=0.28, size=5.5, color=INK_FAINT)


def feature_subplotgrid(fig, axs):
    """The returned grid is indexable like an array."""
    for index, ax in enumerate(axs):
        column = index % 3
        bare(
            ax,
            facecolor=ACCENT if column == 1 else SUNK,
            edgecolor=RULE,
        )
    axs[1].text(
        0.5,
        0.5,
        "axs[:, 1]",
        transform=axs[1].transAxes,
        rotation=90,
        ha="center",
        va="center",
        fontsize=5.5,
        color="w",
        family="monospace",
    )


# --------------------------------------------------------------- axes


def feature_panels(fig, axs):
    """Marginal panels take their own gridspec slot."""
    ax = axs[0]
    data = RNG.normal(size=(400, 2))
    ax.scatter(data[:, 0], data[:, 1], s=2, alpha=0.5, color=ACCENT)
    for side in ("r", "t"):
        panel = ax.panel_axes(side, width="4mm")
        values = data[:, 0 if side == "t" else 1]
        (panel.hist if side == "t" else panel.histh)(
            values,
            bins=16,
            color=ACCENT,
            alpha=0.6,
            lw=0,
        )
        bare(panel)
    bare(ax)


def feature_inset(fig, axs):
    """Insets can draw their own zoom indicator."""
    ax = axs[0]
    ax.plot(X, np.sin(X) + RNG.normal(0, 0.05, X.size), lw=1, color=ACCENT)
    inset = ax.inset_axes([0.52, 0.06, 0.44, 0.42], zoom=True)
    inset.plot(X, np.sin(X) + RNG.normal(0, 0.05, X.size), lw=1, color=ACCENT)
    inset.format(xlim=(2, 4), ylim=(0.2, 1.1))
    bare(inset)
    bare(ax)


def feature_dual_axes(fig, axs):
    """A twin axes that carries a scaled version of the same data."""
    ax = axs[0]
    ax.plot(X, np.sin(X), lw=1.2, color=ACCENT)
    dual = ax.dualx(lambda value: value * 2.54)
    ax.format(xlabel="in", labelsize=5.5, ticklabelsize=4.5, xlocator=5, grid=False)
    dual.format(xlabel="cm", labelsize=5.5, ticklabelsize=4.5, xlocator=10)
    ax.format(yticks=[])


def feature_projections(fig, axs):
    """Projections by short name, with cartographic features built in."""
    axs[0].format(
        land=True,
        ocean=True,
        coast=True,
        landcolor="gray3",
        oceancolor=ACCENT,
        coastlinewidth=0.3,
        grid=True,
        gridalpha=0.35,
        labels=False,
    )


def feature_taylor(fig, axs):
    """Projections that are whole diagram types."""
    ax = axs[0]
    ax.format(
        rlim=(0, 1.6),
        corrlines=(1, 0.9, 0.6, 0),
        rlines=0.5,
        corrlabel="",
        ticklabelsize=4,
        labelsize=4,
    )
    ax.plot_corr(1, 1, marker="*", markersize=9, color="red7")
    for (corr, std), color in zip(
        ((0.95, 1.15), (0.8, 0.75)),
        ("denim", "green7"),
    ):
        ax.scatter_corr(corr, std, s=24, color=color, zorder=6)


# --------------------------------------------------------------- guides


def feature_outer_guide(fig, axs):
    """Outer guides get their own slot instead of eating the axes."""
    ax = axs[0]
    mesh = ax.pcolormesh(_field(), cmap="batlow", levels=7)
    ax.colorbar(mesh, loc="r", width="3mm", ticks=[])
    bare(ax)


def feature_stacked_guides(fig, axs):
    """Several guides on one side queue up."""
    ax = axs[0]
    mesh = ax.pcolormesh(_field(), cmap="batlow", levels=7)
    ax.colorbar(mesh, loc="b", width="2.6mm", ticks=[], length=0.9)
    ax.colorbar(mesh, loc="b", width="2.6mm", ticks=[], length=0.9)
    bare(ax)


def feature_inset_guide(fig, axs):
    """The same location codes place a guide inside the axes."""
    ax = axs[0]
    mesh = ax.pcolormesh(_field(), cmap="batlow", levels=7)
    ax.colorbar(mesh, loc="ll", width="3.4mm", length=0.78, ticks=[], frame=True)
    bare(ax)


def feature_semantic_legend(fig, axs):
    """Legends that describe an encoding, with no artist to point at."""
    ax = axs[0]
    ax.sizelegend(
        [12, 60, 150],
        labels=["S", "M", "L"],
        loc="c",
        ncols=1,
        frame=False,
        fontsize=6,
        markercolor=ACCENT,
    )
    bare(ax)


def feature_on_the_fly(fig, axs):
    """A plotting command can build its own guide."""
    ax = axs[0]
    lines = ax.plot(
        X,
        np.column_stack([np.sin(X), np.cos(X), np.sin(X / 2)]),
        lw=1.2,
        labels=["a", "b", "c"],
        cycle="colorblind",
    )
    ax.legend(lines, loc="b", ncols=3, frame=False, fontsize=5.5)
    bare(ax)


# --------------------------------------------------------------- color


def feature_discrete_norm(fig, axs):
    """Levels are discrete by default, so a colorbar reads as steps."""
    ax = axs[0]
    mesh = ax.pcolormesh(_field(), cmap="batlow", levels=7)
    ax.colorbar(mesh, loc="b", width="3mm", ticks=[], length=0.95)
    bare(ax)


def feature_centred_levels(fig, axs):
    """`values=` pins a diverging midpoint to the real zero."""
    ax = axs[0]
    mesh = ax.pcolormesh(
        _field() * 4,
        cmap="BuRd",
        values=uplt.arange(-4, 4, 1),
        extend="both",
    )
    ax.colorbar(mesh, loc="b", width="3mm", ticks=[0], length=0.95, ticklabelsize=5)
    bare(ax)


def feature_colormap_surgery(fig, axs):
    """Existing colormaps can be truncated, shifted and merged."""
    ax = axs[0]
    gradient = np.linspace(0, 1, 256)[None, :]
    recipes = (
        ("roma", {}),
        ("roma", {"left": 0.35}),
        ("roma", {"shift": 90}),
        ("roma", {"cut": 0.35}),
    )
    for index, (name, kwargs) in enumerate(recipes):
        bar = ax.inset_axes(
            [0.06, 0.80 - index * 0.24, 0.88, 0.16],
            transform=ax.transAxes,
            zoom=False,
        )
        bar = bar[0] if hasattr(bar, "__len__") else bar
        bar.imshow(gradient, aspect="auto", cmap=uplt.Colormap(name, **kwargs))
        bare(bar)
    bare(ax, linewidth=0)


def feature_perceptual(fig, axs):
    """Colormaps can be built from perceptual channel values."""
    ax = axs[0]
    gradient = np.linspace(0, 1, 256)[None, :]
    recipes = (
        {"h": (0, 120), "s": 80, "l": (20, 90), "space": "hpl"},
        {"h": (200, 320), "s": 60, "l": (25, 95), "space": "hpl"},
        {"h": (0, 360), "c": 50, "l": 70, "space": "hcl", "cyclic": True},
    )
    for index, kwargs in enumerate(recipes):
        bar = ax.inset_axes(
            [0.06, 0.72 - index * 0.30, 0.88, 0.20],
            transform=ax.transAxes,
            zoom=False,
        )
        bar = bar[0] if hasattr(bar, "__len__") else bar
        bar.imshow(gradient, aspect="auto", cmap=uplt.Colormap(**kwargs))
        bare(bar)
    bare(ax, linewidth=0)


def feature_cycle_from_cmap(fig, axs):
    """Any colormap can become a property cycle."""
    ax = axs[0]
    values = np.column_stack([np.sin(X + shift / 2) for shift in range(6)])
    ax.plot(X, values, lw=1.3, cycle="Blues", cycle_kw={"left": 0.25})
    bare(ax)


def feature_named_colors(fig, axs):
    """A registry of named colors from xkcd and open-color."""
    ax = axs[0]
    names = (
        "denim",
        "rose",
        "ocean blue",
        "sky blue",
        "kelly green",
        "orange7",
        "violet7",
        "gray6",
        "red7",
    )
    for index, name in enumerate(names):
        row, column = divmod(index, 3)
        swatch = ax.inset_axes(
            [0.08 + column * 0.30, 0.66 - row * 0.28, 0.24, 0.20],
            transform=ax.transAxes,
            zoom=False,
        )
        swatch = swatch[0] if hasattr(swatch, "__len__") else swatch
        bare(swatch, facecolor=name, linewidth=0)
    bare(ax, linewidth=0)


# --------------------------------------------------------------- data


def feature_statistics(fig, axs):
    """Reductions and spread indicators computed from raw samples."""
    ax = axs[0]
    runs = np.sin(X)[None, :] + RNG.normal(0, 0.3, (60, X.size))
    ax.plot(X, runs, mean=True, shadestd=1, fadepctile=(10, 90), lw=1.5)
    bare(ax)


def feature_dataframe(fig, axs):
    """Labels, coordinates and units are read off pandas and xarray."""
    import pandas as pd

    ax = axs[0]
    frame = pd.DataFrame(
        {"signal (mV)": np.sin(X) + RNG.normal(0, 0.05, X.size)},
        index=pd.Index(X, name="time (s)"),
    )
    ax.plot(frame, lw=1.3, color=ACCENT)
    ax.format(labelsize=5.5, ticklabelsize=4.5, xlocator=5, ylocator=1, grid=False)


def feature_labels(fig, axs):
    """Cell and contour labels in a colour that stays legible."""
    axs[0].heatmap(
        RNG.uniform(-1, 1, (3, 3)).round(1),
        cmap="BuRd",
        vmin=-1,
        vmax=1,
        labels=True,
        labels_kw={"fontsize": 5.5},
    )
    bare(axs[0])


# --------------------------------------------------------------- output


def feature_rc_context(fig, axs):
    """Settings cascade, and apply inside a context."""
    ax = axs[0]
    _mark(ax, "uplt.rc", y=0.70, size=6.5, color=INK)
    _mark(ax, "fontsize", y=0.47, size=5.5, color=INK_FAINT)
    _mark(ax, "tickdir", y=0.30, size=5.5, color=INK_FAINT)
    _mark(ax, "cycle", y=0.13, size=5.5, color=INK_FAINT)
    bare(ax, facecolor=SUNK, edgecolor=RULE)


def feature_animation(fig, axs):
    """A faster writer behind matplotlib's animation API."""
    ax = axs[0]
    for index, alpha in enumerate((0.2, 0.45, 1.0)):
        ax.plot(X, np.sin(X + index * 0.6), lw=1.5, color=ACCENT, alpha=alpha)
    bare(ax)


def feature_curvedtext(fig, axs):
    """Text that follows a path."""
    ax = axs[0]
    theta = np.linspace(0.15 * np.pi, 0.85 * np.pi, 200)
    x, y = np.cos(theta), np.sin(theta)
    ax.plot(x, y, lw=0.6, color=RULE)
    ax.curvedtext(x, y, "curved text", fontsize=6.5, color=INK)
    ax.format(xlim=(-1.25, 1.25), ylim=(-0.35, 1.3))
    bare(ax, linewidth=0)


#: Each feature is either *de novo* — matplotlib has no equivalent at all — or
#: an *enhancement*, where matplotlib can do it but you assemble it yourself.
#: Saying which, and naming the matplotlib counterpart, keeps the sheet honest:
#: most of what UltraPlot gives you is the second kind, and that is the point.
NEW, BETTER = "new", "better"

#: name -> spec. ``draw`` and ``subplots`` make the icon; ``label`` captions it;
#: ``kind`` and ``mpl`` classify it; ``group`` places it on the page.
FEATURES = {
    # ----------------------------------------------------------- layout
    "format": {
        "draw": feature_format,
        "subplots": {},
        "group": "layout",
        "label": "format()",
        "kind": BETTER,
        "mpl": "set_title, set_xlabel, set_xlim, tick_params, …",
    },
    "sharing": {
        "draw": feature_sharing,
        "subplots": {"nrows": 2, "ncols": 2, "share": True},
        "group": "layout",
        "label": "share=True",
        "kind": BETTER,
        "mpl": "sharex=, sharey= — without the label collapsing",
    },
    "spanning_labels": {
        "draw": feature_spanning,
        "subplots": {"ncols": 2, "share": True, "span": True},
        "group": "layout",
        "label": "span=True",
        "kind": BETTER,
        "mpl": "supxlabel spans the whole figure, not a subset",
    },
    "edge_labels": {
        "draw": feature_edge_labels,
        "subplots": {"nrows": 2, "ncols": 2},
        "group": "layout",
        "label": "toplabels=",
        "kind": NEW,
        "mpl": None,
    },
    "abc_labels": {
        "draw": feature_abc,
        "subplots": {"nrows": 2, "ncols": 2},
        "group": "layout",
        "label": "abc='a.'",
        "kind": NEW,
        "mpl": None,
    },
    "corner_titles": {
        "draw": feature_corner_titles,
        "subplots": {},
        "group": "layout",
        "label": "urtitle=",
        "kind": BETTER,
        "mpl": "set_title(loc=) — three slots, all above the axes",
    },
    "mosaic_array": {
        "draw": feature_mosaic,
        "subplots": {"array": [[1, 1, 2], [3, 4, 2]]},
        "group": "layout",
        "label": "subplots([[…]])",
        "kind": BETTER,
        "mpl": "subplot_mosaic",
    },
    "physical_units": {
        "draw": feature_units,
        "subplots": {},
        "group": "layout",
        "label": "refwidth='55mm'",
        "kind": NEW,
        "mpl": None,
    },
    "subplotgrid": {
        "draw": feature_subplotgrid,
        "subplots": {"nrows": 2, "ncols": 3},
        "group": "layout",
        "label": "axs[:, 1]",
        "kind": BETTER,
        "mpl": "the ndarray indexes, but will not broadcast format()",
    },
    # ------------------------------------------------------------- axes
    "panel_axes": {
        "draw": feature_panels,
        "subplots": {},
        "group": "axes",
        "label": "panel_axes('r')",
        "kind": BETTER,
        "mpl": "mpl_toolkits axes_grid1 divider",
    },
    "inset_axes": {
        "draw": feature_inset,
        "subplots": {},
        "group": "axes",
        "label": "inset_axes(zoom=True)",
        "kind": BETTER,
        "mpl": "inset_axes + indicate_inset_zoom",
    },
    "dualx": {
        "draw": feature_dual_axes,
        "subplots": {},
        "group": "axes",
        "label": "dualx(f)",
        "kind": BETTER,
        "mpl": "secondary_xaxis",
    },
    "projections": {
        "draw": feature_projections,
        "subplots": {"proj": "ortho"},
        "group": "axes",
        "label": "proj='ortho'",
        "kind": BETTER,
        "mpl": "cartopy GeoAxes, wired up by hand",
    },
    "taylor_axes": {
        "draw": feature_taylor,
        "subplots": {"proj": "taylor"},
        "group": "axes",
        "label": "proj='taylor'",
        "kind": NEW,
        "mpl": None,
    },
    # ----------------------------------------------------------- guides
    "outer_guides": {
        "draw": feature_outer_guide,
        "subplots": {},
        "group": "guides",
        "label": "colorbar(loc='r')",
        "kind": BETTER,
        "mpl": "fig.colorbar(ax=) steals space from the axes",
    },
    "stacked_guides": {
        "draw": feature_stacked_guides,
        "subplots": {},
        "group": "guides",
        "label": "two on one side",
        "kind": BETTER,
        "mpl": "possible, but you place the second one yourself",
    },
    "inset_guides": {
        "draw": feature_inset_guide,
        "subplots": {},
        "group": "guides",
        "label": "colorbar(loc='ll')",
        "kind": BETTER,
        "mpl": "colorbar(cax=inset_axes(...))",
    },
    "guides_on_the_fly": {
        "draw": feature_on_the_fly,
        "subplots": {},
        "group": "guides",
        "label": "legend='b'",
        "kind": NEW,
        "mpl": None,
    },
    "semantic_legends": {
        "draw": feature_semantic_legend,
        "subplots": {},
        "group": "guides",
        "label": "sizelegend()",
        "kind": NEW,
        "mpl": None,
    },
    # ------------------------------------------------------------ color
    "discrete_levels": {
        "draw": feature_discrete_norm,
        "subplots": {},
        "group": "color",
        "label": "levels=7",
        "kind": BETTER,
        "mpl": "BoundaryNorm, constructed by hand",
    },
    "centred_levels": {
        "draw": feature_centred_levels,
        "subplots": {},
        "group": "color",
        "label": "values=arange()",
        "kind": BETTER,
        "mpl": "TwoSlopeNorm, CenteredNorm",
    },
    "colormap_surgery": {
        "draw": feature_colormap_surgery,
        "subplots": {},
        "group": "color",
        "label": "cmap_kw={...}",
        "kind": BETTER,
        "mpl": "resampled() truncates; no cut or shift",
    },
    "perceptual_colormaps": {
        "draw": feature_perceptual,
        "subplots": {},
        "group": "color",
        "label": "Colormap(h=, s=, l=)",
        "kind": NEW,
        "mpl": None,
    },
    "cycle_from_cmap": {
        "draw": feature_cycle_from_cmap,
        "subplots": {},
        "group": "color",
        "label": "cycle='Blues'",
        "kind": BETTER,
        "mpl": "cycler(color=cmap(...)) by hand",
    },
    "named_colors": {
        "draw": feature_named_colors,
        "subplots": {},
        "group": "color",
        "label": "'denim' 'orange7'",
        "kind": BETTER,
        "mpl": "xkcd: and CSS4 names, prefixed",
    },
    # ------------------------------------------------------------- data
    "statistics": {
        "draw": feature_statistics,
        "subplots": {},
        "group": "data",
        "label": "mean=True",
        "kind": NEW,
        "mpl": None,
    },
    "pandas_xarray": {
        "draw": feature_dataframe,
        "subplots": {},
        "group": "data",
        "label": "pandas / xarray",
        "kind": NEW,
        "mpl": None,
    },
    "auto_labels": {
        "draw": feature_labels,
        "subplots": {},
        "group": "data",
        "label": "labels=True",
        "kind": BETTER,
        "mpl": "clabel, for contours only",
    },
    "rc_settings": {
        "draw": feature_rc_context,
        "subplots": {},
        "group": "data",
        "label": "uplt.rc",
        "kind": BETTER,
        "mpl": "rcParams, one setting at a time",
    },
    "fast_animation": {
        "draw": feature_animation,
        "subplots": {},
        "group": "data",
        "label": "FuncAnimation",
        "kind": BETTER,
        "mpl": "same API, slower writer",
    },
    "curved_text": {
        "draw": feature_curvedtext,
        "subplots": {},
        "group": "data",
        "label": "curvedtext()",
        "kind": NEW,
        "mpl": None,
    },
}


def write_manifest():
    """
    Emit the registry as Typst data.

    The page builds its galleries from this, so the classification lives in one
    place and a new icon reaches the sheet by being added here.
    """
    import os

    from common import ASSETS

    path = os.path.join(ASSETS, "features.typ")
    with open(path, "w") as handle:
        handle.write("// Generated by parts/features.py — do not edit.\n")
        handle.write("#let features = (\n")
        for name, spec in FEATURES.items():
            mpl = spec["mpl"]
            mpl = f'"{mpl}"' if mpl else "none"
            handle.write(
                f'  (name: "{name}", label: "{spec["label"]}", '
                f'kind: "{spec["kind"]}", mpl: {mpl}, '
                f'group: "{spec["group"]}"),\n'
            )
        handle.write(")\n")
    print("  assets/features.typ")


def main():
    use_style(fontsize=5)
    failures = []
    for name, spec in FEATURES.items():
        kwargs = dict(spec["subplots"])
        array = kwargs.pop("array", None)
        args = (array,) if array is not None else ()
        fig, axs = uplt.subplots(
            *args,
            figwidth=SIZE,
            figheight=SIZE,
            hspace="1mm",
            wspace="1mm",
            **kwargs,
        )
        try:
            spec["draw"](fig, axs)
        except Exception as error:  # keep going; the build reports the gap
            failures.append(f"{name}: {type(error).__name__}: {error}")
            uplt.close(fig)
            continue
        save(fig, f"features/{name}.png", dpi=220)
    write_manifest()
    if failures:
        print("feature icon failures:")
        for failure in failures:
            print(f"  {failure}")


if __name__ == "__main__":
    main()
