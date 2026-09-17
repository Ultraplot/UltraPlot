#!/usr/bin/env python3
"""
One small icon per UltraPlot feature that matplotlib does not have.

The plot-type icons in ``icons.py`` answer "what can I draw"; these answer
"what does UltraPlot add". The registry contains the features used by the draw.io sheet.

Each icon is drawn by the feature it illustrates: the sharing icon really has
sharing switched on, the outer-colorbar icon really allocates a gridspec slot.
Anything that cannot be drawn honestly at this size is left out rather than
faked.
"""

from __future__ import annotations

import numpy as np

import ultraplot as uplt

from common import ACCENT, INK, INK_FAINT, RULE, SUNK, bare, save, use_style

#: Square vector icons are scaled by the draw.io layout.
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
    ax.plot(X, np.sin(X), lw=2.5)
    ax.format(
        title="Title",
        xlabel="X",
        ylabel="Y",
        abc="a.",
        abcloc="ul",
        titlesize=10,
        labelsize=9,
        abcsize=11,
        ticklabelsize=6,
        xlocator=5,
        ylocator=2,
        grid=True,
    )


def feature_spanning(fig, axs):
    """One label spans the panels it describes."""
    for ax in axs:
        ax.plot(X, np.sin(X), lw=2.2)
    axs.format(
        xlabel="shared X",
        ylabel="y",
        labelsize=9,
        ticklabelsize=6,
        xlocator=5,
        ylocator=2,
        grid=False,
    )


def feature_edge_labels(fig, axs):
    """Row and column headers belong to the figure, not to an axes."""
    for ax in axs:
        bare(ax, facecolor=SUNK, edgecolor=RULE)
    axs.format(
        toplabels=("A", "B"),
        leftlabels=("I", "II"),
        toplabelsize=12,
        leftlabelsize=12,
    )


def feature_abc(fig, axs):
    """Panel letters use the conventional upper-left position."""
    for ax in axs:
        bare(ax, facecolor=SUNK, edgecolor=RULE)
        ax.format(abc="a.", abcloc="ul", abcsize=10)


def feature_corner_titles(fig, axs):
    """Six corner-title keywords, no manual text placement."""
    ax = bare(axs[0], facecolor=SUNK, edgecolor=RULE)
    ax.format(
        ultitle="ul",
        urtitle="ur",
        lltitle="ll",
        lrtitle="lr",
        titlesize=10,
    )
    _mark(ax, "title", size=11, weight="bold")


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
            fontsize=17, fontweight="bold",
            color=ACCENT,
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
    _mark(ax, "'55mm'", y=0.68, size=12, weight="bold")
    _mark(ax, "refwidth", y=0.25, size=9, color=INK, weight="bold")


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
        ":, 1",
        transform=axs[1].transAxes,
        rotation=90,
        ha="center",
        va="center",
        fontsize=10, fontweight="bold",
        color="w",
        family="monospace",
    )


# --------------------------------------------------------------- axes


def feature_panels(fig, axs):
    """Marginal panels take their own gridspec slot."""
    ax = axs[0]
    data = RNG.normal(size=(90, 2))
    ax.scatter(data[:, 0], data[:, 1], s=10, alpha=0.8, color=ACCENT)
    for side in ("r", "t"):
        panel = ax.panel_axes(side, width="4mm")
        values = data[:, 0 if side == "t" else 1]
        (panel.hist if side == "t" else panel.histh)(
            values,
            bins=8,
            color=ACCENT,
            alpha=0.6,
            lw=0,
        )
        bare(panel)
    bare(ax)


def feature_inset(fig, axs):
    """A zoomed copy of the same data, connected at the facing corners."""
    from matplotlib.patches import ConnectionPatch

    ax = axs[0]
    y = np.sin(X) + RNG.normal(0, 0.05, X.size)
    ax.plot(X, y, lw=2.2, color=ACCENT)
    inset = ax.inset_axes([0.52, 0.06, 0.44, 0.42], zoom=True)
    inset.plot(X, y, lw=2.2, color=ACCENT)
    inset.format(xlim=(2, 4), ylim=(0.2, 1.1))
    bare(inset)
    bare(ax)
    indicator = inset.indicate_inset_zoom()
    connectors = indicator.connectors if hasattr(indicator, "connectors") else indicator[1]
    for connector in connectors:
        connector.set_visible(False)
    # Explicit facing-edge links avoid running through the source rectangle.
    for corner, limit in ((0, 0.2), (1, 1.1)):
        connector = ConnectionPatch(
            xyA=(0, corner), coordsA=inset.transAxes,
            xyB=(4, limit), coordsB=ax.transData,
            arrowstyle="-", color=RULE, linewidth=1, clip_on=False,
            zorder=inset.get_zorder() + 1,
        )
        ax.add_artist(connector)


def feature_dual_axes(fig, axs):
    """A twin axes that carries a scaled version of the same data."""
    ax = axs[0]
    ax.plot(X, np.sin(X), lw=2.3, color=ACCENT)
    dual = ax.dualx(lambda value: value * 2.54)
    ax.format(xlabel="in", labelsize=9, ticklabelsize=6, xlocator=5, grid=False)
    dual.format(xlabel="cm", labelsize=9, ticklabelsize=6, xlocator=10)
    ax.format(yticks=[])


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
    ax.colorbar(mesh, loc="ll", width="1.5mm", length="0.5ax", ticks=[], frame=True)
    bare(ax)


