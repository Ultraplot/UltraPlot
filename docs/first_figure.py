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
# .. _first_figure:
#
# Your first UltraPlot figure
# ===========================
#
# This short, runnable ladder builds one two-panel figure in five stages. Each
# stage is self-contained, so you can run it on its own while learning. The
# plotting methods are the familiar Matplotlib axes methods; UltraPlot's main
# contribution here is the layout and figure-wide formatting.

# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 1: choose a layout
# ------------------------
#
# Start by asking :func:`~ultraplot.ui.subplots` for two panels. ``axs`` is a
# convenient collection of axes that can be indexed from left to right.

# %%
import ultraplot as uplt

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 2: add data
# -----------------
#
# Add a line to the first panel and an image to the second. The data are
# deterministic and generated in memory, so this example has no network or
# heavyweight dependency.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto", cmap="viridis")
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 3: format the panels
# --------------------------
#
# ``format`` groups common labels and titles in one call. You can still use
# any ordinary axes plotting method alongside it.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto", cmap="viridis")
axs[0].format(title="Signal", xlabel="angle", ylabel="value")
axs[1].format(title="Image", xlabel="column", ylabel="row")
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 4: add guides and figure formatting
# -------------------------------------------
#
# A legend describes the line, while a colorbar describes the image. Guides
# belong to the figure because they help the reader interpret the panels.
# ``fig.format`` adds the shared title without repeating it on each axes.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto", cmap="viridis")
axs[0].format(title="Signal", xlabel="angle", ylabel="value")
axs[1].format(title="Image", xlabel="column", ylabel="row")
fig.format(suptitle="A first UltraPlot figure")
fig.legend(loc="t")
fig.colorbar(mesh, loc="r", label="intensity")
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 5: save the result
# ------------------------
#
# Once the figure looks right, save it with :meth:`~ultraplot.figure.Figure.save`.
# PNG is convenient for a quick preview; choose another extension when your
# publication or workflow calls for a different format.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto", cmap="viridis")
axs[0].format(title="Signal", xlabel="angle", ylabel="value")
axs[1].format(title="Image", xlabel="column", ylabel="row")
fig.format(suptitle="A first UltraPlot figure")
fig.legend(loc="t")
fig.colorbar(mesh, loc="r", label="intensity")
fig.save("first_figure.png")
