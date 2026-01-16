"""
Robinson projection tracks
==========================

Global tracks plotted on a Robinson projection without external datasets.

Why UltraPlot here?
-------------------
UltraPlot creates GeoAxes with a single ``proj`` keyword and formats
geographic gridlines and features with ``format``. This avoids the verbose
cartopy setup typically needed in Matplotlib.

Key functions: :py:func:`ultraplot.subplots`, :py:meth:`ultraplot.axes.GeoAxes.format`.

See also
--------
* :doc:`Geographic projections </projections>`
"""

import cartopy.crs as ccrs
import numpy as np

import ultraplot as uplt

lon = np.linspace(-180, 180, 300)
lat_a = 25 * np.sin(np.deg2rad(lon * 1.5))
lat_b = -15 * np.cos(np.deg2rad(lon * 1.2))

fig, ax = uplt.subplots(proj="robin", proj_kw={"lon0": 0}, refwidth=4)
ax.plot(lon, lat_a, transform=ccrs.PlateCarree(), lw=2, label="Track A")
ax.plot(lon, lat_b, transform=ccrs.PlateCarree(), lw=2, label="Track B")
ax.scatter([-140, -40, 60, 150], [10, -20, 30, -5], transform=ccrs.PlateCarree())

ax.format(title="Global trajectories", lonlines=60, latlines=30)
ax.legend(loc="bottom", frame=False)

fig.show()
