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
# Your First UltraPlot Figure
# ===========================
#
# UltraPlot is designed to make creating complex Matplotlib figures simpler and
# more intuitive. This tutorial builds a two-panel figure in five stages.
# Because each stage is self-contained, you can run them individually while
# seeing exactly how UltraPlot removes standard Matplotlib boilerplate and
# automates layout generation.

# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 1: Choose a layout
# ------------------------
#
# In standard Matplotlib, you generally have to guess a ``figsize`` tuple,
# which requires tedious trial and error anytime you add or remove subplots.
# UltraPlot calculates the figure size dynamically. By setting ``refwidth=2.4``,
# you simply define the width of a single reference panel, and UltraPlot
# automatically scales the entire figure to fit your rows and columns perfectly.

# %%
import ultraplot as uplt

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 2: Add data
# -----------------
#
# While UltraPlot revolutionizes the figure layout, the actual plotting
# commands are completely identical to Matplotlib. Because UltraPlot axes
# are directly built upon Matplotlib axes, you can use standard methods like
# ``plot()`` and ``imshow()`` with absolutely zero learning curve.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto")
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 3: Format the panels
# --------------------------
#
# This is where UltraPlot drastically reduces boilerplate code. In Matplotlib,
# formatting these two axes would require six separate lines of code (using
# ``set_title()``, ``set_xlabel()``, and ``set_ylabel()``). UltraPlot introduces
# a unified ``format()`` method, allowing you to configure titles, labels,
# limits, and styling all in a single, readable function call per axis.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto")
axs[1].colorbar(mesh, label="Intensity", loc="r")
axs[0].format(title="Signal", xlabel="angle", ylabel="value")
axs[1].format(title="Image", xlabel="column", ylabel="row")
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 4: Add guides and figure formatting
# -----------------------------------------
#
# Adding colorbars and legends in Matplotlib is notorious for ruining layouts—they
# often overlap with data or require tedious ``GridSpec`` wrangling. UltraPlot
# solves this natively. By passing simple location strings like ``loc="t"`` (top)
# or ``loc="r"`` (right) to figure-level guide commands, UltraPlot allocates
# dedicated space *outside* the subplots without shrinking or distorting your axes.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto", colorbar = "lr", colorbar_kw = dict(label = "Intensity"))
axs[0].format(title="Signal", xlabel="angle", ylabel="value")
axs[1].format(title="Image", xlabel="column", ylabel="row")
#
fig.format(suptitle="A first UltraPlot figure")
fig.legend(loc="b")
fig.show()


# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 5: Save the result
# ------------------------
#
# Saving the figure is just as straightforward. Unlike standard Matplotlib, where
# you frequently have to pass ``bbox_inches="tight"`` to prevent labels and guides
# from being cut off, UltraPlot's automated layout engine guarantees that your
# saved file will automatically have perfectly tight margins.

# %%
import numpy as np
import ultraplot as uplt

rng = np.random.RandomState(2024)
x = np.linspace(0, 2 * np.pi, 100)
signal = np.sin(x) + 0.06 * rng.randn(x.size)
image = np.outer(np.sin(x / 2), np.cos(x / 3))

fig, axs = uplt.subplots(ncols=2, share=False, refwidth=2.4)
axs[0].plot(x, signal, label="signal")
mesh = axs[1].imshow(image, origin="lower", aspect="auto", colorbar = "ur", colorbar_kw = dict(label = "Intensity"))
axs[0].format(title="Signal", xlabel="angle", ylabel="value")
axs[1].format(title="Image", xlabel="column", ylabel="row")
fig.format(suptitle="A first UltraPlot figure")
fig.legend(loc="b")
fig.save("first_figure.png")

# %% [raw] raw_mimetype="text/restructuredtext"
# Stage 6: The Grand Finale
# -------------------------
#
# To truly see UltraPlot's power, let's create a complex, publication-ready
# figure. In standard Matplotlib, combining a custom mosaic layout, a geographic
# projection, an inset axes, and A-B-C panel labels usually results in hundreds
# of lines of fragile ``GridSpec`` and ``transform`` code.
#
# UltraPlot condenses all of this into a highly readable, declarative script.
# Notice how we assign a projection to just one panel using a dictionary,
# add an inset using a simple location string, and auto-generate our panel
# labels with a single ``abc=True`` argument.

# %%
import numpy as np
import ultraplot as uplt

