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
# .. _ug_data_aware:
#
# Data-aware plotting
# ===================
#
# UltraPlot recognizes labelled data from pandas and xarray. Pass a pandas
# Series or DataFrame directly to an axes method and UltraPlot can use its
# index, column names, and axis metadata to choose coordinates and labels.
# This keeps the plotting call focused on the data instead of repeating its
# description in several formatting arguments.
#
# The example below starts with a small, labelled DataFrame. The date index
# becomes the horizontal coordinate, and the column names become legend labels.

# %%
import numpy as np
import pandas as pd
import ultraplot as uplt

dates = pd.date_range("2025-01-01", periods=24, freq="MS")
season = np.sin(np.linspace(0, 2 * np.pi, dates.size))
data = pd.DataFrame(
    {
        "observed": 18 + 3 * season,
        "smoothed": 18 + 2.5 * season,
    },
    index=dates,
)
data.index.name = "Date"

fig, ax = uplt.subplots()
ax.plot(data)
ax.format(title="Monthly temperature", ylabel="Temperature (°C)")
ax.legend(loc="ur", ncols=1)


# %% [raw] raw_mimetype="text/restructuredtext"
# What UltraPlot inferred
# ------------------------
#
# The DataFrame index supplies the x coordinates, while its column labels are
# available to the legend. You can still override any inferred value with the
# usual plotting or :meth:`~ultraplot.axes.Axes.format` keyword arguments.
#
# For data arrays, coordinate inference works the same way with xarray. See the
# detailed :ref:`1D integration guide <ug_1dintegration>` and
# :ref:`2D integration guide <ug_2dintegration>` for MultiIndex data,
# DataArrays, and labelled two-dimensional plots.
