"""
Shared axes and ABC labels
=========================

A multi-panel layout with shared limits, shared labels, and automatic panel labels.

Why UltraPlot here?
-------------------
UltraPlot shares limits and labels across a grid with a single ``share``/``span``
configuration, and adds panel letters automatically. This keeps complex layouts
consistent without the manual axis management required in base Matplotlib.

<<<<<<< HEAD
Key functions: :py:func:`ultraplot.ui.subplots`, :py:meth:`ultraplot.gridspec.SubplotGrid.format`.
=======
Key functions: :py:func:`ultraplot.subplots`, :py:meth:`ultraplot.gridspec.SubplotGrid.format`.
>>>>>>> 0f95f74c (Add gallery infrastructure and examples)

See also
--------
* :doc:`Subplots and layouts </subplots>`
"""

import numpy as np

import ultraplot as uplt

rng = np.random.default_rng(12)
x = np.linspace(0, 10, 300)

layout = [[1, 2, 3], [1, 2, 4], [1, 2, 5]]
fig, axs = uplt.subplots(
    layout,
)
for i, ax in enumerate(axs):
    noise = 0.15 * rng.standard_normal(x.size)
    y = np.sin(x + i * 0.4) + 0.2 * np.cos(2 * x) + 0.1 * i + noise
    ax.plot(x, y, lw=2)
    ax.scatter(x[::30], y[::30], s=18, alpha=0.65)

axs.format(
    abc="[A.]",
    xlabel="Time (s)",
    ylabel="Signal",
    suptitle="Shared axes with consistent limits and panel lettering",
    grid=False,
)

fig.show()
