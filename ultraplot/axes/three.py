#!/usr/bin/env python3
"""
The "3D" axes class.
"""

import numpy as np

from . import base, shared

try:
    from mpl_toolkits.mplot3d import Axes3D
except ImportError:
    Axes3D = object


class ThreeAxes(shared._SharedAxes, base.Axes, Axes3D):
    """
    Simple mix-in of `ultraplot.axes.Axes` with `~mpl_toolkits.mplot3d.axes3d.Axes3D`.

    Important
    ---------
    Note that this subclass does *not* implement the :class:`~ultraplot.axes.PlotAxes`
    plotting overrides. This axes subclass can be used by passing ``proj='3d'`` or
    ``proj='three'`` to axes-creation commands like `~ultraplot.figure.Figure.add_axes`,
    `~ultraplot.figure.Figure.add_subplot`, and `~ultraplot.figure.Figure.subplots`.
    """

    # TODO: Figure out a way to have internal Axes3D calls to plotting commands
    # access the overrides rather than the originals? May be impossible.
    _name = "three"
    _name_aliases = ("3d",)

    def __init__(self, *args, **kwargs):
        import mpl_toolkits.mplot3d  # noqa: F401 verify package is available

        kwargs.setdefault("alpha", 0.0)
        super().__init__(*args, **kwargs)

    def graph(self, *args, **kwargs):
        """
        Draw network graphs on 3D projections.
        """
        from .plot import PlotAxes

        return PlotAxes.graph(self, *args, **kwargs)

    def plot_surface(self, X, Y, Z, *args, **kwargs):
        """Plot a surface and retain a private coarse interaction proxy."""
        surface = super().plot_surface(X, Y, Z, *args, **kwargs)
        try:
            arrays = tuple(np.asanyarray(array) for array in (X, Y, Z))
            if any(array.ndim != 2 for array in arrays):
                return surface
            rows, cols = arrays[2].shape
            if rows * cols <= 625:
                return surface
            # A 10-by-10 mesh is deliberately modest: mplot3d depth-sorts every
            # face in Python, so even a visually coarse 25-by-25 mesh can exceed
            # an interactive 16.7 ms frame budget before rasterization begins.
            row_idx = np.unique(np.linspace(0, rows - 1, min(10, rows), dtype=int))
            col_idx = np.unique(np.linspace(0, cols - 1, min(10, cols), dtype=int))
            sampled = tuple(array[np.ix_(row_idx, col_idx)] for array in arrays)
            proxy_kwargs = dict(kwargs)
            for key in ("rcount", "ccount", "rstride", "cstride"):
                proxy_kwargs.pop(key, None)
            facecolors = proxy_kwargs.get("facecolors")
            if facecolors is not None:
                facecolors = np.asanyarray(facecolors)
                if facecolors.shape[:2] == (rows, cols):
                    proxy_kwargs["facecolors"] = facecolors[np.ix_(row_idx, col_idx)]
                else:
                    proxy_kwargs.pop("facecolors")
            limits = (self.get_xlim3d(), self.get_ylim3d(), self.get_zlim3d())
            autoscale = self.get_autoscale_on()
            proxy = super().plot_surface(*sampled, *args, **proxy_kwargs)
            proxy.set_visible(False)
            proxy.set_norm(surface.norm)
            proxy.set_clim(*surface.get_clim())
            proxy._ultraplot_lod_proxy = True
            surface._ultraplot_lod_proxy = proxy
            proxy.remove()
            self.set_xlim3d(*limits[0], auto=autoscale)
            self.set_ylim3d(*limits[1], auto=autoscale)
            self.set_zlim3d(*limits[2], auto=autoscale)
        except (AttributeError, IndexError, TypeError, ValueError):
            # Proxy creation is an optional interaction optimization. The exact
            # Matplotlib surface remains fully functional if it is unsupported.
            pass
        return surface
