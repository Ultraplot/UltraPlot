#!/usr/bin/env python3
"""
Map figures: a few projections, and what ``format`` puts on them.

Needs cartopy. If it is missing the build skips this part rather than failing,
and the page falls back to the code column alone.
"""

from __future__ import annotations

import numpy as np

import ultraplot as uplt

from common import save, use_style

#: Projection short names, in the order they appear on the page.
PROJECTIONS = ("robin", "ortho", "npstere", "hammer", "eqearth", "lcc")


def _field():
    """
    A smooth global field to drape over the projections.
    """
    lon = np.linspace(-180, 180, 145)
    lat = np.linspace(-90, 90, 73)
    grid_lon, grid_lat = np.meshgrid(lon, lat)
    data = np.cos(np.deg2rad(grid_lat)) ** 2 * np.sin(
        np.deg2rad(2 * grid_lon)
    ) + 0.4 * np.sin(np.deg2rad(3 * grid_lat))
    return lon, lat, data


def projections():
    """
    One panel per projection, each labelled with the string that makes it.
    """
    lon, lat, data = _field()
    fig, axs = uplt.subplots(
        proj=PROJECTIONS,
        ncols=3,
        nrows=2,
        figwidth="120mm",
        figheight="52mm",
        wspace="3mm",
        hspace="5mm",
    )
    for ax, name in zip(axs, PROJECTIONS):
        mesh = ax.pcolormesh(lon, lat, data, cmap="roma", levels=11, extend="both")
        ax.format(
            coast=True,
            coastlinewidth=0.3,
            title=f"proj='{name}'",
            titlesize=5.6,
            titlepad=1.5,
            grid=True,
            gridalpha=0.25,
            labels=False,
        )
    fig.colorbar(
        mesh,
        loc="b",
        length=0.5,
        width="2.5mm",
        label="anomaly",
        labelsize=5.6,
        ticklabelsize=5,
    )
    save(fig, "geo_projections.png")


def features():
    """
    The cartographic features ``format`` can switch on, and gridline labels.
    """
    # Height is left to the layout solver: pinning both dimensions clips the
    # gridline labels, which have nowhere to go.
    fig, ax = uplt.subplots(proj="cyl", refwidth="72mm")
    ax.format(
        land=True,
        ocean=True,
        coast=True,
        borders=True,
        rivers=True,
        landcolor="gray3",
        oceancolor="denim",
        coastlinewidth=0.3,
        lonlim=(-15, 40),
        latlim=(33, 62),
        lonlabels="b",
        latlabels="l",
        labelsize=5.5,
        gridlabelsize=5.5,
        grid=True,
        gridalpha=0.3,
        title="",
        titlesize=5.6,
    )
    save(fig, "geo_features.png")


def main():
    try:
        import cartopy  # noqa: F401
    except ImportError:
        print("  (cartopy missing, skipping the map figures)")
        return
    use_style()
    projections()
    features()


if __name__ == "__main__":
    main()
