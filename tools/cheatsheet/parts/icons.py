#!/usr/bin/env python3
"""
One small plot per UltraPlot command, drawn with the command itself.

Everything is drawn from the shared vocabulary in ``common`` — one wave, one
cloud, one field, one set of categories — so two icons differ only where the
commands differ. Icons are read at a glance and often at 10 mm, so the drawing
rules are deliberately narrow: thick strokes, few marks, no ticks, and colour
used for one job at a time.

Each entry is classified as ``SAME`` (matplotlib has the command), ``BETTER``
(matplotlib can, but you assemble it) or ``NEW`` (no equivalent), and the
matplotlib counterpart is named for the middle case. ``GROUP`` places it on the
page and in the docs index.
"""

from __future__ import annotations

import numpy as np

import ultraplot as uplt

from common import (
    ASSETS,
    CATEGORIES,
    CLOUD,
    ICON_DIVERGING,
    ICON_LINE,
    ICON_LW,
    ICON_MARGIN,
    ICON_MS,
    ICON_DENSITY,
    ICON_SEQUENTIAL,
    ICON_STRUCTURE,
    SAMPLES,
    SIGNED,
    VALUES,
    WAVE,
    WAVE_X,
    WAVES,
    bare,
    rotational_field,
    save,
    peak_field,
    smooth_field,
    use_style,
    without_new_text,
)

#: Icons are square and rendered large; the pages scale them down.
SIZE = "26mm"

#: Kinds, so the pages can say how far a command is from matplotlib.
SAME, BETTER, NEW = "same", "better", "new"

RNG = np.random.default_rng(51423)


# ------------------------------------------------------------------ lines


def icon_plot(ax):
    ax.plot(WAVE_X, WAVES, lw=ICON_LW)


def icon_scatter(ax):
    ax.scatter(CLOUD[:, 0], CLOUD[:, 1], s=ICON_MS, alpha=0.8)


def icon_step(ax):
    ax.step(np.arange(10), np.tile(VALUES, 2), lw=ICON_LW, color=ICON_LINE)


def icon_stem(ax):
    # stem takes fmt strings, so its colours come from the cycle: C0 is the
    # stems and marker, C1 the baseline.
    ax.stem(
        np.arange(8),
        np.sin(np.linspace(0, 3, 8)) + 1.2,
        cycle=uplt.Cycle((ICON_LINE, ICON_STRUCTURE), name="_no_name"),
    )


def icon_vlines(ax):
    ax.vlines(
        np.arange(9), 0, np.sin(np.linspace(0, 4, 9)), lw=ICON_LW, color=ICON_LINE
    )


def icon_hlines(ax):
    ax.hlines(
        np.arange(9), 0, np.sin(np.linspace(0, 4, 9)), lw=ICON_LW, color=ICON_LINE
    )


def icon_parametric(ax):
    theta = np.linspace(0, 4 * np.pi, 300)
    ax.parametric(
        theta * np.cos(theta),
        theta * np.sin(theta),
        theta,
        cmap=ICON_SEQUENTIAL,
        lw=2.6,
    )


def icon_loglog(ax):
    x = np.logspace(0, 3, 40)
    ax.loglog(x, x**1.6, lw=ICON_LW, color=ICON_LINE)
    ax.loglog(x, x**0.8, lw=ICON_LW, color=ICON_STRUCTURE)


# --------------------------------------------------------------- category


def icon_bar(ax):
    ax.bar(CATEGORIES, VALUES, width=0.72)


def icon_barh(ax):
    ax.barh(CATEGORIES, VALUES, width=0.72)


def icon_bar_stack(ax):
    ax.bar(CATEGORIES, RNG.uniform(0.2, 0.6, (5, 3)), width=0.72, stack=True)


def icon_bar_negpos(ax):
    ax.bar(CATEGORIES, SIGNED, width=0.72, negpos=True)


def icon_lollipop(ax):
    ax.lollipop(CATEGORIES, VALUES, marker="o", markersize=5, color=ICON_LINE)


def icon_lollipoph(ax):
    ax.lollipoph(CATEGORIES, VALUES, marker="o", markersize=5, color=ICON_LINE)


def icon_pie(ax):
    ax.pie(VALUES, np.zeros(5))


def icon_area(ax):
    ax.area(WAVE_X, np.abs(WAVES) + 0.2, alpha=0.9)


