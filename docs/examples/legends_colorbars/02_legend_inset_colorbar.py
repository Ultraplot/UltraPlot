"""
Legend with inset colorbar
==========================

Combine a multi-line legend with a compact inset colorbar.

Why UltraPlot here?
-------------------
UltraPlot supports inset colorbars via simple location codes while keeping
legends lightweight and aligned. This keeps focus on the data without resorting
to manual axes transforms.

Key functions: :py:meth:`ultraplot.axes.PlotAxes.legend`, :py:meth:`ultraplot.axes.Axes.colorbar`.

See also
--------
* :doc:`Colorbars and legends </colorbars_legends>`
"""

import numpy as np

import ultraplot as uplt

rng = np.random.default_rng(3)
x = np.linspace(0, 4 * np.pi, 400)

fig, ax = uplt.subplots(refwidth=3.4)
for i, phase in enumerate([0.0, 0.6, 1.2, 1.8]):
    ax.plot(x, np.sin(x + phase), lw=2, label=f"Phase {i + 1}")

scatter_x = rng.uniform(0, x.max(), 80)
scatter_y = np.sin(scatter_x) + 0.2 * rng.standard_normal(scatter_x.size)
depth = np.linspace(0, 1, scatter_x.size)
points = ax.scatter(scatter_x, scatter_y, c=depth, cmap="Fire", s=40, alpha=0.8)

ax.format(xlabel="Time (s)", ylabel="Amplitude", title="Signals with phase offsets")
ax.legend(loc="upper right", ncols=2, frame=False)
ax.colorbar(points, loc="ll", label="Depth")

fig.show()
