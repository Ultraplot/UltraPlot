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

from matplotlib.path import Path
import numpy as np

import ultraplot as uplt

rng = np.random.default_rng(2)

fig, axs = uplt.subplots(nrows=2, ncols=2, refwidth=2.4, share=0)
axs.format(abc=True, abcloc="ul", grid=False, suptitle="Semantic legend helpers")

# Categorical legend
ax = axs[0, 0]
x = np.linspace(0, 2 * np.pi, 120)
ax.plot(x, np.sin(x), color="gray6", lw=1.5)
ax.cat_legend(
    ["A", "B", "C"],
    colors={"A": "red7", "B": "green7", "C": "blue7"},
    markers={"A": "o", "B": "s", "C": "^"},
    loc="ul",
    title="Category",
    frame=False,
)
ax.format(title="cat_legend", xlocator="null", ylocator="null")

# Size legend
ax = axs[0, 1]
vals = rng.normal(0, 1, 30)
ax.scatter(rng.uniform(0, 1, 30), vals, c="gray6", s=12, alpha=0.5)
ax.size_legend(
    [10, 50, 200],
    color="blue7",
    fmt="{:.0f}",
    loc="ur",
    ncols=1,
    title="Population",
    frame=False,
)
ax.format(title="size_legend", xlocator="null", ylocator="null")

# Numeric-color legend
ax = axs[1, 0]
z = rng.uniform(0, 1, 60)
ax.scatter(rng.uniform(0, 1, 60), rng.uniform(0, 1, 60), c=z, cmap="viko", s=16)
ax.num_legend(
    vmin=0,
    vmax=1,
    n=5,
    cmap="viko",
    fmt="{:.2f}",
    loc="ll",
    ncols=1,
    title="Score",
    frame=False,
)
ax.format(title="num_legend", xlocator="null", ylocator="null")

# Geometry legend
ax = axs[1, 1]
diamond = Path.unit_regular_polygon(4)
ax.geo_legend(
    [
        ("Triangle", "triangle", {"facecolor": "#6baed6"}),
        ("Diamond", diamond, {"facecolor": "#74c476"}),
        ("Hexagon", "hexagon", {"facecolor": "#fd8d3c"}),
    ],
    loc="lr",
    title="Geometry",
    handlesize=1.8,
    linewidth=1.0,
    frame=False,
)
ax.format(title="geo_legend", xlocator="null", ylocator="null")

fig.show()
