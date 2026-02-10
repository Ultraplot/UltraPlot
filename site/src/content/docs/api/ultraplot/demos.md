---
title: "ultraplot.demos"
description: "Functions for displaying colors and fonts."
source: "ultraplot/demos.py"
---

`ultraplot.demos`

Functions for displaying colors and fonts.

## Public Functions

### `show_channels(*args, N=100, rgb=False, saturation=True, minhue=0, maxsat=500, width=100, refwidth=1.7)`

Show how arbitrary colormap(s) vary with respect to the hue, chroma,

### `show_colorspaces(*, luminance=None, saturation=None, hue=None, refwidth=2)`

Generate hue-saturation, hue-luminance, and luminance-saturation

### `show_cmaps(*args, **kwargs)`

Generate a table of the registered colormaps or the input colormaps

### `show_cycles(*args, **kwargs)`

Generate a table of registered color cycles or the input color cycles

### `show_colors(*, nhues=17, minsat=10, unknown='User', include=None, ignore=None)`

Generate tables of the registered color names. Adapted from

### `show_fonts(*args, family=None, user=None, text=None, math=False, fallback=False, **kwargs)`

Generate a table of fonts. If a glyph for a particular font is unavailable,
