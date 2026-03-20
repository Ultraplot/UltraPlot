"""
Semantic legends
================

Build legends from semantic mappings rather than existing artists.

Why UltraPlot here?
-------------------
UltraPlot adds semantic legend helpers directly on axes:
``entrylegend``, ``catlegend``, ``sizelegend``, ``numlegend``, and ``geolegend``.
These are useful when you want legend meaning decoupled from plotted handles, or
when you want a standalone semantic key that describes an encoding directly.

Key functions: :py:meth:`ultraplot.axes.Axes.entrylegend`, :py:meth:`ultraplot.axes.Axes.catlegend`, :py:meth:`ultraplot.axes.Axes.sizelegend`, :py:meth:`ultraplot.axes.Axes.numlegend`, :py:meth:`ultraplot.axes.Axes.geolegend`.

See also
--------
* :doc:`Colorbars and legends </colorbars_legends>`
"""

# %%
import cartopy.crs as ccrs
import shapely.geometry as sg

import ultraplot as uplt

fig, ax = uplt.subplots(refwidth=5.0)
ax.format(title="Semantic legend helpers")

ax.entrylegend(
    [
        {
            "label": "Observed samples",
            "line": False,
            "marker": "o",
            "markersize": 8,
            "markerfacecolor": "blue7",
            "markeredgecolor": "black",
        },
        {
            "label": "Model fit",
            "line": True,
            "color": "black",
            "linewidth": 2.5,
            "linestyle": "--",
        },
    ],
    loc="l",
    title="Entry styles",
    frameon=False,
)
ax.catlegend(
    ["A", "B", "C"],
    colors={"A": "red7", "B": "green7", "C": "blue7"},
    markers={"A": "o", "B": "s", "C": "^"},
    loc="top",
    frameon=False,
)
ax.sizelegend(
    [10, 50, 200],
    labels=["Small", "Medium", "Large"],
    loc="upper right",
    title="Population",
    ncols=1,
    frameon=False,
)
ax.numlegend(
    vmin=0,
    vmax=1,
    n=5,
    cmap="viko",
    fmt="{:.2f}",
    loc="ll",
    ncols=1,
    frameon=False,
)

poly1 = sg.Polygon([(0, 0), (2, 0), (1.2, 1.4)])
ax.geolegend(
    [
        ("Triangle", "triangle"),
        ("Triangle-ish", poly1),
        ("Australia", "country:AU"),
        ("Netherlands (Mercator)", "country:NLD", "mercator"),
        (
            "Netherlands (Lambert)",
            "country:NLD",
            {
                "country_proj": ccrs.LambertConformal(
                    central_longitude=5,
                    central_latitude=52,
                ),
                "country_reso": "10m",
                "country_territories": False,
                "facecolor": "steelblue",
                "fill": True,
            },
        ),
    ],
    loc="r",
    ncols=1,
    handlesize=2.4,
    handletextpad=0.35,
    frameon=False,
    country_reso="10m",
)
ax.axis("off")
fig.show()
