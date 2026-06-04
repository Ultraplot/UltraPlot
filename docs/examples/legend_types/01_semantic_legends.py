"""
Semantic legends
================
With UltraPlot semantic legends can be expressed in a flexible and cohesive manner with customg glyphs, latex and or spatial locations.
"""

# Semantic Legend with custom markers and advanced styles
import matplotlib.transforms as mtransforms
import numpy as np
from matplotlib.markers import CapStyle, JoinStyle, MarkerStyle
from matplotlib.path import Path

import ultraplot as uplt

star = Path.unit_regular_star(6)
circle = Path.unit_circle()
star_path = Path.unit_regular_star(5)
cut_star = Path(
    vertices=np.concatenate([circle.vertices, star.vertices[::-1, ...]]),
    codes=np.concatenate([circle.codes, star.codes]),
)

fig, ax = uplt.subplots()

# upper left legend with custom mark
ax.catlegend(
    ["star", "cus_star"],
    marker=[star_path, cut_star],
    markersize=10,
    add=True,
    loc="ul",
    title="Paths",
    ncols=1,
)

# upper right legend with advanced CapStyle and JoinStyle
ax.catlegend(
    ["butt / round", "round / miter", "projecting / bevel"],
    marker="1",
    markersize=10,
    markeredgecolor=list("gbr"),
    markeredgewidth=4,
    markerfacecoloralt="none",
    marker_capstyle=[
        CapStyle.butt,
        CapStyle.round,
        CapStyle.projecting,
    ],
    marker_joinstyle=[
        JoinStyle.round,
        JoinStyle.miter,
        JoinStyle.bevel,
    ],
    marker_transform=[mtransforms.Affine2D().rotate_deg(x) for x in [0, 30, 60]],
    title="Cap & Join Style",
    add=True,
    loc="ur",
    ncols=1,
)

# center geolegend with different styles
ax.geolegend(
    ["rect", "tri", "hex", "AU"],
    facecolor=["tab:red", "r", "k", "tab:blue"],
    ec=["k", "g", "orange", "bright pink"],
    loc="c",
    title="geolegend",
    ew=[0.5, 2, 1, 0.5],
    markersize=10,
    ncols=4,
    handletextpad=0.1,
    columnspacing=0.7,
)

# lower left legend with TeX symbols and rotation transform
ax.catlegend(
    ["\\infty", "\\sum", "\\int"],
    marker=[r"$\infty$", r"$\sum$", r"$\int$"],
    s=[6, 18, 9],  # ms/markersize=[6,8,10]
    title="TeX symbols\nwith rotation",
    marker_transform=[mtransforms.Affine2D().rotate_deg(x) for x in [30, 90, 45]],
    add=True,
    loc="ll",
    ncols=1,
)

# lower right legend with different fill style
ax.catlegend(
    ["top", "bottom", "left", "right"],
    marker="o",
    markersize=10,
    mfc=["r", "g", "b", "c"],
    markerfacecoloralt="lightsteelblue",
    markeredgecolor=["k", "r", "y", "b"],
    fillstyle=["top", "bottom", "left", "right"],
    title="Half filled",
    add=True,
    loc="lr",
    ncols=1,
)
ax.axis("off")
