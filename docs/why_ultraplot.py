# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [raw] raw_mimetype="text/restructuredtext"
# .. _why_ultraplot:
#
# Why UltraPlot?
# =============
#
# Matplotlib is an incredibly powerful plotting engine, but creating multi-panel,
# publication-ready figures often requires repetitive boilerplate code. UltraPlot
# solves this by adding a concise, intuitive layer for layout and formatting,
# while letting you keep the familiar Matplotlib object-oriented methods you
# already know.
#
# .. note::
#
#    If you just need a quick, exploratory plot, vanilla Matplotlib is perfect.
#    UltraPlot truly shines when you are managing multi-panel figures or need
#    consistent, publication-quality styling across your work.
#
# The comparison below uses a straightforward two-panel figure to illustrate the
# difference. This isn't about code golf or minimizing lines; it's about the
# separation of concerns. Matplotlib handles the plotting primitives, while
# UltraPlot gives you a streamlined syntax to orchestrate the broader figure layout.

# %% [raw] raw_mimetype="text/restructuredtext"
# Setting up the data
# -------------------
#
# To keep things fully reproducible without needing external downloads, we will
# generate some basic synthetic data locally. The data itself is intentionally
# simple so we can focus entirely on the plotting mechanics.

# %%
import numpy as np

SEED = 51423
rng = np.random.RandomState(SEED)
x = np.linspace(0, 10, 100)
line = np.sin(x) + 0.08 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))


# %% [raw] raw_mimetype="text/restructuredtext"
# The Matplotlib approach
# -----------------------
#
# Matplotlib's explicit API is fantastic when you need surgical control over every
# individual artist on the canvas. Here is how you would conventionally build and
# format this two-panel figure using standard Matplotlib.
#
# For a deep dive into this approach, see the `Matplotlib subplots tutorial
# <https://matplotlib.org/stable/plot_types/subplots.html>`__.

# %%
import matplotlib.pyplot as plt

mpl_fig, mpl_axs = plt.subplots(1, 2, figsize=(7, 3), constrained_layout=True)
mpl_axs[0].plot(x, line, label="signal", color="tab:blue")
mpl_axs[0].set(xlabel="x", ylabel="value", title="Line")
mpl_axs[0].legend(loc="upper right")
mpl_mesh = mpl_axs[1].imshow(image, origin="lower", aspect="auto", cmap="viridis")
mpl_axs[1].set(xlabel="column", ylabel="row", title="Image")
mpl_fig.colorbar(mpl_mesh, ax=mpl_axs[1], label="intensity")
mpl_fig.suptitle("The same two-panel figure")
mpl_fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# The UltraPlot approach
# ----------------------
#
# Notice that the actual drawing commands,
# :meth:`~ultraplot.axes.PlotAxes.plot` and
# :meth:`~ultraplot.axes.PlotAxes.imshow`, are identical to the Matplotlib
# version above. UltraPlot adds :func:`~ultraplot.ui.subplots` for figure
# construction and :meth:`~ultraplot.axes.Axes.format` for panel formatting.
#
# Instead of scattering setter methods across your script, UltraPlot lets you
# define figure layouts and shared labels cohesively. As your figures grow in
# complexity, this centralized formatting keeps your code clean and readable.
#
# Discover more in the :ref:`format command <ug_format>` guide and the
# :func:`~ultraplot.ui.subplots` API reference.

# %%
import ultraplot as uplt

uplt_fig, uplt_axs = uplt.subplots(ncols=2, share=False, refwidth=2.3)
uplt_axs[0].plot(x, line, label="signal", color="tab:blue")
uplt_mesh = uplt_axs[1].imshow(image, origin="lower", aspect="auto", cmap="viridis")
uplt_axs[0].format(title="Line", xlabel="x", ylabel="value")
uplt_axs[0].legend(loc="ur")
uplt_axs[1].format(title="Image", xlabel="column", ylabel="row")
uplt_fig.format(suptitle="The same two-panel figure")
uplt_fig.colorbar(uplt_mesh, loc="r", label="intensity")
uplt_fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# The takeaway
# ------------
#
# UltraPlot does not reinvent the wheel—it just makes it easier to steer. A good
# mental model for your workflow looks like this:
#
# * Use standard axes methods such as :meth:`~ultraplot.axes.PlotAxes.plot`,
#   :meth:`~ultraplot.axes.PlotAxes.imshow`, and
#   :meth:`~ultraplot.axes.PlotAxes.scatter` to draw data.
# * Use :meth:`~ultraplot.axes.Axes.format` through ``axs.format()`` to apply
#   consistent labels, ticks, and styling at the panel level.
# * Use :meth:`~ultraplot.figure.Figure.format` through ``fig.format()`` for
#   global aesthetics, and :meth:`~ultraplot.figure.Figure.colorbar` for a
#   shared colorbar.
#
# For a single, fast plot, stick with Matplotlib. When layout scaling and repetitive
# formatting become a chore, let UltraPlot handle the heavy lifting.
