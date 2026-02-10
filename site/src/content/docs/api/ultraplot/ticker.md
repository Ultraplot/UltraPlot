---
title: "ultraplot.ticker"
description: "Various `~matplotlib.ticker.Locator` and `~matplotlib.ticker.Formatter` classes."
source: "ultraplot/ticker.py"
---

`ultraplot.ticker`

Various `~matplotlib.ticker.Locator` and `~matplotlib.ticker.Formatter` classes.

## Public Classes

### `IndexLocator(mticker.Locator)`

Format numbers by assigning fixed strings to non-negative indices. The ticks

### `DiscreteLocator(mticker.Locator)`

A tick locator suitable for discretized colorbars. Adds ticks to some

### `DegreeLocator(mticker.MaxNLocator)`

Locate geographic gridlines with degree-minute-second support.

### `LongitudeLocator(DegreeLocator)`

Locate longitude gridlines with degree-minute-second support.

### `LatitudeLocator(DegreeLocator)`

Locate latitude gridlines with degree-minute-second support.

### `AutoFormatter(mticker.ScalarFormatter)`

The default formatter used for ultraplot tick labels.

### `SimpleFormatter(mticker.Formatter)`

A general purpose number formatter. This is similar to `AutoFormatter`

### `IndexFormatter(mticker.Formatter)`

Format numbers by assigning fixed strings to non-negative indices. Generally

### `SciFormatter(mticker.Formatter)`

Format numbers with scientific notation.

### `SigFigFormatter(mticker.Formatter)`

Format numbers by retaining the specified number of significant digits.

### `FracFormatter(mticker.Formatter)`

Format numbers as integers or integer fractions. Optionally express the

### `CFDatetimeFormatter(mticker.Formatter)`

Format dates using `cftime.datetime.strftime` format strings.

### `AutoCFDatetimeFormatter(mticker.Formatter)`

Automatic formatter for `cftime.datetime` data.

### `AutoCFDatetimeLocator(mticker.Locator)`

Determines tick locations when plotting `cftime.datetime` data.

### `DegreeFormatter(_CartopyFormatter, _PlateCarreeFormatter)`

Formatter for longitude and latitude gridline labels.

### `LongitudeFormatter(_CartopyFormatter, LongitudeFormatter)`

Format longitude gridline labels. Adapted from

### `LatitudeFormatter(_CartopyFormatter, LatitudeFormatter)`

Format latitude gridline labels. Adapted from

### `CFTimeConverter(mdates.DateConverter)`

Converter for cftime.datetime data.
