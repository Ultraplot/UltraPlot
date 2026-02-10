---
title: "ultraplot.scale"
description: "Various axis `~matplotlib.scale.ScaleBase` classes."
source: "ultraplot/scale.py"
---

`ultraplot.scale`

Various axis `~matplotlib.scale.ScaleBase` classes.

## Public Classes

### `LinearScale(_Scale, mscale.LinearScale)`

As with `~matplotlib.scale.LinearScale` but with

### `LogitScale(_Scale, mscale.LogitScale)`

As with `~matplotlib.scale.LogitScale` but with `~ultraplot.ticker.AutoFormatter`

### `LogScale(_Scale, mscale.LogScale)`

As with `~matplotlib.scale.LogScale` but with `~ultraplot.ticker.AutoFormatter`

### `SymmetricalLogScale(_Scale, mscale.SymmetricalLogScale)`

As with `~matplotlib.scale.SymmetricalLogScale` but with

### `FuncScale(_Scale, mscale.ScaleBase)`

Axis scale composed of arbitrary forward and inverse transformations.

### `FuncTransform(mtransforms.Transform)`

No module docstring available.

### `PowerScale(_Scale, mscale.ScaleBase)`

"Power scale" that performs the transformation

### `PowerTransform(mtransforms.Transform)`

No module docstring available.

### `InvertedPowerTransform(mtransforms.Transform)`

No module docstring available.

### `ExpScale(_Scale, mscale.ScaleBase)`

"Exponential scale" that performs either of two transformations. When

### `ExpTransform(mtransforms.Transform)`

No module docstring available.

### `InvertedExpTransform(mtransforms.Transform)`

No module docstring available.

### `MercatorLatitudeScale(_Scale, mscale.ScaleBase)`

Axis scale that is linear in the `Mercator projection latitude <http://en.wikipedia.org/wiki/Mercator_projection>`__. Adapted from `this example <https://matplotlib.org/2.0.2/examples/api/custom_scale_example.html>`__.

### `MercatorLatitudeTransform(mtransforms.Transform)`

No module docstring available.

### `InvertedMercatorLatitudeTransform(mtransforms.Transform)`

No module docstring available.

### `SineLatitudeScale(_Scale, mscale.ScaleBase)`

Axis scale that is linear in the sine transformation of *x*. The axis

### `SineLatitudeTransform(mtransforms.Transform)`

No module docstring available.

### `InvertedSineLatitudeTransform(mtransforms.Transform)`

No module docstring available.

### `CutoffScale(_Scale, mscale.ScaleBase)`

Axis scale composed of arbitrary piecewise linear transformations.

### `CutoffTransform(mtransforms.Transform)`

No module docstring available.

### `InverseScale(_Scale, mscale.ScaleBase)`

Axis scale that is linear in the *inverse* of *x*. The forward and inverse

### `InverseTransform(mtransforms.Transform)`

No module docstring available.