def icon_area_stack(ax):
    ax.area(WAVE_X, np.abs(WAVES) + 0.2, stack=True, alpha=0.9)


def icon_area_negpos(ax):
    ax.area(WAVE_X, WAVE, negpos=True, alpha=0.9)


# ----------------------------------------------------------- distribution


def icon_hist(ax):
    ax.hist(CLOUD[:, 0], bins=12, filled=True, alpha=0.9, color=ICON_LINE)


def icon_histh(ax):
    ax.histh(CLOUD[:, 0], bins=12, filled=True, alpha=0.9, color=ICON_LINE)


def icon_hist2d(ax):
    points = RNG.normal(size=(2, 4000))
    ax.hist2d(points[0], points[1], 16, cmap=ICON_DENSITY)


def icon_hexbin(ax):
    points = RNG.normal(size=(2, 4000))
    ax.hexbin(points[0], points[1], gridsize=10, cmap=ICON_DENSITY)


def icon_box(ax):
    ax.box(RNG.normal(size=(200, 3)) + [0, 0.7, -0.5], lw=0.9, showfliers=False)


def icon_boxh(ax):
    ax.boxh(RNG.normal(size=(200, 3)) + [0, 0.7, -0.5], lw=0.9, showfliers=False)


def icon_violin(ax):
    ax.violin(RNG.normal(size=(200, 3)) + [0, 0.7, -0.5], lw=0.9)


def icon_violinh(ax):
    ax.violinh(RNG.normal(size=(200, 3)) + [0, 0.7, -0.5], lw=0.9)


def icon_beeswarm(ax):
    ax.beeswarm(RNG.normal(size=(140, 3)) + [0, 0.7, -0.5], ms=4)


def icon_ridgeline(ax):
    data = [RNG.normal(size=200) + index * 0.5 for index in range(5)]
    ax.ridgeline(data, overlap=0.6, cmap=ICON_SEQUENTIAL, lw=0.7)


def icon_errorbars(ax):
    ax.plot(
        WAVE_X,
        SAMPLES,
        mean=True,
        shadestd=1,
        fadepctile=(10, 90),
        lw=ICON_LW,
        color=ICON_LINE,
    )


def icon_bars(ax):
    ax.plot(
        WAVE_X[::6],
        SAMPLES[:, ::6],
        mean=True,
        bars=True,
        lw=ICON_LW,
        color=ICON_LINE,
        barcolor=ICON_STRUCTURE,
        barlw=1.0,
    )


# --------------------------------------------------------------- 2D fields


def icon_pcolormesh(ax):
    ax.pcolormesh(smooth_field(), cmap=ICON_SEQUENTIAL)


def icon_pcolor(ax):
    ax.pcolor(smooth_field(14), cmap=ICON_SEQUENTIAL)


def icon_contour(ax):
    ax.contour(peak_field(), color=ICON_LINE, levels=7, lw=1.3)


def icon_contourf(ax):
    ax.contourf(smooth_field(), cmap=ICON_SEQUENTIAL, levels=9)


def icon_contour_labels(ax):
    ax.contour(
        peak_field(),
        color=ICON_LINE,
        levels=5,
        lw=1.2,
        labels=True,
        labels_kw={"fontsize": 5},
    )


def icon_imshow(ax):
    ax.imshow(smooth_field(24), cmap="dusk")


def icon_matshow(ax):
    ax.matshow(smooth_field(8), cmap="dusk")


def icon_spy(ax):
    ax.spy(RNG.random((18, 18)) > 0.82, markersize=1.8, color=ICON_LINE)


def icon_heatmap(ax):
    ax.heatmap(smooth_field(5), cmap=ICON_DIVERGING, vmin=-1.3, vmax=1.3)


def icon_heatmap_labels(ax):
    ax.heatmap(
        smooth_field(3).round(1),
        cmap=ICON_DIVERGING,
        vmin=-1.3,
        vmax=1.3,
        labels=True,
        labels_kw={"fontsize": 5.5},
    )


def icon_levels(ax):
    ax.pcolormesh(smooth_field(), cmap=ICON_SEQUENTIAL, levels=6)


def icon_continuous(ax):
    ax.pcolormesh(smooth_field(), cmap=ICON_SEQUENTIAL, discrete=False)


