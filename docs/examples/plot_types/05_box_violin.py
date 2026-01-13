"""
Box and violin plots
====================

Standard box and violin plots with automatic customization.

Why UltraPlot here?
-------------------
UltraPlot wraps :meth:`matplotlib.axes.Axes.boxplot` and :meth:`matplotlib.axes.Axes.violinplot`
with more convenient arguments (like ``fillcolor``, ``alpha``) and automatically applies
cycle colors to the boxes/violins.

Key functions: :py:meth:`ultraplot.axes.PlotAxes.boxplot`, :py:meth:`ultraplot.axes.PlotAxes.violinplot`.

See also
--------
* :doc:`1D statistics </stats>`
"""

import numpy as np

import ultraplot as uplt

# Generate sample data
data = [np.random.normal(0, std, 100) for std in range(1, 6)]

fig, axs = uplt.subplots(ncols=2, refwidth=3)

# Box plot
axs[0].boxplot(data, lw=1.5, fillcolor="gray4", medianlw=2)
axs[0].format(title="Box plot", xlabel="Distribution", ylabel="Value")

# Violin plot
axs[1].violinplot(data, lw=1, fillcolor="gray6", fillalpha=0.5)
axs[1].format(title="Violin plot", xlabel="Distribution", ylabel="Value")

axs.format(suptitle="Statistical distributions")
fig.show()
