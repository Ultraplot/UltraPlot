---
title: "ultraplot.config"
description: "Tools for setting up ultraplot and configuring global settings."
source: "ultraplot/config.py"
---

`ultraplot.config`

Tools for setting up ultraplot and configuring global settings.

## Public Classes

### `Configurator(MutableMapping, dict)`

A dictionary-like class for managing `matplotlib settings

## Public Functions

### `config_inline_backend(fmt=None)`

Set up the ipython `inline backend display format <https://ipython.readthedocs.io/en/stable/interactive/magics.html#magic-matplotlib>`__

### `use_style(style)`

Apply the `matplotlib style(s) <https://matplotlib.org/stable/tutorials/introductory/customizing.html>`__

### `register_cmaps(*args, user=None, local=None, default=False)`

Register named colormaps. This is called on import.

### `register_cycles(*args, user=None, local=None, default=False)`

Register named color cycles. This is called on import.

### `register_colors(*args, user=None, local=None, default=False, space=None, margin=None, **kwargs)`

Register named colors. This is called on import.

### `register_fonts(*args, user=True, local=True, default=False)`

Register font families. This is called on import.
