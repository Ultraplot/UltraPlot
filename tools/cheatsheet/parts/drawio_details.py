#!/usr/bin/env python3
"""Sharing comparisons, semantic legends and geography for the draw.io sheet."""
import numpy as np
import ultraplot as uplt
from common import ACCENT, bare, save, use_style


def sharing():
    for name, level in (("none", False), ("limits", "limits"), ("all", "all")):
        fig, axs = uplt.subplots(nrows=2, ncols=2, figwidth="48mm",
                                 figheight="43mm", share=level,
                                 span=level is not False, wspace="6mm", hspace="6mm")
        for i, ax in enumerate(axs):
            row, col = divmod(i, 2)
            x = np.linspace(0, 5 * (col + 1), 80)
            ax.plot(x, (row + 1) * np.sin(x), color=ACCENT, lw=2.3)
        axs.format(xlabel="X", ylabel="Y", labelsize=8,
                   ticklabelsize=6.5, xlocator=5, ylocator=2, grid=False)
        if level == "all":
            # Explicit label groups centre labels over the whole grid even
            # when global numeric sharing uses a single parent axes.
            axs.share_labels(axis="both")
        save(fig, f"drawio/sharing_{name}.png")


def legends():
    for kind in ("cat", "size", "num", "entry"):
        fig, ax = uplt.subplots(figwidth="43mm", figheight="34mm")
        bare(ax, linewidth=0)
        kw = dict(loc="c", ncols=1, frame=False, fontsize=11)
        if kind == "cat":
            ax.catlegend(["Control", "Treatment", "Reference"],
                         colors=["#3b638c", "#c47a50", "#548348"],
                         markers=["o", "s", "^"], markersize=12, **kw)
        elif kind == "size":
            ax.sizelegend([12, 60, 150], labels=["Small", "Medium", "Large"],
                          markercolor=ACCENT, labelspacing="1.3em", **kw)
        elif kind == "num":
            ax.numlegend(levels=[0, .25, .5, .75, 1], cmap="batlow", fmt="{:.2f}", **kw)
        else:
            ax.entrylegend([
                {"label": "Observed", "line": False, "marker": "o", "color": ACCENT},
                {"label": "Model", "line": True, "linestyle": "--", "color": "gray7"},
                {"label": "Reference", "line": True, "color": "#c47a50"},
            ], **kw)
        save(fig, f"drawio/legend_{kind}.png")


def geography():
    lon = np.linspace(-180, 180, 145)
    lat = np.linspace(-90, 90, 73)
    grid_lon, grid_lat = np.meshgrid(lon, lat)
    values = (np.cos(np.deg2rad(grid_lat)) ** 2 * np.sin(np.deg2rad(2 * grid_lon))
              + .4 * np.sin(np.deg2rad(3 * grid_lat)))
    fig, ax = uplt.subplots(proj="robin", figwidth="57mm", figheight="36mm")
    ax.pcolormesh(lon, lat, values, cmap="roma", levels=9, colorbar="b",
                  colorbar_kw={"width": "2mm", "length": .8, "ticklabelsize": 5})
    ax.format(coast=True, coastlinewidth=.6, grid=True, labels=False)
    save(fig, "drawio/geography.png")


def regional_map():
    # This longitude/latitude extent is nearly square in Mercator coordinates.
    # Let the projection determine the axes aspect; never stretch the image.
    fig, ax = uplt.subplots(proj="merc", refwidth="42mm")
    ax.format(land=True, ocean=True, coast=True, borders=True, rivers=True,
              landcolor="gray3", oceancolor="denim", coastlinewidth=.6,
              lonlim=(-15, 40), latlim=(30, 63), lonlabels="b", latlabels="l",
              labelsize=6, gridlabelsize=8, lonlocator=20, latlocator=10, grid=True, gridalpha=.3)
    save(fig, "drawio/regional_map.png")


def colormap_samples():
    """Cache registered colormap samples for editable draw.io swatches."""
    import json
    from pathlib import Path
    from matplotlib.colors import to_hex
    from common import ASSETS

    groups = {
        "Sequential": ["fire", "batlow", "thermal"],
        "Diverging": ["roma", "vik", "balance"],
        "Cyclic": ["phase", "romaO", "vikO"],
    }
    samples = {}
    for group, names in groups.items():
        samples[group] = [
            {"name": name, "colors": [to_hex(uplt.Colormap(name)(v))
                                       for v in np.linspace(0, 1, 48)]}
            for name in names
        ]
    target = Path(ASSETS) / "drawio" / "colormaps.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(samples, indent=2) + "\n")


def main():
    use_style()
    sharing()
    legends()
    colormap_samples()
    try:
        import cartopy  # noqa: F401
    except ImportError:
        print("  (cartopy missing, skipping draw.io geography specimen)")
    else:
        geography()
        regional_map()


if __name__ == "__main__":
    main()