# 1. Generate synthetic scientific data
rng = np.random.RandomState(2024)
lon, lat = np.linspace(-180, 180, 100), np.linspace(-90, 90, 100)
lon2d, lat2d = np.meshgrid(lon, lat)
# A pseudo-spatial anomaly pattern
geo_data = np.cos(np.radians(lat2d)) * np.sin(np.radians(lon2d * 2))
time = np.linspace(0, 10, 200)
series1 = np.sin(time) * np.exp(-time / 5)
series2 = np.cos(time) * np.exp(-time / 5)

# Use a Cartesian panel as the square reference. The map keeps its native
# Robinson aspect while the right-hand plots remain readable in a tall figure.
layout = [[1, 2], [1, 2], [1, 3], [1, 3]]

# 3. Create the figure
# Apply a Robinson projection only to the first panel.
fig, axs = uplt.subplots(
    layout,
    proj={1: 'robin'},
    share=0,
    refnum=2,
    refwidth=1.5,
    wratios=(3.25, 1),
    # The two right-hand axes span rows (0, 1) and (2, 3), respectively.
    # Only the middle boundary separates them.
    hspace=('0pt', '13em', '0pt'),
)

# 4. Geographic data
m = axs[0].contourf(
    lon, lat, geo_data,
    cmap='marine',
    levels=15,
)

axs[0].format(
    land=True,
    borders=True,
    labels=True,
    lonlines=120,
    latlines=45,
    labelsize=12,
    title='Global Spatial Anomaly',
    title_kw={'fontsize': 14},
)

# A geographic callout is useful for showing a local-scale pattern without
# sacrificing the global view. These deterministic points mimic city readings.
paris = (2.3522, 48.8566)
paris_rng = np.random.RandomState(99)
paris_lon = paris[0] + paris_rng.normal(scale=0.65, size=36)
paris_lat = paris[1] + paris_rng.normal(scale=0.45, size=36)
paris_value = np.hypot(paris_lon - paris[0], paris_lat - paris[1])
paris_ax = axs[0].hawkeye(
    (0.43, 0.68),
    size=0.45,
    anchor='ur',
    proj='merc',
    extent=(-0.8, 5.5, 46.8, 50.8),
    shape='circle',
    target='circle',
    connector='line',
    color='red7',
    indicator_kw={'linewidth': 1.4},
)
paris_ax.format(land=True, landcolor='gray8', borders=True)
paris_ax.scatter(
    paris_lon,
    paris_lat,
    c=paris_value,
    cmap='fire',
    markersize=24,
    edgecolor='white',
    linewidth=0.35,
    transform='cyl',
    absolute_size = True,
)
paris_ax.plot(
    *paris,
    marker='*',
    markersize=9,
    color='red7',
    markeredgecolor='white',
    markeredgewidth=0.6,
    transform='cyl',
)

axs[0].colorbar(
    m,
    loc='b',
    label='Anomaly magnitude',
    length=0.8,
    labelsize = 14
)

# 5. Scatter data with inset
x = rng.rand(100)
y = x + rng.randn(100) * 0.2

axs[1].scatter(
    x, y,
    c=x,
    cmap='fire',
    markersize=15,
    alpha=0.7,
)

axs[1].format(
    title='Correlation Profile',
    xlabel='Predictor',
    ylabel='Response',
    xlocator=(0, 0.5, 1),
    ylocator=(0, 0.5, 1),
    xtickminor=False,
    ytickminor=False,
    ticklabelsize=10,
    labelsize=12,
    title_kw={'fontsize': 12},
)

ax_ins = axs[1].inset([0.55, 0.55, 0.35, 0.35], zoom=False)
ax_ins.hist(x, bins=10, color='gray5', edgecolor='black')
ax_ins.format(
    titleloc='uc',
    grid=False,
    xtickminor=False,
    ytickminor=False,
)

# 6. Time series
axs[2].plot(time, series1, label='Model Alpha')
axs[2].plot(time, series2, label='Model Beta')

axs[2].format(
    title='Temporal Decay',
    xlabel='Time (s)',
    ylabel='Amplitude',
    xlocator=(0, 5, 10),
    ylocator=(-0.5, 0, 0.5, 1),
    xtickminor=False,
    ytickminor=False,
    ticklabelsize=10,
    labelsize=12,
    title_kw={'fontsize': 12},
)

axs[2].legend(
    loc='ur',
    frame=False,
    fontsize=6,
    ncols = 1,
)

# 7. Figure-wide formatting
fig.format(
    suptitle='Putting It All Together',
    suptitle_kw={'fontsize': 15},
    abc=True,
    abcloc='ul',
    abcstyle='(a)',
    abc_kw={'fontsize': 11},
)

fig.save('complex_figure.png', dpi=150)
