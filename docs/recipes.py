# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
# ---

# %% [raw] raw_mimetype="text/restructuredtext"
# .. _ug_recipes:
#
# Common figure recipes
# =====================
#
# These small, complete examples cover the patterns most figures need. Copy a
# recipe into a script or notebook and adapt the data and labels.

# %%
import numpy as np
import ultraplot as uplt


# %% [raw] raw_mimetype="text/restructuredtext"
# Labelled line
# -------------
# Use ``label`` on each artist and format the axes in one place.

# %%
x = np.linspace(0, 2 * np.pi, 200)
fig, ax = uplt.subplots(refwidth=3.2)
ax.plot(x, np.sin(x), label="sine")
ax.plot(x, np.cos(x), label="cosine")
ax.format(xlabel="angle", ylabel="value", title="Two signals")
ax.legend(loc="ur")


# %% [raw] raw_mimetype="text/restructuredtext"
# Shared-axis grid
# ----------------
# ``share="labels"`` keeps the grid readable while retaining tick labels.

# %%
fig, axs = uplt.subplots(nrows=2, ncols=2, refwidth=2.0, share="labels")
for number, ax in enumerate(axs, start=1):
    ax.plot(x, np.sin(x + number / 3), color=f"C{number - 1}")
    ax.format(title=f"Panel {number}")
axs.format(xlabel="x", ylabel="y", suptitle="A shared-axis grid")


# %% [raw] raw_mimetype="text/restructuredtext"
# Image with a colorbar
# ---------------------
# Plot the returned mappable and request an outer colorbar with
# :meth:`~ultraplot.axes.Axes.colorbar`.

# %%
image = np.outer(np.sin(x[:60]), np.cos(x[:60]))
fig, ax = uplt.subplots(refwidth=3.0)
ax.imshow(image, cmap="viridis", colorbar="r")
ax.format(title="Image data", xformatter="none", yformatter="none")


# %% [raw] raw_mimetype="text/restructuredtext"
# Figure-wide legend
# ------------------
# A :meth:`~ultraplot.figure.Figure.legend` collects labelled artists across
# the selected axes.

# %%
fig, axs = uplt.subplots(ncols=2, refwidth=2.2)
for ax, phase in zip(axs, (0, np.pi / 2)):
    ax.plot(x, np.sin(x + phase), label="signal")
    ax.plot(x, np.cos(x + phase), label="reference")
    ax.format(title=f"phase = {phase:.2g}")
fig.legend(loc="b", ncols=2)


# %% [raw] raw_mimetype="text/restructuredtext"
# Publication-sized export
# ------------------------
# Set a physical figure width and write a vector file for a manuscript with
# :meth:`~ultraplot.figure.Figure.save`.

# %%
fig, ax = uplt.subplots(figwidth="89mm", refaspect=1.6)
ax.plot(x, np.sin(x), color="C0")
ax.format(xlabel="angle", ylabel="value")
fig.save("figure.pdf")
