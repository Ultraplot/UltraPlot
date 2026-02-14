"""
Semantic legends
================

Build legends from semantic mappings rather than existing artists.

Why UltraPlot here?
-------------------
UltraPlot adds semantic legend helpers directly on axes:
``cat_legend``, ``size_legend``, ``num_legend``, and ``geo_legend``.
These are useful when you want legend meaning decoupled from plotted handles.

Key functions: :py:meth:`ultraplot.axes.Axes.cat_legend`, :py:meth:`ultraplot.axes.Axes.size_legend`, :py:meth:`ultraplot.axes.Axes.num_legend`, :py:meth:`ultraplot.axes.Axes.geo_legend`.

See also
--------
* :doc:`Colorbars and legends </colorbars_legends>`
"""

# %%
import cartopy.crs as ccrs
import numpy as np
import shapely.geometry as sg
from matplotlib.path import Path

import ultraplot as uplt

np.random.seed(0)
data = np.random.randn(2, 100)
sizes = np.random.randint(10, 512, data.shape[1])
colors = np.random.rand(data.shape[1])

fig, ax = uplt.subplots()
ax.scatter(*data, color=colors, s=sizes, cmap="viko")
ax.format(title="Semantic legend helpers")

ax.cat_legend(
    ["A", "B", "C"],
    colors={"A": "red7", "B": "green7", "C": "blue7"},
    markers={"A": "o", "B": "s", "C": "^"},
    loc="top",
    frameon=False,
)
ax.size_legend(
    [10, 50, 200],
    loc="upper right",
    title="Population",
    ncols=1,
    frameon=False,
)
ax.num_legend(
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
ax.geo_legend(
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
fig.show()