def icon_diverging(ax):
    ax.pcolormesh(
        smooth_field(),
        cmap=ICON_DIVERGING,
        values=uplt.arange(-1.2, 1.2, 0.3),
        extend="both",
    )


def icon_tripcolor(ax):
    x, y = RNG.uniform(0, 1, 60), RNG.uniform(0, 1, 60)
    ax.tripcolor(x, y, np.sin(6 * x) * np.cos(6 * y), cmap=ICON_SEQUENTIAL)


def icon_tricontourf(ax):
    x, y = RNG.uniform(0, 1, 150), RNG.uniform(0, 1, 150)
    ax.tricontourf(x, y, np.sin(5 * x) * np.cos(5 * y), cmap=ICON_SEQUENTIAL, levels=8)


# ------------------------------------------------------------ vector fields


def icon_quiver(ax):
    x, y, u, v = rotational_field(8)
    ax.quiver(x, y, u, v, color=ICON_LINE, width=0.013)


def icon_barbs(ax):
    x, y, u, v = rotational_field(5, extent=1.6)
    ax.barbs(
        x,
        y,
        u * 12,
        v * 12,
        np.hypot(u, v),
        cmap=ICON_SEQUENTIAL,
        length=4.5,
        linewidth=0.5,
    )


def icon_streamplot(ax):
    x, y, u, v = rotational_field(28)
    ax.streamplot(x, y, u, v, color=np.hypot(x, y), cmap=ICON_SEQUENTIAL, lw=0.8)


def icon_curved_quiver(ax):
    x, y, u, v = rotational_field(24)
    ax.curved_quiver(
        x,
        y,
        u,
        v,
        color=np.hypot(x, y),
        cmap=ICON_SEQUENTIAL,
        density=7,
        grains=7,
        linewidth=0.6,
        arrowsize=0.6,
    )


# ------------------------------------------------------ networks and polar


def icon_graph(ax):
    import networkx as nx

    ax.graph(
        nx.karate_club_graph(),
        layout="spring",
        layout_kw={"seed": 4},
        node_kw={"node_size": 18, "node_color": ICON_LINE, "linewidths": 0},
        edge_kw={"alpha": 0.35, "width": 0.6},
        label_kw={"font_size": 0},
    )


def icon_sankey(ax):
    ax.sankey(
        nodes=["A", "B", "C", "D"],
        flows=[("A", "B", 5.0, ""), ("A", "C", 3.0, ""), ("B", "D", 2.5, "")],
        style="budget",
        flow_labels=False,
        node_label_box=False,
    )


def icon_ribbon(ax):
    import pandas as pd

    rows = [
        {
            "id": identifier,
            "period": period,
            "topic": f"T{(identifier + period) % 4}",
            "value": 1.0,
        }
        for period in range(4)
        for identifier in range(12)
    ]
    with without_new_text(ax):
        ax.ribbon(pd.DataFrame(rows))


def icon_chord(ax):
    import pandas as pd

    names = list("ABCD")
    ax.chord_diagram(
        pd.DataFrame(RNG.integers(2, 10, (4, 4)), index=names, columns=names),
        ticks_interval=None,
        space=6,
    )


def icon_radar(ax):
    import pandas as pd

    frame = pd.DataFrame(
        {"a": [3.5, 4.2], "b": [4.2, 2.8], "c": [2.6, 4.4], "d": [3.9, 3.1]},
        index=["one", "two"],
    )
    with without_new_text(ax):
        ax.radar_chart(frame, vmin=0, vmax=5, fill=True, marker_size=2)


def icon_phylogeny(ax):
    ax.phylogeny(
        "(((A:1,B:1):1,(C:1,D:1):1):1,((E:1,F:1):1,(G:1,H:1):1):2);",
        leaf_label_size=0,
    )


def icon_taylor(ax):
    ax.format(
        rlim=(0, 1.6),
        corrlines=(1, 0.9, 0.6, 0),
        rlines=0.5,
        corrlabel="",
        ticklabelsize=4,
        labelsize=4,
    )
    ax.plot_corr(1, 1, marker="*", markersize=13, color="red7")
    for (corr, std), color in zip(
        ((0.95, 1.15), (0.8, 0.75)),
        ("denim", "green7"),
    ):
        ax.scatter_corr(corr, std, s=40, color=color, zorder=6)


