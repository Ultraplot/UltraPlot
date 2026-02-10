---
title: "ultraplot.colors"
description: "Various colormap classes and colormap normalization classes."
source: "ultraplot/colors.py"
---

`ultraplot.colors`

Various colormap classes and colormap normalization classes.

## Public Classes

### `ContinuousColormap(mcolors.LinearSegmentedColormap, _Colormap)`

Replacement for `~matplotlib.colors.LinearSegmentedColormap`.

### `DiscreteColormap(mcolors.ListedColormap, _Colormap)`

Replacement for `~matplotlib.colors.ListedColormap`.

### `PerceptualColormap(ContinuousColormap)`

A `ContinuousColormap` with linear transitions across hue, saturation,

### `DiscreteNorm(mcolors.BoundaryNorm)`

Meta-normalizer that discretizes the possible color values returned by

### `SegmentedNorm(mcolors.Normalize)`

Normalizer that scales data linearly with respect to the

### `DivergingNorm(mcolors.Normalize)`

Normalizer that ensures some central data value lies at the central

### `ColorDatabase(MutableMapping, dict)`

Dictionary subclass used to replace the builtin matplotlib color database.

### `ColormapDatabase(mcm.ColormapRegistry)`

Dictionary subclass used to replace the matplotlib
