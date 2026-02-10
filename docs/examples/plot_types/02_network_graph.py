"""
Network graph styling
=====================

Render a network with node coloring by degree and clean styling.

Why UltraPlot here?
-------------------
UltraPlot wraps NetworkX drawing with a single ``ax.graph`` call and applies
sensible defaults for size, alpha, and aspect. This removes a lot of boilerplate
around layout and styling.

Key functions: :py:meth:`ultraplot.axes.PlotAxes.graph`, :py:meth:`ultraplot.figure.Figure.colorbar`.

See also
--------
* :doc:`Networks </networks>`
"""

import networkx as nx
import numpy as np

import ultraplot as uplt

g = nx.karate_club_graph()
degrees = np.array([g.degree(n) for n in g.nodes()])

fig, ax = uplt.subplots(refwidth=3.2)
nodes, edges, labels = ax.graph(
    g,
    layout="spring",
    layout_kw={"seed": 4},
    node_kw={
        "node_color": degrees,
        "cmap": "viko",
        "edgecolors": "black",
        "linewidths": 0.6,
        "node_size": 128,
    },
    edge_kw={
        "alpha": 0.4,
        "width": [np.random.rand() * 4 for _ in range(len(g.edges()))],
    },
    label_kw={"font_size": 7},
)
ax.format(title="Network connectivity", grid=False)
ax.margins(0.15)
fig.colorbar(
    nodes,
    ax=ax,
    loc="r",
    label="Node degree",
    length=0.33,
    align="top",
)

fig.show()