# --------------------------------------------------------------------- maps
#
# Maps are the case where UltraPlot's integration shows: a projection short
# name, cartographic features as format keywords, and any plotting command on
# top in lon/lat. Each icon layers something over the map rather than showing
# an empty globe.


def _global_field(nlon=181, nlat=91):
    """
    A smooth global field in lon/lat, for the map icons to drape.
    """
    lon = np.linspace(-180, 180, nlon)
    lat = np.linspace(-90, 90, nlat)
    grid_lon, grid_lat = np.meshgrid(lon, lat)
    data = np.cos(np.deg2rad(grid_lat)) ** 2 * np.sin(
        np.deg2rad(2 * grid_lon)
    ) + 0.4 * np.sin(np.deg2rad(3 * grid_lat))
    return lon, lat, data


def icon_map_field(ax):
    lon, lat, data = _global_field()
    ax.pcolormesh(lon, lat, data, cmap=ICON_DIVERGING, levels=11, extend="both")
    ax.format(coast=True, coastlinewidth=0.4, labels=False, grid=False)


def icon_map_contour(ax):
    lon, lat, data = _global_field()
    ax.contourf(lon, lat, data, cmap=ICON_DIVERGING, levels=9, extend="both")
    ax.contour(lon, lat, data, levels=5, color="k", lw=0.35)
    ax.format(coast=True, coastlinewidth=0.4, labels=False, grid=False)


def icon_map_features(ax):
    ax.format(
        land=True,
        ocean=True,
        coast=True,
        borders=True,
        landcolor="gray3",
        oceancolor=ICON_LINE,
        coastlinewidth=0.35,
        labels=False,
        grid=True,
        gridalpha=0.4,
    )


def icon_map_scatter(ax):
    state = np.random.default_rng(7)
    lon = state.uniform(-170, 170, 45)
    lat = state.uniform(-70, 70, 45)
    ax.format(
        land=True,
        landcolor="gray3",
        coast=True,
        coastlinewidth=0.3,
        labels=False,
        grid=False,
    )
    ax.scatter(
        lon,
        lat,
        s=state.uniform(6, 40, 45),
        c=state.uniform(0, 1, 45),
        cmap=ICON_SEQUENTIAL,
        alpha=0.85,
        lw=0,
    )


def icon_map_quiver(ax):
    lon = np.linspace(-170, 170, 15)
    lat = np.linspace(-70, 70, 9)
    grid_lon, grid_lat = np.meshgrid(lon, lat)
    u = np.cos(np.deg2rad(grid_lat)) * 10
    v = np.sin(np.deg2rad(2 * grid_lon)) * 6
    ax.format(
        land=True,
        landcolor="gray2",
        coast=True,
        coastlinewidth=0.3,
        labels=False,
        grid=False,
    )
    ax.quiver(lon, lat, u, v, color=ICON_LINE, width=0.008)


def icon_map_track(ax):
    steps = np.linspace(0, 1, 120)
    lon = -140 + 260 * steps
    lat = 55 * np.sin(np.pi * steps) - 10
    ax.format(
        land=True,
        landcolor="gray3",
        ocean=True,
        oceancolor="#dce6f0",
        coast=True,
        coastlinewidth=0.3,
        labels=False,
        grid=False,
    )
    ax.plot(lon, lat, lw=1.8, color="red7")
    ax.scatter(lon[::40], lat[::40], s=14, color="red7", zorder=5)


