#!/usr/bin/env python3
"""
Deprecated and removed rc keys.
"""

from __future__ import annotations

_RC_REMOVED = {  # {key: (alternative, version)} dictionary
    "rgbcycle": ("", "0.6.0"),  # no alternative, we no longer offer this feature
    "geogrid.latmax": ("Please use ax.format(latmax=N) instead.", "0.6.0"),
    "geogrid.latstep": ("Please use ax.format(latlines=N) instead.", "0.6.0"),
    "geogrid.lonstep": ("Please use ax.format(lonlines=N) instead.", "0.6.0"),
    "gridminor.latstep": ("Please use ax.format(latminorlines=N) instead.", "0.6.0"),
    "gridminor.lonstep": ("Please use ax.format(lonminorlines=N) instead.", "0.6.0"),
}

_RC_RENAMED = {  # {old_key: (new_key, version)} dictionary
    "abc.format": ("abc", "0.5.0"),
    "align": ("subplots.align", "0.6.0"),
    "axes.facealpha": ("axes.alpha", "0.6.0"),
    "geoaxes.edgecolor": ("axes.edgecolor", "0.6.0"),
    "geoaxes.facealpha": ("axes.alpha", "0.6.0"),
    "geoaxes.facecolor": ("axes.facecolor", "0.6.0"),
    "geoaxes.linewidth": ("axes.linewidth", "0.6.0"),
    "geogrid.alpha": ("grid.alpha", "0.6.0"),
    "geogrid.color": ("grid.color", "0.6.0"),
    "geogrid.labels": ("grid.labels", "0.6.0"),
    "geogrid.labelpad": ("grid.pad", "0.6.0"),
    "geogrid.labelsize": ("grid.labelsize", "0.6.0"),
    "geogrid.linestyle": ("grid.linestyle", "0.6.0"),
    "geogrid.linewidth": ("grid.linewidth", "0.6.0"),
    "share": ("subplots.share", "0.6.0"),
    "small": ("font.smallsize", "0.6.0"),
    "large": ("font.largesize", "0.6.0"),
    "span": ("subplots.span", "0.6.0"),
    "tight": ("subplots.tight", "0.6.0"),
    "axes.formatter.timerotation": ("formatter.timerotation", "0.6.0"),
    "axes.formatter.zerotrim": ("formatter.zerotrim", "0.6.0"),
    "abovetop": ("title.above", "0.7.0"),
    "subplots.pad": ("subplots.outerpad", "0.7.0"),
    "subplots.axpad": ("subplots.innerpad", "0.7.0"),
    "subplots.axwidth": ("subplots.refwidth", "0.7.0"),
    "text.labelsize": ("font.smallsize", "0.8.0"),
    "text.titlesize": ("font.largesize", "0.8.0"),
    "alpha": ("axes.alpha", "0.8.0"),
    "facecolor": ("axes.facecolor", "0.8.0"),
    "edgecolor": ("meta.color", "0.8.0"),
    "color": ("meta.color", "0.8.0"),
    "linewidth": ("meta.width", "0.8.0"),
    "lut": ("cmap.lut", "0.8.0"),
    "image.levels": ("cmap.levels", "0.8.0"),
    "image.inbounds": ("cmap.inbounds", "0.8.0"),
    "image.discrete": ("cmap.discrete", "0.8.0"),
    "image.edgefix": ("edgefix", "0.8.0"),
    "tick.ratio": ("tick.widthratio", "0.8.0"),
    "grid.ratio": ("grid.widthratio", "0.8.0"),
    "abc.style": ("abc", "0.8.0"),
    "grid.loninline": ("grid.inlinelabels", "0.8.0"),
    "grid.latinline": ("grid.inlinelabels", "0.8.0"),
    "cmap.edgefix": ("edgefix", "0.9.0"),
    "basemap": ("geo.backend", "0.10.0"),
    "inlinefmt": ("inlineformat", "0.10.0"),
    "cartopy.circular": ("geo.round", "0.10.0"),
    "cartopy.autoextent": ("geo.extent", "0.10.0"),
    "colorbar.rasterize": ("colorbar.rasterized", "0.10.0"),
}


def get_rc_removed():
    """
    Return removed rc settings.
    """
    return _RC_REMOVED.copy()


def get_rc_renamed():
    """
    Return renamed rc settings.
    """
    return _RC_RENAMED.copy()
