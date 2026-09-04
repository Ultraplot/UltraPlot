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
# Matplotlib is a powerful plotting library. UltraPlot keeps its familiar
# object-oriented plotting methods and adds a small layer for arranging and
# formatting complete figures. This page uses one deterministic, two-panel
# example to make that distinction concrete.
#
# .. note::
#
#    UltraPlot is most useful when a figure has several panels or needs
#    repeated, publication-oriented formatting. A one-panel exploratory plot
#    may not need UltraPlot at all; plain Matplotlib is an excellent choice.
#
# The comparison below is intentionally fair: both versions plot the same
# line and image, use the same labels, and add the same colorbar. The point is
# not to count lines of code. Matplotlib and UltraPlot have different
# responsibilities: Matplotlib supplies the plotting primitives, while
# UltraPlot makes figure-level layout and consistent formatting easier to
# express.

# %% [raw] raw_mimetype="text/restructuredtext"
# The shared data
# ---------------
#
# The data are generated locally so the examples are reproducible and do not
# require a download. The line and image are deliberately simple enough to
# understand before looking at the plotting code.

# %%
import numpy as np

SEED = 51423
rng = np.random.RandomState(SEED)
x = np.linspace(0, 10, 100)
line = np.sin(x) + 0.08 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))


# %% [raw] raw_mimetype="text/restructuredtext"
# Matplotlib
# ----------
#
# Matplotlib's explicit axes and figure calls are a good fit when you want
# fine-grained control over each artist. The code below is a complete,
# conventional Matplotlib solution.
#
# See the `Matplotlib subplots tutorial
# <https://matplotlib.org/stable/plot_types/subplots.html>`__ for the
# underlying interface.

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
# UltraPlot
# ---------
#
# The plotting calls remain ordinary axes methods. The difference is that
# ``uplt.subplots`` and ``format`` let the figure layout and shared labels be
# described together. This is particularly handy when the number of panels
# grows: the intent of the figure stays in one place instead of being spread
# over many setter calls.
#
# See the :ref:`format command <ug_format>` and the
# :func:`~ultraplot.ui.subplots` API reference for more options.

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
# What to take away
# -----------------
#
# UltraPlot does not replace Matplotlib's plotting vocabulary. A useful mental
# model is:
#
# * use normal axes methods such as ``plot`` and ``imshow`` to draw data;
# * use ``axs.format`` for consistent panel-level labels and styling; and
# * use ``fig.format`` and figure guides when the whole figure must agree.
#
# For a quick one-panel question, start with Matplotlib. When layout and
# formatting become the recurring work, UltraPlot can remove that friction
# while keeping the Matplotlib object model.