# --------------------------------------------------------------- color


# --------------------------------------------------------------- data


# --------------------------------------------------------------- output


def feature_curvedtext(fig, axs):
    """Text that follows a path."""
    ax = axs[0]
    theta = np.linspace(0.15 * np.pi, 0.85 * np.pi, 200)
    x, y = np.cos(theta), np.sin(theta)
    ax.plot(x, y, lw=0.6, color=RULE)
    ax.curvedtext(x, y, "curved text", fontsize=12, fontweight="bold", color=INK)
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
    'format': {
        'draw': feature_format,
        'subplots': {},
        'group': 'layout',
        'label': 'format()',
        'kind': BETTER,
        'mpl': 'set_title, set_xlabel, set_xlim, tick_params, …',
    },
    'spanning_labels': {
        'draw': feature_spanning,
        'subplots': {'ncols': 2, 'share': True, 'span': True},
        'group': 'layout',
        'label': 'span=True',
        'kind': BETTER,
        'mpl': 'supxlabel spans the whole figure, not a subset',
    },
    'edge_labels': {
        'draw': feature_edge_labels,
        'subplots': {'nrows': 2, 'ncols': 2},
        'group': 'layout',
        'label': 'toplabels=',
        'kind': NEW,
        'mpl': None,
    },
    'abc_labels': {
        'draw': feature_abc,
        'subplots': {'nrows': 2, 'ncols': 2},
        'group': 'layout',
        'label': "abc='a.'",
        'kind': NEW,
        'mpl': None,
    },
    'corner_titles': {
        'draw': feature_corner_titles,
        'subplots': {},
        'group': 'layout',
        'label': 'urtitle=',
        'kind': BETTER,
        'mpl': 'set_title(loc=) — three slots, all above the axes',
    },
    'mosaic_array': {
        'draw': feature_mosaic,
        'subplots': {'array': [[1, 1, 2], [3, 4, 2]]},
        'group': 'layout',
        'label': 'subplots([[…]])',
        'kind': BETTER,
        'mpl': 'subplot_mosaic',
    },
    'physical_units': {
        'draw': feature_units,
        'subplots': {},
        'group': 'layout',
        'label': "refwidth='55mm'",
        'kind': NEW,
        'mpl': None,
    },
    'subplotgrid': {
        'draw': feature_subplotgrid,
        'subplots': {'nrows': 2, 'ncols': 3},
        'group': 'layout',
        'label': 'axs[:, 1]',
        'kind': BETTER,
        'mpl': 'the ndarray indexes, but will not broadcast format()',
    },
    'panel_axes': {
        'draw': feature_panels,
        'subplots': {},
        'group': 'axes',
        'label': "panel_axes('r')",
        'kind': BETTER,
        'mpl': 'mpl_toolkits axes_grid1 divider',
    },
    'inset_axes': {
        'draw': feature_inset,
        'subplots': {},
        'group': 'axes',
        'label': 'inset_axes(zoom=True)',
        'kind': BETTER,
        'mpl': 'inset_axes + indicate_inset_zoom',
    },
    'dualx': {
        'draw': feature_dual_axes,
        'subplots': {},
        'group': 'axes',
        'label': 'dualx(f)',
        'kind': BETTER,
        'mpl': 'secondary_xaxis',
    },
    'outer_guides': {
        'draw': feature_outer_guide,
        'subplots': {},
        'group': 'guides',
        'label': "colorbar(loc='r')",
        'kind': BETTER,
        'mpl': 'fig.colorbar(ax=) steals space from the axes',
    },
    'stacked_guides': {
        'draw': feature_stacked_guides,
        'subplots': {},
        'group': 'guides',
        'label': 'two on one side',
        'kind': BETTER,
        'mpl': 'possible, but you place the second one yourself',
    },
    'inset_guides': {
        'draw': feature_inset_guide,
        'subplots': {},
        'group': 'guides',
        'label': "colorbar(loc='ll')",
        'kind': BETTER,
        'mpl': 'colorbar(cax=inset_axes(...))',
    },
    'curved_text': {
        'draw': feature_curvedtext,
        'subplots': {},
        'group': 'data',
        'label': 'curvedtext()',
        'kind': NEW,
        'mpl': None,
    },
}


def main():
    use_style(fontsize=5)
    uplt.rc.update({"font.weight": "bold", "axes.labelweight": "bold",
                    "axes.titleweight": "bold", "abc.weight": "bold"})
    failures = []
    for name, spec in FEATURES.items():
        kwargs = dict(spec["subplots"])
        array = kwargs.pop("array", None)
        args = (array,) if array is not None else ()
        fig, axs = uplt.subplots(
            *args,
            figwidth=SIZE,
            figheight=SIZE,
            hspace="2mm",
            wspace="2mm",
            **kwargs,
        )
        try:
            spec["draw"](fig, axs)
        except Exception as error:  # keep going; the build reports the gap
            failures.append(f"{name}: {type(error).__name__}: {error}")
            uplt.close(fig)
            continue
        save(fig, f"features/{name}.svg", dpi=220)
    if failures:
        print("feature icon failures:")
        for failure in failures:
            print(f"  {failure}")


if __name__ == "__main__":
    main()
