"""
Taylor Diagram
==============

Taylor diagrams compare model skill with correlation coefficient, standard
deviation, and centered RMS difference in a single polar-style plot.

Why UltraPlot here?
-------------------
UltraPlot exposes Taylor diagrams as a projection, so you can create them with
``proj="taylor"`` and then use regular axes methods plus convenience methods
for plotting points from correlation and standard-deviation coordinates.

Key functions: :py:meth:`ultraplot.axes.TaylorAxes.plot_corr`,
:py:meth:`ultraplot.axes.TaylorAxes.scatter_corr`.

See also
--------
* :doc:`Geographic and polar axes </projections>`
"""

import numpy as np

import ultraplot as uplt

models = ("Control", "Physics A", "Physics B", "Ensemble")
correlation = np.array([0.73, 0.84, 0.91, 0.96])
stddev = np.array([0.82, 1.18, 1.05, 0.93])
colors = ("blue7", "orange7", "green7", "violet7")

fig, ax = uplt.subplots(proj="taylor", refwidth=4.2)
ax.format(
    title="Model skill summary",
    xlabel="Standard deviation",
    ylabel="",
    corrlabel="Correlation",
    rlim=(0, 1.5),
    rlines=0.25,
    corrlines=(1, 0.95, 0.9, 0.8, 0.6, 0.4, 0.2, 0),
)

# Centered RMS-difference contours around the reference point at (corr=1, std=1).
theta = np.linspace(0, np.pi / 2, 160)
radius = np.linspace(0, 1.5, 160)
theta_grid, radius_grid = np.meshgrid(theta, radius)
rms = np.sqrt(1 + radius_grid**2 - 2 * radius_grid * np.cos(theta_grid))
contours = ax.contour(
    theta_grid,
    radius_grid,
    rms,
    levels=(0.25, 0.5, 0.75, 1.0, 1.25),
    cmap="tokyo",
    lw=0.9,
    ls="--",
)
ax.clabel(contours, levels=(0.5, 1.0), inline=True, fontsize=8, fmt="%.1f")

ax.plot_corr(1, 1, marker="*", markersize=12, color="red7", label="Reference")
for name, corr, std, color in zip(models, correlation, stddev, colors):
    ax.scatter_corr(
        corr,
        std,
        s=75,
        color=color,
        edgecolor="white",
        lw=0.8,
        zorder=4,
        label=name,
    )

ax.legend(loc="b", ncols=3, frame=False)
fig.show()
