"""
Phylogeny
=========

UltraPlot wrapper around pyCirclize phylogeny plots.
"""

import ultraplot as uplt

newick = "((A,B),C);"

fig, ax = uplt.subplots(proj="polar", refwidth=3.2)
ax.phylogeny(newick, leaf_label_size=10)
ax.format(title="Phylogeny")
fig.show()