#: name -> (draw, projection, kind, matplotlib counterpart, group)
#: Groups place an icon on the page: relational, distribution, field, vector,
#: network, keyword (what one argument does), swapped (the …h/…x siblings).
ICONS = {
    # -------------------------------------------------------- relational
    "plot": (icon_plot, None, SAME, None, "relational"),
    "scatter": (icon_scatter, None, SAME, None, "relational"),
    "step": (icon_step, None, SAME, None, "relational"),
    "stem": (icon_stem, None, SAME, None, "relational"),
    "vlines": (icon_vlines, None, SAME, None, "relational"),
    "hlines": (icon_hlines, None, SAME, None, "relational"),
    "loglog": (icon_loglog, None, SAME, None, "relational"),
    "parametric": (
        icon_parametric,
        None,
        BETTER,
        "LineCollection by hand",
        "relational",
    ),
    "bar": (icon_bar, None, SAME, None, "relational"),
    "barh": (icon_barh, None, SAME, None, "relational"),
    "lollipop": (
        icon_lollipop,
        None,
        BETTER,
        "stem, then markers by hand",
        "relational",
    ),
    "area": (icon_area, None, BETTER, "fill_between", "relational"),
    "pie": (icon_pie, None, SAME, None, "relational"),
    # ------------------------------------------------------ distribution
    "hist": (icon_hist, None, SAME, None, "distribution"),
    "hist2d": (icon_hist2d, None, SAME, None, "distribution"),
    "hexbin": (icon_hexbin, None, SAME, None, "distribution"),
    "box": (icon_box, None, SAME, None, "distribution"),
    "violin": (icon_violin, None, SAME, None, "distribution"),
    "beeswarm": (icon_beeswarm, None, NEW, None, "distribution"),
    "ridgeline": (icon_ridgeline, None, NEW, None, "distribution"),
    "errorbars": (
        icon_errorbars,
        None,
        BETTER,
        "errorbar, after you reduce",
        "distribution",
    ),
    # ------------------------------------------------------------- field
    "pcolormesh": (icon_pcolormesh, None, SAME, None, "field"),
    "pcolor": (icon_pcolor, None, SAME, None, "field"),
    "contour": (icon_contour, None, SAME, None, "field"),
    "contourf": (icon_contourf, None, SAME, None, "field"),
    "imshow": (icon_imshow, None, SAME, None, "field"),
    "matshow": (icon_matshow, None, SAME, None, "field"),
    "spy": (icon_spy, None, SAME, None, "field"),
    "heatmap": (icon_heatmap, None, BETTER, "imshow, then label each cell", "field"),
    "tripcolor": (icon_tripcolor, None, SAME, None, "field"),
    "tricontourf": (icon_tricontourf, None, SAME, None, "field"),
    # ------------------------------------------------------------ vector
    "quiver": (icon_quiver, None, SAME, None, "vector"),
    "barbs": (icon_barbs, None, SAME, None, "vector"),
    "streamplot": (icon_streamplot, None, SAME, None, "vector"),
    "curved_quiver": (icon_curved_quiver, None, NEW, None, "vector"),
    # ----------------------------------------------------------- network
    "graph": (icon_graph, None, BETTER, "networkx draws onto an axes", "network"),
    "sankey": (icon_sankey, None, BETTER, "matplotlib.sankey.Sankey", "network"),
    "ribbon": (icon_ribbon, None, NEW, None, "network"),
    "chord_diagram": (icon_chord, "polar", NEW, None, "network"),
    "radar_chart": (icon_radar, "polar", BETTER, "a polar plot, by hand", "network"),
    "phylogeny": (icon_phylogeny, "polar", NEW, None, "network"),
    "taylor": (icon_taylor, "taylor", NEW, None, "network"),
    # --------------------------------------------------------------- maps
    "proj='robin'": (
        icon_map_field,
        "robin",
        BETTER,
        "cartopy, wired up by hand",
        "maps",
    ),
    "proj='ortho'": (
        icon_map_contour,
        "ortho",
        BETTER,
        "cartopy, wired up by hand",
        "maps",
    ),
    "coast, land, ocean": (
        icon_map_features,
        "cyl",
        BETTER,
        "cartopy feature calls",
        "maps",
    ),
    "scatter on a map": (
        icon_map_scatter,
        "robin",
        BETTER,
        "transform= on every call",
        "maps",
    ),
    "quiver on a map": (
        icon_map_quiver,
        "cyl",
        BETTER,
        "transform= on every call",
        "maps",
    ),
    "plot on a map": (
        icon_map_track,
        "ortho",
        BETTER,
        "transform= on every call",
        "maps",
    ),
    # -------------------------------- what one keyword does to a command
    "bar(stack=True)": (
        icon_bar_stack,
        None,
        BETTER,
        "bottom=, cumulatively",
        "keyword",
    ),
    "bar(negpos=True)": (icon_bar_negpos, None, NEW, None, "keyword"),
    "area(stack=True)": (icon_area_stack, None, BETTER, "stackplot", "keyword"),
    "area(negpos=True)": (icon_area_negpos, None, NEW, None, "keyword"),
    "plot(bars=True)": (
        icon_bars,
        None,
        BETTER,
        "errorbar, after you reduce",
        "keyword",
    ),
    "contour(labels=True)": (icon_contour_labels, None, BETTER, "clabel", "keyword"),
    "heatmap(labels=True)": (
        icon_heatmap_labels,
        None,
        BETTER,
        "a loop of ax.text",
        "keyword",
    ),
    "pcolormesh(levels=6)": (icon_levels, None, BETTER, "BoundaryNorm", "keyword"),
    "pcolormesh(discrete=False)": (icon_continuous, None, SAME, None, "keyword"),
    "pcolormesh(values=)": (icon_diverging, None, BETTER, "TwoSlopeNorm", "keyword"),
    # ------------------------------------- the siblings that swap the axes
    "histh": (icon_histh, None, NEW, None, "swapped"),
    "boxh": (icon_boxh, None, BETTER, "boxplot(vert=False)", "swapped"),
    "violinh": (icon_violinh, None, BETTER, "violinplot(vert=False)", "swapped"),
    "lollipoph": (icon_lollipoph, None, NEW, None, "swapped"),
}


