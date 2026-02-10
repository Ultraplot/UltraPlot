---
title: "ultraplot.constructor"
description: "T'he constructor functions used to build class instances from simple shorthand arguments."
source: "ultraplot/constructor.py"
---

`ultraplot.constructor`

T"he constructor functions used to build class instances from simple shorthand arguments.

## Public Classes

### `Cycle(cycler.Cycler)`

Generate and merge `~cycler.Cycler` instances in a variety of ways. The new generated class can be used to internally map keywords to the properties of the `~cycler.Cycler` instance. It is used by various plot functions to cycle through colors, linestyles, markers, etc.

## Public Functions

### `Colormap(*args, name=None, listmode='perceptual', filemode='continuous', discrete=False, cycle=None, save=False, save_kw=None, **kwargs)`

Generate, retrieve, modify, and/or merge instances of

### `Norm(norm, *args, **kwargs)`

Return an arbitrary `~matplotlib.colors.Normalize` instance. See this

### `Locator(locator, *args, discrete=False, **kwargs)`

Return a `~matplotlib.ticker.Locator` instance.

### `Formatter(formatter, *args, date=False, index=False, **kwargs)`

Return a `~matplotlib.ticker.Formatter` instance.

### `Scale(scale, *args, **kwargs)`

Return a `~matplotlib.scale.ScaleBase` instance.

### `Proj(name, backend=None, lon0=None, lon_0=None, lat0=None, lat_0=None, lonlim=None, latlim=None, **kwargs)`

Return a `cartopy.crs.Projection` or `~mpl_toolkits.basemap.Basemap` instance.
