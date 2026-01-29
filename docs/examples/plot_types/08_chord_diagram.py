"""
Chord diagram
=============

UltraPlot wrapper around pyCirclize chord diagrams.
"""

import pandas as pd

import ultraplot as uplt

matrix = pd.DataFrame(
    [[10, 6, 2], [6, 12, 4], [2, 4, 8]],
    index=["A", "B", "C"],
    columns=["A", "B", "C"],
)

fig, ax = uplt.subplots(proj="polar", refwidth=3.6)
ax.chord_diagram(matrix, ticks_interval=None, space=4)
ax.format(title="Chord diagram")
fig.show()
