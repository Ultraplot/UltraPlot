"""
Map projections and features
============================

Compare different map projections and add geographic features.

Why UltraPlot here?
-------------------
UltraPlot's :class:`~ultraplot.axes.GeoAxes` supports many projections via
``proj`` and makes adding features like land, ocean, and borders trivial
via :meth:`~ultraplot.axes.GeoAxes.format`.

Key functions: :py:func:`ultraplot.subplots`, :py:meth:`ultraplot.axes.GeoAxes.format`.

See also
--------
* :doc:`Geographic projections </projections>`
"""

import ultraplot as uplt

# Projections to compare
projs = ["moll", "ortho", "kav7"]

fig, axs = uplt.subplots(ncols=3, proj=projs, refwidth=3, share = 0)

# Format all axes with features
# land=True, coast=True, etc. are shortcuts for adding cartopy features
axs.format(
    land=True,
    landcolor="bisque",
    ocean=True,
    oceancolor="azure",
    coast=True,
    borders=True,
    labels=True,
    suptitle="Projections and features",
)

axs[0].format(title="Mollweide")
axs[1].format(title="Orthographic")
axs[2].format(title="Kavrayskiy VII")

fig.show()