#: The commands the cheatsheet shows: two rows of fifteen, chosen to span the
#: kinds of plot rather than to be complete. The poster carries all of them.
FEATURED = (
    "plot",
    "scatter",
    "step",
    "stem",
    "bar",
    "barh",
    "area",
    "hist",
    "box",
    "violin",
    "parametric",
    "lollipop",
    "ridgeline",
    "beeswarm",
    "errorbars",
    "pcolormesh",
    "contour",
    "contourf",
    "imshow",
    "heatmap",
    "hexbin",
    "tripcolor",
    "quiver",
    "streamplot",
    "curved_quiver",
    "graph",
    "sankey",
    "chord_diagram",
    "radar_chart",
    "taylor",
    "proj='robin'",
    "scatter on a map",
)


def slug(name):
    """
    Turn a command signature into a file name.

    Names carry parentheses, quotes and spaces — ``proj='robin'`` — none of
    which belong in a path that Typst and Sphinx both have to reference.
    """
    name = name.strip()
    for old, new in (
        ("(", "-"),
        (")", ""),
        ("=", "-"),
        (",", "-"),
        ("'", ""),
        ('"', ""),
        (" ", "-"),
    ):
        name = name.replace(old, new)
    while "--" in name:
        name = name.replace("--", "-")
    return name.strip("-")


def write_manifest():
    """
    Emit the registry as Typst data, so the pages are built from this list.
    """
    import os

    path = os.path.join(ASSETS, "icons.typ")
    with open(path, "w") as handle:
        handle.write("// Generated by parts/icons.py — do not edit.\n")
        handle.write("#let commands = (\n")
        for name, (_, _, kind, mpl, group) in ICONS.items():
            mpl = f'"{mpl}"' if mpl else "none"
            handle.write(
                f'  (name: "{name.strip()}", file: "{slug(name)}", '
                f'kind: "{kind}", mpl: {mpl}, group: "{group}", '
                f"featured: {str(name in FEATURED).lower()}),\n"
            )
        handle.write(")\n")
    print("  assets/icons.typ")


def main():
    use_style(fontsize=5)
    failures = []
    for name, (draw, proj, _kind, _mpl, _group) in ICONS.items():
        # Nearly full bleed: a thin margin so the drawing breathes inside the
        # tile without the empty band tight layout used to leave. Projections
        # keep a little more room for their own circular frame.
        edge = "0.9mm" if proj is not None else "0.6mm"
        fig, ax = uplt.subplots(
            figwidth=SIZE,
            figheight=SIZE,
            proj=proj,
            tight=False,
            left=edge,
            right=edge,
            top=edge,
            bottom=edge,
        )
        try:
            draw(ax)
        except Exception as error:  # keep going; the build reports the gap
            failures.append(f"{name}: {type(error).__name__}: {error}")
            uplt.close(fig)
            continue
        if proj is None:
            bare(ax, linewidth=0)
            ax.margins(ICON_MARGIN)
        else:
            ax.format(grid=False, labelsize=0, ticklabelsize=0, title="")
        save(fig, f"icons/{slug(name)}.png", dpi=220)
    write_manifest()
    if failures:
        print("icon failures:")
        for failure in failures:
            print(f"  {failure}")


if __name__ == "__main__":
    main()
