---
title: "ultraplot.utils"
description: "Various tools that may be useful while making plots."
source: "ultraplot/utils.py"
---

`ultraplot.utils`

Various tools that may be useful while making plots.

## Public Functions

### `arange(min_, *args)`

Identical to `numpy.arange` but with inclusive endpoints. For example,

### `edges(z, axis=-1)`

Calculate the approximate "edge" values along an axis given "center" values.

### `edges2d(z)`

Calculate the approximate "edge" values given a 2D grid of "center" values.

### `get_colors(*args, **kwargs)`

Get the colors associated with a registered or

### `shift_hue(color, shift=0, space='hcl')`

Shift the hue channel of a color.

### `scale_saturation(color, scale=1, space='hcl')`

Scale the saturation channel of a color.

### `scale_luminance(color, scale=1, space='hcl')`

Scale the luminance channel of a color.

### `set_hue(color, hue, space='hcl')`

Return a color with a different hue and the same luminance and saturation

### `set_saturation(color, saturation, space='hcl')`

Return a color with a different saturation and the same hue and luminance

### `set_luminance(color, luminance, space='hcl')`

Return a color with a different luminance and the same hue and saturation

### `set_alpha(color, alpha)`

Return a color with the opacity channel set to the specified value.

### `to_hex(color, space='rgb', cycle=None, keep_alpha=True)`

Translate the color from an arbitrary colorspace to a HEX string.

### `to_rgb(color, space='rgb', cycle=None)`

Translate the color from an arbitrary colorspace to an RGB tuple. This is

### `to_rgba(color, space='rgb', cycle=None, clip=True)`

Translate the color from an arbitrary colorspace to an RGBA tuple. This is

### `to_xyz(color, space='hcl')`

Translate color in *any* format to a tuple of channel values in *any*

### `to_xyza(color, space='hcl')`

Translate color in *any* format to a tuple of channel values in *any*

### `units(value, numeric=None, dest=None, *, fontsize=None, figure=None, axes=None, width=None)`

Convert values between arbitrary physical units. This is used internally all

### `check_for_update(package_name: str)`

No module docstring available.
