"""
Spanning labels with shared axes
===============================

Demonstrate shared labels across a row of related subplots.

Why UltraPlot here?
-------------------
UltraPlot can span labels across subplot groups while keeping axis limits shared.
This avoids manual ``fig.supxlabel`` placement and reduces label clutter.

Key functions: :py:func:`ultraplot.subplots`, :py:meth:`ultraplot.gridspec.SubplotGrid.format`.

See also
--------
* :doc:`Subplots and layouts </subplots>`
"""

import numpy as np

import ultraplot as uplt

rng = np.random.default_rng(21)
x = np.linspace(0, 5, 300)

fig, axs = uplt.subplots(ncols=3, share="labels", span=True, refwidth=2.1)
for i, ax in enumerate(axs):
    trend = (i + 1) * 0.2
    y = np.exp(-0.4 * x) * np.sin(2 * x + i * 0.6) + trend
    y += 0.05 * rng.standard_normal(x.size)
    ax.plot(x, y, lw=2)
    ax.fill_between(x, y - 0.15, y + 0.15, alpha=0.2)
    ax.set_title(f"Condition {i + 1}")

axs.format(
    xlabel="Time (days)",
    ylabel="Normalized response",
    abc=True,
    abcloc="ul",
    suptitle="Spanning labels with shared axes",
    grid=False,
)

fig.show()
