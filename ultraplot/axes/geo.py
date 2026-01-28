#!/usr/bin/env python3
"""
Axes filled with cartographic projections.
"""
from __future__ import annotations

import copy
import inspect
from functools import partial

try:
    # From python 3.12
    from typing import override
except ImportError:
    # From Python 3.5
    from typing_extensions import override
from collections.abc import Iterator, MutableMapping, Sequence
from typing import Any, Optional, Protocol

import matplotlib.axis as maxis
import matplotlib.path as mpath
import matplotlib.text as mtext
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
import numpy as np

from .. import constructor
from .. import proj as pproj
from .. import ticker as pticker
from ..config import rc
from ..internals import (
    _not_none,
    _pop_rc,
    _version_cartopy,
    docstring,
    ic,  # noqa: F401
    labels,
    warnings,
)
from ..utils import units
from . import plot, shared

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import cartopy.mpl.gridliner as cgridliner
    from cartopy.crs import Projection
    from cartopy.mpl.geoaxes import GeoAxes as _GeoAxes
except ModuleNotFoundError:
    ccrs = cfeature = cgridliner = None
    _GeoAxes = Projection = object

try:
    from mpl_toolkits.basemap import Basemap
except ModuleNotFoundError:
    Basemap = object

__all__ = ["GeoAxes"]

# Basemap gridlines are dicts keyed by location containing (lines, labels).
GridlineDict = MutableMapping[float, tuple[list[Any], list[mtext.Text]]]
_GRIDLINER_PAD_SCALE = 2.0  # points; matches tick size visually
_MINOR_TICK_SCALE = 0.6  # relative to major tick length
_BASEMAP_LABEL_SIZE_SCALE = 0.5  # empirical scaling for label offset
_BASEMAP_LABEL_Y_SCALE = 0.65  # empirical spacing to mimic cartopy
_BASEMAP_LABEL_X_SCALE = 0.25  # empirical spacing to mimic cartopy
_CARTOPY_LABEL_SIDES = ("labelleft", "labelright", "labelbottom", "labeltop", "geo")
_BASEMAP_LABEL_SIDES = ("labelleft", "labelright", "labeltop", "labelbottom", "geo")


# Format docstring
_format_docstring = """
round : bool, default: :rc:`geo.round`
    *For polar cartopy axes only*.
    Whether to bound polar projections with circles rather than squares. Note that outer
    gridline labels cannot be added to circle-bounded polar projections. When basemap
    is the backend this argument must be passed to `~ultraplot.constructor.Proj` instead.
extent : {'globe', 'auto'}, default: :rc:`geo.extent`
    *For cartopy axes only*.
    Whether to auto adjust the map bounds based on plotted content. If ``'globe'`` then
    non-polar projections are fixed with `~cartopy.mpl.geoaxes.GeoAxes.set_global`,
    non-Gnomonic polar projections are bounded at the equator, and Gnomonic polar
    projections are bounded at 30 degrees latitude. If ``'auto'`` nothing is done.
lonlim, latlim : 2-tuple of float, optional
    *For cartopy axes only.*
    The approximate longitude and latitude boundaries of the map, applied
    with `~cartopy.mpl.geoaxes.GeoAxes.set_extent`. When basemap is the backend
    this argument must be passed to `~ultraplot.constructor.Proj` instead.
boundinglat : float, optional
    *For cartopy axes only.*
    The edge latitude for the circle bounding North Pole and South Pole-centered
    projections. When basemap is the backend this argument must be passed to
    `~ultraplot.constructor.Proj` instead.
longrid, latgrid, grid : bool, default: :rc:`grid`
    Whether to draw longitude and latitude gridlines.
    Use the keyword `grid` to toggle both at once.
longridminor, latgridminor, gridminor : bool, default: :rc:`gridminor`
    Whether to draw "minor" longitude and latitude lines.
    Use the keyword `gridminor` to toggle both at once.
lonticklen, latticklen, ticklen : unit-spec, default: :rc:`tick.len`
    Major tick lengths for the longitudinal (x) and latitude (y) axis.
    %(units.pt)s
    Use the keyword `ticklen` to set both at once.
latmax : float, default: 80
    The maximum absolute latitude for gridlines. Longitude gridlines are cut off
    poleward of this value (note this feature does not work in cartopy 0.18).
nsteps : int, default: :rc:`grid.nsteps`
    *For cartopy axes only.*
    The number of interpolation steps used to draw gridlines.
lonlines, latlines : optional
    Aliases for `lonlocator`, `latlocator`.
lonlocator, latlocator : locator-spec, optional
    Used to determine the longitude and latitude gridline locations.
    Passed to the `~ultraplot.constructor.Locator` constructor. Can be
    string, float, list of float, or `matplotlib.ticker.Locator` instance.

    For basemap or cartopy < 0.18, the defaults are ``'deglon'`` and
    ``'deglat'``, which correspond to the `~ultraplot.ticker.LongitudeLocator`
    and `~ultraplot.ticker.LatitudeLocator` locators (adapted from cartopy).
    For cartopy >= 0.18, the defaults are ``'dmslon'`` and ``'dmslat'``,
    which uses the same locators with ``dms=True``. This selects gridlines
    at nice degree-minute-second intervals when the map extent is very small.
lonlines_kw, latlines_kw : optional
    Aliases for `lonlocator_kw`, `latlocator_kw`.
lonlocator_kw, latlocator_kw : dict-like, optional
    Keyword arguments passed to the `matplotlib.ticker.Locator` class.
lonminorlocator, latminorlocator, lonminorlines, latminorlines : optional
    As with `lonlocator` and `latlocator` but for the "minor" gridlines.
lonminorlines_kw, latminorlines_kw : optional
    Aliases for `lonminorlocator_kw`, `latminorlocator_kw`.
lonminorlocator_kw, latminorlocator_kw : optional
    As with `lonlocator_kw`, and `latlocator_kw` but for the "minor" gridlines.
lonlabels, latlabels, labels : str, bool, or sequence, :rc:`grid.labels`
    Whether to add non-inline longitude and latitude gridline labels, and on
    which sides of the map. Use the keyword `labels` to set both at once. The
    argument must conform to one of the following options:

    * A boolean. ``True`` indicates the bottom side for longitudes and
      the left side for latitudes, and ``False`` disables all labels.
    * A string or sequence of strings indicating the side names, e.g.
      ``'top'`` for longitudes or ``('left', 'right')`` for latitudes.
    * A string indicating the side names with single characters, e.g.
      ``'bt'`` for longitudes or ``'lr'`` for latitudes.
    * A string matching ``'neither'`` (no labels), ``'both'`` (equivalent
      to ``'bt'`` for longitudes and ``'lr'`` for latitudes), or ``'all'``
      (equivalent to ``'lrbt'``, i.e. all sides).
    * A boolean 2-tuple indicating whether to draw labels
      on the ``(bottom, top)`` sides for longitudes,
      and the ``(left, right)`` sides for latitudes.
    * A boolean 4-tuple indicating whether to draw labels on the
      ``(left, right, bottom, top)`` sides, as with the basemap
      :func:`~mpl_toolkits.basemap.Basemap.drawmeridians` and
      :func:`~mpl_toolkits.basemap.Basemap.drawparallels` `labels` keyword.

loninline, latinline, inlinelabels : bool, default: :rc:`grid.inlinelabels`
    *For cartopy axes only.*
    Whether to add inline longitude and latitude gridline labels. Use
    the keyword `inlinelabels` to set both at once.
rotatelabels : bool, default: :rc:`grid.rotatelabels`
    *For cartopy axes only.*
    Whether to rotate non-inline gridline labels so that they automatically
    follow the map boundary curvature.
labelrotation : float, optional
    The rotation angle in degrees for both longitude and latitude tick labels.
    Use `lonlabelrotation` and `latlabelrotation` to set them separately.
lonlabelrotation : float, optional
    The rotation angle in degrees for longitude tick labels.
    Works for both cartopy and basemap backends.
latlabelrotation : float, optional
    The rotation angle in degrees for latitude tick labels.
    Works for both cartopy and basemap backends.
labelpad : unit-spec, default: :rc:`grid.labelpad`
    *For cartopy axes only.*
    The padding between non-inline gridline labels and the map boundary.
    %(units.pt)s
dms : bool, default: :rc:`grid.dmslabels`
    *For cartopy axes only.*
    Whether the default locators and formatters should use "minutes" and "seconds"
    for gridline labels on small scales rather than decimal degrees. Setting this to
    ``False`` is equivalent to ``ax.format(lonlocator='deglon', latlocator='deglat')``
    and ``ax.format(lonformatter='deglon', latformatter='deglat')``.
lonformatter, latformatter : formatter-spec, optional
    Formatter used to style longitude and latitude gridline labels.
    Passed to the `~ultraplot.constructor.Formatter` constructor. Can be
    string, list of string, or `matplotlib.ticker.Formatter` instance.

    For basemap or cartopy < 0.18, the defaults are ``'deglon'`` and
    ``'deglat'``, which correspond to `~ultraplot.ticker.SimpleFormatter`
    presets with degree symbols and cardinal direction suffixes.
    For cartopy >= 0.18, the defaults are ``'dmslon'`` and ``'dmslat'``,
    which uses cartopy's `~cartopy.mpl.ticker.LongitudeFormatter` and
    `~cartopy.mpl.ticker.LatitudeFormatter` formatters with ``dms=True``.
    This formats gridlines that do not fall on whole degrees as "minutes" and
    "seconds" rather than decimal degrees. Use ``dms=False`` to disable this.
lonformatter_kw, latformatter_kw : dict-like, optional
    Keyword arguments passed to the `matplotlib.ticker.Formatter` class.
land, ocean, coast, rivers, lakes, borders, innerborders : bool, optional
    Toggles various geographic features. These are actually the
    :rcraw:`land`, :rcraw:`ocean`, :rcraw:`coast`, :rcraw:`rivers`,
    :rcraw:`lakes`, :rcraw:`borders`, and :rcraw:`innerborders`
    settings passed to `~ultraplot.config.Configurator.context`.
    The style can be modified using additional `rc` settings.

    For example, to change :rcraw:`land.color`, use
    ``ax.format(landcolor='green')``, and to change
    :rcraw:`land.zorder`, use ``ax.format(landzorder=4)``.
reso : {'lo', 'med', 'hi', 'x-hi', 'xx-hi'}, optional
    *For cartopy axes only.*
    The resolution of geographic features. When basemap is the backend this
    must be passed to `~ultraplot.constructor.Proj` instead.
color : color-spec, default: :rc:`meta.color`
    The color for the axes edge. Propagates to `labelcolor` unless specified
    otherwise (similar to :func:`~ultraplot.axes.CartesianAxes.format`).
gridcolor : color-spec, default: :rc:`grid.color`
    The color for the gridline labels.
labelcolor : color-spec, default: `color` or :rc:`grid.labelcolor`
    The color for the gridline labels (`gridlabelcolor` is also allowed).
labelsize : unit-spec or str, default: :rc:`grid.labelsize`
    The font size for the gridline labels (`gridlabelsize` is also allowed).
    %(units.pt)s
labelweight : str, default: :rc:`grid.labelweight`
    The font weight for the gridline labels (`gridlabelweight` is also allowed).
"""
docstring._snippet_manager["geo.format"] = _format_docstring


class _GeoLabel(object):
    """
    Optionally omit overlapping check if an rc setting is disabled.
    """

    def check_overlapping(self, *args: Any, **kwargs: Any) -> bool:
        if rc["grid.checkoverlap"]:
            return super().check_overlapping(*args, **kwargs)
        else:
            return False


if cgridliner is not None and hasattr(cgridliner, "Label"):  # only recent versions

    class _CartopyLabel(_GeoLabel, cgridliner.Label):
        """Label class with configurable overlap checks."""

    class _CartopyGridliner(cgridliner.Gridliner):
        """
        Gridliner subclass to localize cartopy quirks in one place.
        """

        LabelClass = _CartopyLabel

        def _generate_labels(self) -> Iterator[_CartopyLabel]:
            """Yield label objects, reusing cached instances when possible."""
            for label in self._all_labels:
                yield label

            while True:
                new_artist = mtext.Text()
                new_artist.set_figure(self.axes.figure)
                new_artist.axes = self.axes

                new_label = self.LabelClass(new_artist, None, None, None)
                self._all_labels.append(new_label)

                yield new_label

        def _axes_domain(self, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
            x_range, y_range = super()._axes_domain(*args, **kwargs)
            if _version_cartopy < "0.18":
                lon_0 = self.axes.projection.proj4_params.get("lon_0", 0)
                x_range = np.asarray(x_range) + lon_0
            return x_range, y_range

        def _draw_gridliner(self, *args: Any, **kwargs: Any) -> Any:  # noqa: E306
            result = super()._draw_gridliner(*args, **kwargs)
            if _version_cartopy >= "0.18":
                lon_lim, _ = self._axes_domain()
                if abs(np.diff(lon_lim)) == abs(np.diff(self.crs.x_limits)):
                    for collection in self.xline_artists:
                        if not getattr(collection, "_cartopy_fix", False):
                            collection.get_paths().pop(-1)
                            collection._cartopy_fix = True
            return result

else:
    _CartopyGridliner = None


class _GeoAxis(object):
    """
    Dummy axis used by longitude and latitude locators and for storing view limits on
    longitude and latitude coordinates. Modeled after how `matplotlib.ticker._DummyAxis`
    and `matplotlib.ticker.TickHelper` are used to control tick locations and labels.
    """

    # NOTE: Due to cartopy bug (https://github.com/SciTools/cartopy/issues/1564)
    # we store presistent longitude and latitude locators on axes, then *call*
    # them whenever set_extent is called and apply *fixed* locators.
    def __init__(self, axes: "GeoAxes") -> None:
        self.axes = axes
        self.major = maxis.Ticker()
        self.minor = maxis.Ticker()
        self.isDefault_majfmt = True
        self.isDefault_majloc = True
        self.isDefault_minloc = True
        self._interval = None
        self._use_dms = (
            ccrs is not None
            and isinstance(
                axes.projection, (ccrs._RectangularProjection, ccrs.Mercator)
            )  # noqa: E501
            and _version_cartopy >= "0.18"
        )

    def _get_extent(self) -> tuple[float, float, float, float]:
        # Try to get extent but bail out for projections where this is
        # impossible. So far just transverse Mercator
        try:
            return self.axes.get_extent()
        except Exception:
            lon0 = self.axes._get_lon0()
            return (-180 + lon0, 180 + lon0, -90, 90)

    @staticmethod
    def _pad_ticks(ticks: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
        # Wrap up to the longitude/latitude range to avoid
        # giant lists of 10,000 gridline locations.
        if len(ticks) == 0:
            return ticks
        range_ = np.max(ticks) - np.min(ticks)
        vmin = max(vmin, ticks[0] - range_)
        vmax = min(vmax, ticks[-1] + range_)

        # Pad the reported tick range up to specified range
        step = ticks[1] - ticks[0]  # MaxNLocator/AutoMinorLocator steps are equal
        ticks_lo = np.arange(ticks[0], vmin, -step)[1:][::-1]
        ticks_hi = np.arange(ticks[-1], vmax, step)[1:]
        ticks = np.concatenate((ticks_lo, ticks, ticks_hi))
        return ticks

    def get_scale(self) -> str:
        return "linear"

    def get_tick_space(self) -> int:
        return 9  # longstanding default of nbins=9

    def get_major_formatter(self) -> mticker.Formatter | None:
        return self.major.formatter

    def get_major_locator(self) -> mticker.Locator | None:
        return self.major.locator

    def get_minor_locator(self) -> mticker.Locator | None:
        return self.minor.locator

    def get_majorticklocs(self) -> np.ndarray:
        return self._get_ticklocs(self.major.locator)

    def get_minorticklocs(self) -> np.ndarray:
        return self._get_ticklocs(self.minor.locator)

    def set_major_formatter(
        self, formatter: mticker.Formatter, default: bool = False
    ) -> None:
        # NOTE: Cartopy formatters check Formatter.axis.axes.projection
        # in order to implement special projection-dependent behavior.
        self.major.formatter = formatter
        formatter.set_axis(self)
        self.isDefault_majfmt = default

    def set_major_locator(
        self, locator: mticker.Locator, default: bool = False
    ) -> None:
        self.major.locator = locator
        if self.major.formatter:
            self.major.formatter._set_locator(locator)
        locator.set_axis(self)
        self.isDefault_majloc = default

    def set_minor_locator(
        self, locator: mticker.Locator, default: bool = False
    ) -> None:
        self.minor.locator = locator
        locator.set_axis(self)
        self.isDefault_majfmt = default

    def set_view_interval(self, vmin: float, vmax: float) -> None:
        self._interval = (vmin, vmax)

    def _copy_locator_properties(self, other: "_GeoAxis") -> None:
        """
        This function copies the locator properties. It is
        used when the @self is sharing with @other.
        """
        props = [
            "isDefault_majloc",
            "isDefault_minloc",
            "isDefault_majfmt",
        ]
        funcs = [
            "major_locator",
            "minor_locator",
            "major_formatter",
        ]
        for prop, func in zip(props, funcs):
            # Copy if props differ from this to other
            this_prop = getattr(self, prop)
            other_prop = getattr(other, prop)
            if this_prop ^ other_prop:
                # Allow this to error if in the unlikely
                # case that the backend changes
                getter = getattr(self, f"get_{func}")
                setter = getattr(other, f"set_{func}")
                setter(getter())
                setattr(other, prop, this_prop)


class _GridlinerAdapter(Protocol):
    """
    Lightweight facade used to normalize cartopy and basemap gridliner behavior.
    These adapters let GeoAxes apply gridline label toggles and styles without
    backend-specific branching.
    """

    def labels_for_sides(
        self,
        *,
        bottom: bool | str | None = None,
        top: bool | str | None = None,
        left: bool | str | None = None,
        right: bool | str | None = None,
    ) -> dict[str, list[mtext.Text]]: ...

    def toggle_labels(
        self,
        *,
        labelleft: bool | str | None = None,
        labelright: bool | str | None = None,
        labelbottom: bool | str | None = None,
        labeltop: bool | str | None = None,
        geo: bool | str | None = None,
    ) -> None: ...

    def apply_style(
        self,
        *,
        axis: str = "both",
        pad: float | None = None,
        labelsize: float | str | None = None,
        labelcolor: Any = None,
        labelrotation: float | None = None,
        linecolor: Any = None,
        linewidth: float | None = None,
    ) -> None: ...

    def tick_positions(
        self, axis: str, *, lonaxis: "_GeoAxis", lataxis: "_GeoAxis"
    ) -> np.ndarray: ...

    def is_label_on(self, side: str) -> bool: ...


class _CartopyGridlinerProtocol(Protocol):
    """
    Structural protocol for the subset of cartopy Gridliner attributes we use.
    This keeps type hints tight without importing cartopy at runtime.
    """

    collection_kwargs: dict[str, Any]
    xlabel_style: dict[str, Any]
    ylabel_style: dict[str, Any]
    xlocator: mticker.Locator
    ylocator: mticker.Locator
    xpadding: float | None
    ypadding: float | None
    xlines: bool
    ylines: bool
    x_inline: bool | None
    y_inline: bool | None
    rotate_labels: bool | None
    inline_labels: bool | str | None
    geo_labels: bool | str | None
    left_label_artists: list[mtext.Text]
    right_label_artists: list[mtext.Text]
    bottom_label_artists: list[mtext.Text]
    top_label_artists: list[mtext.Text]
    xline_artists: list[Any]

    def _axes_domain(self, *args: Any, **kwargs: Any) -> tuple[Any, Any]: ...
    def _draw_gridliner(self, *args: Any, **kwargs: Any) -> Any: ...


class _CartopyGridlinerAdapter(_GridlinerAdapter):
    """
    Adapter for cartopy's Gridliner, translating common label/style operations
    into the Gridliner API while hiding cartopy version differences.
    """

    def __init__(self, gridliner: Optional[_CartopyGridlinerProtocol]) -> None:
        self.gridliner = gridliner

    @staticmethod
    def _side_labels() -> tuple[str, str, str, str]:
        # Cartopy label attribute names vary by version.
        if _version_cartopy >= "0.18":
            left_labels = "left_labels"
            right_labels = "right_labels"
            bottom_labels = "bottom_labels"
            top_labels = "top_labels"
        else:  # cartopy < 0.18
            left_labels = "ylabels_left"
            right_labels = "ylabels_right"
            bottom_labels = "xlabels_bottom"
            top_labels = "xlabels_top"
        return (left_labels, right_labels, bottom_labels, top_labels)

    def labels_for_sides(
        self,
        *,
        bottom: bool | str | None = None,
        top: bool | str | None = None,
        left: bool | str | None = None,
        right: bool | str | None = None,
    ) -> dict[str, list[mtext.Text]]:
        sides = {}
        gl = self.gridliner
        if gl is None:
            return sides
        for dir, side in zip(
            "bottom top left right".split(), [bottom, top, left, right]
        ):
            if side != True:
                continue
            sides[dir] = getattr(gl, f"{dir}_label_artists")
        return sides

    def toggle_labels(
        self,
        *,
        labelleft: bool | str | None = None,
        labelright: bool | str | None = None,
        labelbottom: bool | str | None = None,
        labeltop: bool | str | None = None,
        geo: bool | str | None = None,
    ) -> None:
        gl = self.gridliner
        if gl is None:
            return
        side_labels = self._side_labels()
        togglers = (labelleft, labelright, labelbottom, labeltop)
        for toggle, side in zip(togglers, side_labels):
            if toggle is not None:
                setattr(gl, side, toggle)
        if geo is not None:  # only cartopy 0.20 supported but harmless
            setattr(gl, "geo_labels", geo)

    def apply_style(
        self,
        *,
        axis: str = "both",
        pad: float | None = None,
        labelsize: float | str | None = None,
        labelcolor: Any = None,
        labelrotation: float | None = None,
        linecolor: Any = None,
        linewidth: float | None = None,
    ) -> None:
        gl = self.gridliner
        if gl is None:
            return

        def _apply_label_style(style: dict[str, Any]) -> None:
            if labelcolor is not None:
                style["color"] = labelcolor
            if labelsize is not None:
                style["fontsize"] = labelsize
            if labelrotation is not None:
                style["rotation"] = labelrotation

        # Cartopy line styling is stored in the collection kwargs.
        if linecolor is not None:
            gl.collection_kwargs["color"] = linecolor
        if linewidth is not None:
            gl.collection_kwargs["linewidth"] = linewidth
        if axis in ("x", "both"):
            _apply_label_style(gl.xlabel_style)
            if pad is not None and hasattr(gl, "xpadding"):
                gl.xpadding = pad
        if axis in ("y", "both"):
            _apply_label_style(gl.ylabel_style)
            if pad is not None and hasattr(gl, "ypadding"):
                gl.ypadding = pad

    def tick_positions(
        self, axis: str, *, lonaxis: _GeoAxis, lataxis: _GeoAxis
    ) -> np.ndarray:
        gl = self.gridliner
        if gl is None:
            return np.asarray([])
        if axis == "x":
            locator = gl.xlocator
            if locator is None:
                return np.asarray([])
            return lonaxis._get_ticklocs(locator)
        if axis == "y":
            locator = gl.ylocator
            if locator is None:
                return np.asarray([])
            return lataxis._get_ticklocs(locator)
        raise ValueError(f"Invalid axis: {axis!r}")

    def is_label_on(self, side: str) -> bool:
        gl = self.gridliner
        if gl is None:
            return False
        left_labels, right_labels, bottom_labels, top_labels = self._side_labels()
        if side == "labelleft":
            return getattr(gl, left_labels)
        elif side == "labelright":
            return getattr(gl, right_labels)
        elif side == "labelbottom":
            return getattr(gl, bottom_labels)
        elif side == "labeltop":
            return getattr(gl, top_labels)
        else:
            raise ValueError(f"Invalid side: {side}")


class _BasemapGridlinerAdapter(_GridlinerAdapter):
    """
    Adapter for basemap meridian/parallel dictionaries, emulating the subset
    of cartopy Gridliner behavior needed by GeoAxes (labels, toggles, styling).
    """

    def __init__(
        self,
        lonlines: GridlineDict | None,
        latlines: GridlineDict | None,
    ) -> None:
        self.lonlines = lonlines
        self.latlines = latlines

    def labels_for_sides(
        self,
        *,
        bottom: bool | str | None = None,
        top: bool | str | None = None,
        left: bool | str | None = None,
        right: bool | str | None = None,
    ) -> dict[str, list[mtext.Text]]:
        directions = "left right top bottom".split()
        bools = [left, right, top, bottom]
        sides = {}
        for direction, is_on in zip(directions, bools):
            if is_on is None:
                continue
            gl = self.lonlines
            if direction in ["left", "right"]:
                gl = self.latlines
            for loc, (lines, labels) in (gl or {}).items():
                for label in labels:
                    # Determine side by label position (Basemap clusters by location).
                    position = label.get_position()
                    match direction:
                        case "top" if position[1] > 0:
                            add = True
                        case "bottom" if position[1] < 0:
                            add = True
                        case "left" if position[0] < 0:
                            add = True
                        case "right" if position[0] > 0:
                            add = True
                        case _:
                            add = False
                    if add:
                        sides.setdefault(direction, []).append(label)
        return sides

    def toggle_labels(
        self,
        *,
        labelleft: bool | str | None = None,
        labelright: bool | str | None = None,
        labelbottom: bool | str | None = None,
        labeltop: bool | str | None = None,
        geo: bool | str | None = None,
    ) -> None:
        labels = self.labels_for_sides(
            bottom=labelbottom, top=labeltop, left=labelleft, right=labelright
        )
        toggles = {
            "bottom": labelbottom,
            "top": labeltop,
            "left": labelleft,
            "right": labelright,
        }
        for direction, toggle in toggles.items():
            if toggle is None:
                continue
            for label in labels.get(direction, []):
                label.set_visible(bool(toggle) or toggle in ("x", "y"))

    def apply_style(
        self,
        *,
        axis: str = "both",
        pad: float | None = None,
        labelsize: float | str | None = None,
        labelcolor: Any = None,
        labelrotation: float | None = None,
        linecolor: Any = None,
        linewidth: float | None = None,
    ) -> None:
        pad  # unused for basemap gridlines
        targets = []
        if axis in ("x", "both"):
            targets.append(self.lonlines)
        if axis in ("y", "both"):
            targets.append(self.latlines)
        for gl in targets:
            for loc, (lines, labels) in (gl or {}).items():
                # Basemap stores line artists and label text separately.
                for line in lines:
                    if linecolor is not None and hasattr(line, "set_color"):
                        line.set_color(linecolor)
                    if linewidth is not None and hasattr(line, "set_linewidth"):
                        line.set_linewidth(linewidth)
                for label in labels:
                    if labelcolor is not None:
                        label.set_color(labelcolor)
                    if labelsize is not None:
                        label.set_fontsize(labelsize)
                    if labelrotation is not None:
                        label.set_rotation(labelrotation)

    def tick_positions(
        self, axis: str, *, lonaxis: _GeoAxis, lataxis: _GeoAxis
    ) -> np.ndarray:
        lonaxis, lataxis  # unused; tick positions are stored in dict keys
        if axis == "x":
            locator = self.lonlines
        elif axis == "y":
            locator = self.latlines
        else:
            raise ValueError(f"Invalid axis: {axis!r}")
        if not locator:
            return np.asarray([])
        return np.asarray(list(locator.keys()))

    def is_label_on(self, side: str) -> bool:
        def group_labels(
            labels: list[mtext.Text],
            which: str,
            labelbottom: bool | str | None = None,
            labeltop: bool | str | None = None,
            labelleft: bool | str | None = None,
            labelright: bool | str | None = None,
        ) -> dict[str, list[mtext.Text]]:
            group = {}
            for label in labels:
                position = label.get_position()
                target = None
                if which == "x":
                    if labelbottom is not None and position[1] < 0:
                        target = "labelbottom"
                    elif labeltop is not None and position[1] >= 0:
                        target = "labeltop"
                else:
                    if labelleft is not None and position[0] < 0:
                        target = "labelleft"
                    elif labelright is not None and position[0] >= 0:
                        target = "labelright"
                if target is not None:
                    group[target] = group.get(target, []) + [label]
            return group

        gl = self.lonlines
        which = "x"
        if side in ["labelleft", "labelright"]:
            gl = self.latlines
            which = "y"
        for loc, (line, labels) in (gl or {}).items():
            grouped = group_labels(
                labels=labels,
                which=which,
                **{side: True},
            )
            for label in grouped.get(side, []):
                if label.get_visible():
                    return True
        return False


class _LonAxis(_GeoAxis):
    """
    Axis with default longitude locator.
    """

    axis_name = "lon"

    # NOTE: Basemap accepts tick formatters with drawmeridians(fmt=Formatter())
    # Try to use cartopy formatter if cartopy installed. Otherwise use
    # default builtin basemap formatting.
    def __init__(self, axes: "GeoAxes") -> None:
        super().__init__(axes)
        if self._use_dms:
            locator = formatter = "dmslon"
        else:
            locator = formatter = "deglon"
        self.set_major_formatter(
            constructor.Formatter(formatter),
            default=True,
        )
        self.set_major_locator(constructor.Locator(locator), default=True)
        self.set_minor_locator(mticker.AutoMinorLocator(), default=True)

    def _get_ticklocs(self, locator: mticker.Locator) -> np.ndarray:
        # Prevent ticks from looping around
        # NOTE: Cartopy 0.17 formats numbers offset by eps with the cardinal indicator
        # (e.g. 0 degrees for map centered on 180 degrees). So skip in that case.
        # NOTE: Common strange issue is e.g. MultipleLocator(60) starts out at
        # -60 degrees for a map from 0 to 360 degrees. If always trimmed circular
        # locations from right then would cut off rightmost gridline. Workaround is
        # to trim on the side closest to central longitude (in this case the left).
        eps = 1e-10
        # We set lon0 in the Formatter here
        # as initially the formatter is parsed
        # as a SimpleFormatter. Here, the formatter
        # should be a LongitudinalFormatter.
        lon0 = self.axes._get_lon0()
        formatter = self.get_major_formatter()
        formatter.lon0 = lon0  # update if necessary
        ticks = np.sort(locator())
        while ticks.size:
            if np.isclose(ticks[0] + 360, ticks[-1]):
                if _version_cartopy >= "0.18" or not np.isclose(ticks[0] % 360, 0):
                    ticks[-1] -= eps  # ensure label appears on *right* not left
                break
            elif ticks[0] + 360 < ticks[-1]:
                idx = (1, None) if lon0 - ticks[0] > ticks[-1] - lon0 else (None, -1)
                ticks = ticks[slice(*idx)]  # cut off ticks looped over globe
            else:
                break

        # Append extra ticks in case longitude/latitude limits do not encompass
        # the entire view range of map, e.g. for Lambert Conformal sectors.
        # NOTE: Try to avoid making 10,000 element lists. Just wrap extra ticks
        # up to the width of *reported* longitude range.
        if isinstance(locator, (mticker.MaxNLocator, mticker.AutoMinorLocator)):
            ticks = self._pad_ticks(ticks, lon0 - 180 + eps, lon0 + 180 - eps)

        return ticks

    def get_view_interval(self) -> tuple[float, float]:
        # NOTE: ultraplot tries to set its *own* view intervals to avoid dateline
        # weirdness, but if rc['geo.extent'] is 'auto' the interval will be unset.
        # In this case we use _get_extent() as a backup.
        interval = self._interval
        if interval is None:
            extent = self._get_extent()
            interval = extent[:2]  # longitude extents
        return interval


class _LatAxis(_GeoAxis):
    """
    Axis with default latitude locator.
    """

    axis_name = "lat"

    def __init__(self, axes: "GeoAxes", latmax: float = 90) -> None:
        # NOTE: Need to pass projection because lataxis/lonaxis are
        # initialized before geoaxes is initialized, because format() needs
        # the axes and format() is called by ultraplot.axes.Axes.__init__()
        self._latmax = latmax
        super().__init__(axes)
        if self._use_dms:
            locator = formatter = "dmslat"
        else:
            locator = formatter = "deglat"
        self.set_major_formatter(constructor.Formatter(formatter), default=True)
        self.set_major_locator(constructor.Locator(locator), default=True)
        self.set_minor_locator(mticker.AutoMinorLocator(), default=True)

    def _get_ticklocs(self, locator: mticker.Locator) -> np.ndarray:
        # Adjust latitude ticks to fix bug in some projections. Harmless for basemap.
        # NOTE: Maybe this was fixed by cartopy 0.18?
        eps = 1e-10
        ticks = np.sort(locator())
        if ticks.size:
            if ticks[0] == -90:
                ticks[0] += eps
            if ticks[-1] == 90:
                ticks[-1] -= eps

        # Append extra ticks in case longitude/latitude limits do not encompass
        # the entire view range of map, e.g. for Lambert Conformal sectors.
        if isinstance(locator, (mticker.MaxNLocator, mticker.AutoMinorLocator)):
            ticks = self._pad_ticks(ticks, -90 + eps, 90 - eps)

        # Filter ticks to latmax range
        latmax = self.get_latmax()
        ticks = ticks[(ticks >= -latmax) & (ticks <= latmax)]

        return ticks

    def get_latmax(self) -> float:
        return self._latmax

    def get_view_interval(self) -> tuple[float, float]:
        interval = self._interval
        if interval is None:
            extent = self._get_extent()
            interval = extent[2:]  # latitudes
        return interval

    def set_latmax(self, latmax: float) -> None:
        self._latmax = latmax


def _gridliner_sides_from_arrays(
    lonarray: Sequence[bool | None] | None,
    latarray: Sequence[bool | None] | None,
    *,
    order: Sequence[str],
    allow_xy: bool,
    include_false: bool,
) -> dict[str, bool | str]:
    """
    Map lon/lat label arrays to gridliner toggle flags.

    Parameters
    ----------
    allow_xy
        Use "x"/"y" to preserve axis-specific toggles when only one of lon/lat
        is enabled for a given side (cartopy behavior).
    include_false
        Include explicit False entries to actively hide existing labels instead
        of leaving previous state untouched (backend-dependent behavior).
    """
    if lonarray is None or latarray is None:
        return {}
    sides: dict[str, bool | str] = {}
    for side, lon, lat in zip(order, lonarray, latarray):
        value: bool | str | None = None
        if allow_xy:
            if lon and lat:
                value = True
            elif lon:
                value = "x"
            elif lat:
                value = "y"
            elif include_false and (lon is not None or lat is not None):
                value = False
        else:
            if lon or lat:
                value = True
            elif include_false and (lon is not None or lat is not None):
                value = False
        if value is not None:
            sides[side] = value
    return sides


class GeoAxes(shared._SharedAxes, plot.PlotAxes):
    """
    Axes subclass for plotting in geographic projections. Uses either cartopy
    or basemap as a "backend".

    Note
    ----
    This subclass uses longitude and latitude as the default coordinate system for all
    plotting commands by internally passing ``transform=cartopy.crs.PlateCarree()`` to
    cartopy commands and ``latlon=True`` to basemap commands. Also, when using basemap
    as the "backend", plotting is still done "cartopy-style" by calling methods from
    the axes instance rather than the `~mpl_toolkits.basemap.Basemap` instance.

    Important
    ---------
    This axes subclass can be used by passing ``proj='proj_name'``
    to axes-creation commands like `~ultraplot.figure.Figure.add_axes`,
    `~ultraplot.figure.Figure.add_subplot`, and `~ultraplot.figure.Figure.subplots`,
    where ``proj_name`` is a registered :ref:`PROJ projection name <proj_table>`.
    You can also pass a `~cartopy.crs.Projection` or `~mpl_toolkits.basemap.Basemap`
    instance instead of a projection name. Alternatively, you can pass any of the
    matplotlib-recognized axes subclass names ``proj='cartopy'``, ``proj='geo'``, or
    ``proj='geographic'`` with a `~cartopy.crs.Projection` `map_projection` keyword
    argument, or pass ``proj='basemap'`` with a `~mpl_toolkits.basemap.Basemap`
    `map_projection` keyword argument.
    """

    @docstring._snippet_manager
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        *args
            Passed to `matplotlib.axes.Axes`.
        map_projection : `~cartopy.crs.Projection` or `~mpl_toolkits.basemap.Basemap`
            The cartopy or basemap projection instance. This is
            passed automatically when calling axes-creation
            commands like `~ultraplot.figure.Figure.add_subplot`.
        %(geo.format)s

        Other parameters
        ----------------
        %(axes.format)s
        %(rc.init)s

        See also
        --------
        GeoAxes.format
        ultraplot.constructor.Proj
        ultraplot.axes.Axes
        ultraplot.axes.PlotAxes
        ultraplot.figure.Figure.subplot
        ultraplot.figure.Figure.add_subplot
        """
        # Cache of backend-specific gridliner adapters (major/minor).
        self._gridliner_adapters: dict[str, _GridlinerAdapter] = {}
        super().__init__(*args, **kwargs)

    @override
    def _sharey_limits(self, sharey: "GeoAxes") -> None:
        return self._share_limits_with(sharey, which="y")

    @override
    def _sharex_limits(self, sharex: "GeoAxes") -> None:
        return self._share_limits_with(sharex, which="x")

    def _share_limits_with(self, other: "GeoAxes", which: str) -> None:
        """
        Safely share limits and tickers without resetting things.
        """
        # NOTE: See _sharex_limits for notes
        if which == "x":
            this_ax = self._lonaxis
            other_ax = other._lonaxis
        else:
            this_ax = self._lataxis
            other_ax = other._lataxis
        for ax1, ax2 in ((other_ax, this_ax), (this_ax, other_ax)):
            ax1.set_view_interval(*ax2.get_view_interval())

        # Set the shared axis
        getattr(self, f"share{which}")(other)
        this_ax._copy_locator_properties(other_ax)

    def _is_rectilinear(self) -> bool:
        return _is_rectilinear_projection(self)

    def __share_axis_setup(
        self,
        other: "GeoAxes",
        *,
        which: str,
        labels: bool,
        limits: bool,
    ) -> None:
        level = getattr(self.figure, f"_share{which}")
        if getattr(self, f"_panel_share{which}_group") and self._is_panel_group_member(
            other
        ):
            level = 3
        if level not in range(5):  # must be internal error
            raise ValueError(f"Invalid sharing level sharex={level!r}.")
        if other in (None, self) or not isinstance(other, GeoAxes):
            return
        # Share future axis label changes. Implemented in _apply_axis_sharing().
        # Matplotlib only uses these attributes in __init__() and cla() to share
        # tickers -- all other builtin sharing features derives from shared x axes
        if level > 0 and labels:
            setattr(self, f"_share{which}", other)
        # Share future axis tickers, limits, and scales
        # NOTE: Only difference between levels 2 and 3 is level 3 hides ticklabels
        # labels. But this is done after the fact -- tickers are still shared.
        if level > 1 and limits:
            self._share_limits_with(other, which=which)

    @override
    def _sharey_setup(
        self, sharey: "GeoAxes", *, labels: bool = True, limits: bool = True
    ) -> None:
        """
        Configure shared axes accounting for panels. The input is the
        'parent' axes, from which this one will draw its properties.
        """
        super()._sharey_setup(sharey, labels=labels, limits=limits)
        return self.__share_axis_setup(sharey, which="y", labels=labels, limits=limits)

    @override
    def _sharex_setup(
        self, sharex: "GeoAxes", *, labels: bool = True, limits: bool = True
    ) -> None:
        # Share panels across *different* subplots
        super()._sharex_setup(sharex, labels=labels, limits=limits)
        return self.__share_axis_setup(sharex, which="x", labels=labels, limits=limits)

    def _toggle_ticks(self, label: str | None, which: str) -> None:
        """
        Ticks are controlled by matplotlib independent of the backend. We can toggle ticks on and of depending on the desired position.
        """
        if not isinstance(label, str):
            return

        # Only allow "lrbt" and "all" or "both"
        label = label.replace("top", "t")
        label = label.replace("bottom", "b")
        label = label.replace("left", "l")
        label = label.replace("right", "r")
        match label:
            case _ if len(label) == 2 and "t" in label and "b" in label:
                self.xaxis.set_ticks_position("both")
            case _ if len(label) == 2 and "l" in label and "r" in label:
                self.yaxis.set_ticks_position("both")
            case "t":
                self.xaxis.set_ticks_position("top")
            case "b":
                self.xaxis.set_ticks_position("bottom")
            case "l":
                self.yaxis.set_ticks_position("left")
            case "r":
                self.yaxis.set_ticks_position("right")
            case "all":
                self.xaxis.set_ticks_position("both")
                self.yaxis.set_ticks_position("both")
            case "both":
                if which == "x":
                    self.xaxis.set_ticks_position("both")
                else:
                    self.yaxis.set_ticks_position("both")
            case _:
                warnings._warn_ultraplot(
                    f"Not toggling {label=}. Input was not understood. Valid values are ['left', 'right', 'top', 'bottom', 'all', 'both']"
                )

    def _set_gridliner_adapter(
        self, which: str, adapter: Optional[_GridlinerAdapter]
    ) -> None:
        if adapter is None:
            self._gridliner_adapters.pop(which, None)
        else:
            self._gridliner_adapters[which] = adapter

    def _get_gridliner_adapter(self, which: str) -> Optional[_GridlinerAdapter]:
        return self._gridliner_adapters.get(which)

    def _gridliner_adapter(
        self, which: str, *, create: bool = True
    ) -> Optional[_GridlinerAdapter]:
        """
        Return a cached gridliner adapter, optionally creating it via the backend
        builder when missing.
        """
        adapter = self._get_gridliner_adapter(which)
        if adapter is None and create:
            builder = getattr(self, "_build_gridliner_adapter", None)
            if builder is not None:
                adapter = builder(which)
                self._set_gridliner_adapter(which, adapter)
        return adapter

    def _iter_gridliner_adapters(self, which: str) -> Iterator[_GridlinerAdapter]:
        """
        Yield available gridliner adapters for the requested tick selection.
        """
        if which in ("major", "both"):
            adapter = self._gridliner_adapter("major")
            if adapter is not None:
                yield adapter
        if which in ("minor", "both"):
            adapter = self._gridliner_adapter("minor")
            if adapter is not None:
                yield adapter

    def _gridliner_tick_positions(
        self, axis: str, *, which: str = "major"
    ) -> np.ndarray:
        """
        Return tick positions from the backend gridliner for a given axis.
        """
        if axis not in ("x", "y"):
            raise ValueError(f"Invalid axis: {axis!r}")
        adapter = self._gridliner_adapter(which)
        if adapter is None:
            return np.asarray([])
        return adapter.tick_positions(
            axis, lonaxis=self._lonaxis, lataxis=self._lataxis
        )

    @override
    def tick_params(self, *args: Any, **kwargs: Any) -> Any:
        """
        Apply tick parameters and mirror a subset of settings onto the backend
        gridliner artists so gridline labels respond to common tick tweaks.
        """
        result = super().tick_params(*args, **kwargs)

        axis = kwargs.get("axis", "both")
        which = kwargs.get("which", "major")
        pad = kwargs.get("pad", None)
        labelsize = kwargs.get("labelsize", None)
        labelcolor = kwargs.get(
            "labelcolor", kwargs.get("colors", kwargs.get("color", None))
        )
        labelrotation = kwargs.get("labelrotation", None)
        linecolor = kwargs.get("colors", kwargs.get("color", None))
        linewidth = kwargs.get("width", kwargs.get("linewidth", None))

        adapters = tuple(self._iter_gridliner_adapters(which))
        if not adapters:
            return result

        for adapter in adapters:
            adapter.apply_style(
                axis=axis,
                pad=pad,
                labelsize=labelsize,
                labelcolor=labelcolor,
                labelrotation=labelrotation,
                linecolor=linecolor,
                linewidth=linewidth,
            )

        # Toggle label visibility for major gridliners when requested.
        if which in ("major", "both"):
            adapter = self._gridliner_adapter("major")
            toggles = {}
            if axis in ("x", "both"):
                for key in ("labelbottom", "labeltop"):
                    if key in kwargs:
                        toggles[key] = kwargs[key]
            if axis in ("y", "both"):
                for key in ("labelleft", "labelright"):
                    if key in kwargs:
                        toggles[key] = kwargs[key]
            if toggles and adapter is not None:
                adapter.toggle_labels(**toggles)

        self.stale = True
        return result

    def _apply_axis_sharing(self) -> None:
        """
        Enforce the "shared" axis labels and axis tick labels. If this is not
        called at drawtime, "shared" labels can be inadvertantly turned off.

        Notes:
            - Critical to apply labels to *shared* axes attributes rather than testing
                extents or we end up sharing labels with twin axes.
            - Similar to how align_super_labels() calls apply_title_above(), this is called
                inside align_axis_labels() so we align the correct text.
            - The "panel sharing group" refers to axes and panels *above* the bottommost
                or to the *right* of the leftmost panel. But the sharing level used for
                the leftmost and bottommost is the *figure* sharing level.
        """

        # Share axis labels
        if self._sharex and self.figure._sharex >= 1:
            if self.figure._is_share_label_group_member(self, "x"):
                pass
            elif self.figure._is_share_label_group_member(self._sharex, "x"):
                self.xaxis.label.set_visible(False)
            else:
                labels._transfer_label(self.xaxis.label, self._sharex.xaxis.label)
                self.xaxis.label.set_visible(False)
        if self._sharey and self.figure._sharey >= 1:
            if self.figure._is_share_label_group_member(self, "y"):
                pass
            elif self.figure._is_share_label_group_member(self._sharey, "y"):
                self.yaxis.label.set_visible(False)
            else:
                labels._transfer_label(self.yaxis.label, self._sharey.yaxis.label)
                self.yaxis.label.set_visible(False)

        # Share interval x
        if self._sharex and self.figure._sharex >= 2:
            self._lonaxis.set_view_interval(*self._sharex._lonaxis.get_view_interval())
            self._lonaxis.set_minor_locator(self._sharex._lonaxis.get_minor_locator())

        # Share interval y
        if self._sharey and self.figure._sharey >= 2:
            self._lataxis.set_view_interval(*self._sharey._lataxis.get_view_interval())
            self._lataxis.set_minor_locator(self._sharey._lataxis.get_minor_locator())

    def _apply_aspect_and_adjust_panels(self, *, tol: float = 1e-9) -> None:
        """
        Apply aspect and then align panels to the adjusted axes box.

        Notes
        -----
        Cartopy and basemap use different tolerances when detecting whether
        apply_aspect() actually changed the axes position.
        """
        self.apply_aspect()
        self._adjust_panel_positions(tol=tol)

    def _adjust_panel_positions(self, *, tol: float = 1e-9) -> None:
        """
        Adjust panel positions to align with the aspect-constrained main axes.
        After apply_aspect() shrinks the main axes, panels should flank the actual
        map boundaries rather than the full gridspec allocation.
        """
        if not getattr(self, "_panel_dict", None):
            return  # no panels to adjust

        # Current (aspect-adjusted) position
        main_pos = getattr(self, "_position", None) or self.get_position()

        # Subplot-spec position before apply_aspect(). This is the true "gridspec slot"
        # and remains well-defined even if we temporarily modify axes positions.
        try:
            ss = self.get_subplotspec()
            original_pos = ss.get_position(self.figure) if ss is not None else None
        except Exception:
            original_pos = None
        if original_pos is None:
            original_pos = getattr(
                self, "_originalPosition", None
            ) or self.get_position(original=True)

        # Only adjust if apply_aspect() actually changed the position (tolerance
        # avoids float churn that can trigger unnecessary layout updates).
        if (
            abs(main_pos.x0 - original_pos.x0) <= tol
            and abs(main_pos.y0 - original_pos.y0) <= tol
            and abs(main_pos.width - original_pos.width) <= tol
            and abs(main_pos.height - original_pos.height) <= tol
        ):
            return

        # Map original -> adjusted coordinates (only along the "long" axis of the
        # panel, so span overrides across subplot rows/cols are preserved).
        sx = main_pos.width / original_pos.width if original_pos.width else 1.0
        sy = main_pos.height / original_pos.height if original_pos.height else 1.0
        ox0, oy0 = original_pos.x0, original_pos.y0
        ox1, oy1 = (
            original_pos.x0 + original_pos.width,
            original_pos.y0 + original_pos.height,
        )
        mx0, my0 = main_pos.x0, main_pos.y0

        for side, panels in self._panel_dict.items():
            for panel in panels:
                # Use the panel subplot-spec box as the baseline (not its current
                # original position) to avoid accumulated adjustments.
                try:
                    ss = panel.get_subplotspec()
                    panel_pos = (
                        ss.get_position(panel.figure) if ss is not None else None
                    )
                except Exception:
                    panel_pos = None
                if panel_pos is None:
                    panel_pos = panel.get_position(original=True)
                px0, py0 = panel_pos.x0, panel_pos.y0
                px1, py1 = (
                    panel_pos.x0 + panel_pos.width,
                    panel_pos.y0 + panel_pos.height,
                )

                # Use _set_position when available to avoid layoutbox side effects
                # from public set_position() on newer matplotlib versions.
                setter = getattr(panel, "_set_position", panel.set_position)

                if side == "left":
                    # Calculate original gap between panel and main axes
                    gap = original_pos.x0 - (panel_pos.x0 + panel_pos.width)
                    # Position panel to the left of the adjusted main axes
                    new_x0 = main_pos.x0 - panel_pos.width - gap
                    if py0 <= oy0 + tol and py1 >= oy1 - tol:
                        new_y0, new_h = my0, main_pos.height
                    else:
                        new_y0 = my0 + (panel_pos.y0 - oy0) * sy
                        new_h = panel_pos.height * sy
                    new_pos = [new_x0, new_y0, panel_pos.width, new_h]
                elif side == "right":
                    # Calculate original gap
                    gap = panel_pos.x0 - (original_pos.x0 + original_pos.width)
                    # Position panel to the right of the adjusted main axes
                    new_x0 = main_pos.x0 + main_pos.width + gap
                    if py0 <= oy0 + tol and py1 >= oy1 - tol:
                        new_y0, new_h = my0, main_pos.height
                    else:
                        new_y0 = my0 + (panel_pos.y0 - oy0) * sy
                        new_h = panel_pos.height * sy
                    new_pos = [new_x0, new_y0, panel_pos.width, new_h]
                elif side == "top":
                    # Calculate original gap
                    gap = panel_pos.y0 - (original_pos.y0 + original_pos.height)
                    # Position panel above the adjusted main axes
                    new_y0 = main_pos.y0 + main_pos.height + gap
                    if px0 <= ox0 + tol and px1 >= ox1 - tol:
                        new_x0, new_w = mx0, main_pos.width
                    else:
                        new_x0 = mx0 + (panel_pos.x0 - ox0) * sx
                        new_w = panel_pos.width * sx
                    new_pos = [new_x0, new_y0, new_w, panel_pos.height]
                elif side == "bottom":
                    # Calculate original gap
                    gap = original_pos.y0 - (panel_pos.y0 + panel_pos.height)
                    # Position panel below the adjusted main axes
                    new_y0 = main_pos.y0 - panel_pos.height - gap
                    if px0 <= ox0 + tol and px1 >= ox1 - tol:
                        new_x0, new_w = mx0, main_pos.width
                    else:
                        new_x0 = mx0 + (panel_pos.x0 - ox0) * sx
                        new_w = panel_pos.width * sx
                    new_pos = [new_x0, new_y0, new_w, panel_pos.height]
                else:
                    # Unknown side, skip adjustment
                    continue

                # Panels typically have aspect='auto', which causes matplotlib to
                # reset their *active* position to their *original* position inside
                # apply_aspect()/get_position(). Update both so the change persists.
                try:
                    setter(new_pos, which="both")
                except TypeError:  # older matplotlib
                    setter(new_pos)

    def _get_gridliner_labels(
        self,
        bottom: bool | str | None = None,
        top: bool | str | None = None,
        left: bool | str | None = None,
        right: bool | str | None = None,
    ) -> dict[str, list[mtext.Text]]:
        adapter = self._gridliner_adapter("major")
        if adapter is None:
            return {}
        return adapter.labels_for_sides(
            bottom=bottom,
            top=top,
            left=left,
            right=right,
        )

    def _toggle_gridliner_labels(
        self,
        labeltop: bool | str | None = None,
        labelbottom: bool | str | None = None,
        labelleft: bool | str | None = None,
        labelright: bool | str | None = None,
        geo: bool | str | None = None,
    ) -> None:
        """
        Toggle visibility of gridliner labels for each direction via the backend
        adapter.

        Parameters
        ----------
        labeltop, labelbottom, labelleft, labelright : bool or None
            Whether to show labels on each side. If None, do not change.
        geo : optional
            Not used in this method.
        """
        adapter = self._gridliner_adapter("major")
        if adapter is None:
            return
        adapter.toggle_labels(
            labelleft=labelleft,
            labelright=labelright,
            labelbottom=labelbottom,
            labeltop=labeltop,
            geo=geo,
        )

    @override
    def _is_ticklabel_on(self, side: str) -> bool:
        """
        Check if tick labels are visible on the requested side via the backend adapter.
        """
        adapter = self._gridliner_adapter("major")
        if adapter is None:
            return False
        return adapter.is_label_on(side)

    @override
    def draw(self, renderer: Any = None, *args: Any, **kwargs: Any) -> None:
        # Perform extra post-processing steps
        # NOTE: In *principle* axis sharing application step goes here. But should
        # already be complete because auto_layout() (called by figure pre-processor)
        # has to run it before aligning labels. So this is harmless no-op.
        self._apply_axis_sharing()
        super().draw(renderer, *args, **kwargs)

    def _get_lonticklocs(self, which: str = "major") -> np.ndarray:
        """
        Retrieve longitude tick locations.
        """
        # Get tick locations from dummy axes
        # NOTE: This is workaround for: https://github.com/SciTools/cartopy/issues/1564
        # Since _axes_domain is wrong we determine tick locations ourselves with
        # more accurate extent tracked by _LatAxis and _LonAxis.
        axis = self._lonaxis
        if which == "major":
            lines = axis.get_majorticklocs()
        else:
            lines = axis.get_minorticklocs()
        return lines

    def _get_latticklocs(self, which: str = "major") -> np.ndarray:
        """
        Retrieve latitude tick locations.
        """
        axis = self._lataxis
        if which == "major":
            lines = axis.get_majorticklocs()
        else:
            lines = axis.get_minorticklocs()
        return lines

    def _set_view_intervals(self, extent: Sequence[float]) -> None:
        """
        Update view intervals for lon and lat axis.
        """
        self._lonaxis.set_view_interval(*extent[:2])
        self._lataxis.set_view_interval(*extent[2:])

    @staticmethod
    def _to_label_array(arg: Any, lon: bool = True) -> list[bool | None]:
        """
        Convert labels argument to length-5 boolean array.
        """
        array = arg
        which = "lon" if lon else "lat"
        array = np.atleast_1d(array).tolist()
        if len(array) == 1 and array[0] is None:
            array = [None] * 5
        elif all(isinstance(_, str) for _ in array):
            strings = array  # iterate over list of strings
            array = [False] * 5
            opts = ("left", "right", "bottom", "top", "geo")
            for string in strings:
                string = string.replace("left", "l")
                string = string.replace("right", "r")
                string = string.replace("bottom", "b")
                string = string.replace("top", "t")
                if string == "all":
                    string = "lrbt"
                elif string == "both":
                    string = "bt" if lon else "lr"
                elif string == "neither":
                    string = ""
                elif string in opts:
                    string = string[0]
                if set(string) - set("lrbtg"):
                    raise ValueError(
                        f"Invalid {which}label string {string!r}. Must be one of "
                        + ", ".join(map(repr, (*opts, "neither", "both", "all")))
                        + " or a string of single-letter characters like 'lr'."
                    )
                for char in string:
                    array["lrbtg".index(char)] = True
                if rc["grid.geolabels"] and any(array):
                    # Geo labels only apply if any edge labels are enabled.
                    array[4] = True  # possibly toggle geo spine labels
        elif not any(isinstance(_, str) for _ in array):
            if len(array) == 1:
                array.append(None)
            if len(array) == 2:
                array = [None, None, *array] if lon else [*array, None, None]
            if len(array) == 4:
                b = (
                    any(a for a in array if a is not None)
                    if rc["grid.geolabels"]
                    else None
                )
                array.append(b)
            if len(array) != 5:
                raise ValueError(f"Invald boolean label array length {len(array)}.")
        else:
            raise ValueError(f"Invalid {which}label spec: {arg}.")
        return array

    def _format_init_basemap_boundary(self) -> None:
        """
        Initialize basemap boundaries before format triggers gridline work.

        Basemap can create a hidden boundary when gridlines are drawn before the
        map boundary is initialized, so we force initialization here.
        """
        if self._name != "basemap" or self._map_boundary is not None:
            return
        if self.projection.projection in self._proj_non_rectangular:
            patch = self.projection.drawmapboundary(ax=self)
            self._map_boundary = patch
        else:
            self.projection.set_axes_limits(self)  # initialize aspect ratio
            self._map_boundary = object()  # sentinel

    def _format_rc_context(
        self,
        kwargs: MutableMapping[str, Any],
        *,
        ticklen: Any,
        labelcolor: Any,
        labelsize: Any,
        labelweight: Any,
    ) -> tuple[dict[str, Any], int, Any]:
        """
        Pop rc overrides and prepare context settings for format().
        """
        rc_kw, rc_mode = _pop_rc(kwargs)
        ticklen = _not_none(ticklen, rc_kw.get("tick.len", None))
        labelcolor = _not_none(labelcolor, kwargs.get("color", None))
        if labelcolor is not None:
            rc_kw["grid.labelcolor"] = labelcolor
        if labelsize is not None:
            rc_kw["grid.labelsize"] = labelsize
        if labelweight is not None:
            rc_kw["grid.labelweight"] = labelweight
        return rc_kw, rc_mode, ticklen

    def _format_normalize_label_inputs(
        self,
        *,
        labels: Any,
        lonlabels: Any,
        latlabels: Any,
        loninline: bool | None,
        latinline: bool | None,
        inlinelabels: bool | None,
    ) -> tuple[Any, Any]:
        """
        Normalize label inputs before rc context is applied.
        """
        lonlabels = _not_none(lonlabels, labels)
        latlabels = _not_none(latlabels, labels)
        if "0.18" <= _version_cartopy < "0.20":
            lonlabels = _not_none(lonlabels, loninline, inlinelabels)
            latlabels = _not_none(latlabels, latinline, inlinelabels)
        return lonlabels, latlabels

    def _format_resolve_label_arrays(
        self, *, labels: Any, lonlabels: Any, latlabels: Any
    ) -> tuple[Any, Any, list[bool | None], list[bool | None]]:
        """
        Resolve label toggles and return label arrays for gridliners.
        """
        if lonlabels is None and latlabels is None:
            labels = _not_none(labels, rc.find("grid.labels", context=True))
            lonlabels = labels
            latlabels = labels
        else:
            lonlabels = _not_none(lonlabels, labels)
            latlabels = _not_none(latlabels, labels)

        self._toggle_ticks(lonlabels, "x")
        self._toggle_ticks(latlabels, "y")
        lonarray = self._to_label_array(lonlabels, lon=True)
        latarray = self._to_label_array(latlabels, lon=False)
        return lonlabels, latlabels, lonarray, latarray

    def _format_update_latmax(self, latmax: float | None) -> None:
        """
        Update the latitude gridline cutoff.
        """
        latmax = _not_none(latmax, rc.find("grid.latmax", context=True))
        if latmax is not None:
            self._lataxis.set_latmax(latmax)

    def _format_update_major_locators(
        self,
        *,
        lonlocator: Any,
        lonlines: Any,
        latlocator: Any,
        latlines: Any,
        lonlocator_kw: MutableMapping | None,
        lonlines_kw: MutableMapping | None,
        latlocator_kw: MutableMapping | None,
        latlines_kw: MutableMapping | None,
    ) -> None:
        """
        Update major longitude/latitude locators.
        """
        lonlocator = _not_none(lonlocator=lonlocator, lonlines=lonlines)
        latlocator = _not_none(latlocator=latlocator, latlines=latlines)
        if lonlocator is not None:
            lonlocator_kw = _not_none(
                lonlocator_kw=lonlocator_kw,
                lonlines_kw=lonlines_kw,
                default={},
            )
            locator = constructor.Locator(lonlocator, **lonlocator_kw)
            self._lonaxis.set_major_locator(locator)
        if latlocator is not None:
            latlocator_kw = _not_none(
                latlocator_kw=latlocator_kw,
                latlines_kw=latlines_kw,
                default={},
            )
            locator = constructor.Locator(latlocator, **latlocator_kw)
            self._lataxis.set_major_locator(locator)

    def _format_update_minor_locators(
        self,
        *,
        lonminorlocator: Any,
        lonminorlines: Any,
        latminorlocator: Any,
        latminorlines: Any,
        lonminorlocator_kw: MutableMapping | None,
        lonminorlines_kw: MutableMapping | None,
        latminorlocator_kw: MutableMapping | None,
        latminorlines_kw: MutableMapping | None,
    ) -> None:
        """
        Update minor longitude/latitude locators.
        """
        lonminorlocator = _not_none(
            lonminorlocator=lonminorlocator, lonminorlines=lonminorlines
        )
        latminorlocator = _not_none(
            latminorlocator=latminorlocator, latminorlines=latminorlines
        )
        if lonminorlocator is not None:
            lonminorlocator_kw = _not_none(
                lonminorlocator_kw=lonminorlocator_kw,
                lonminorlines_kw=lonminorlines_kw,
                default={},
            )
            locator = constructor.Locator(lonminorlocator, **lonminorlocator_kw)
            self._lonaxis.set_minor_locator(locator)
        if latminorlocator is not None:
            latminorlocator_kw = _not_none(
                latminorlocator_kw=latminorlocator_kw,
                latminorlines_kw=latminorlines_kw,
                default={},
            )
            locator = constructor.Locator(latminorlocator, **latminorlocator_kw)
            self._lataxis.set_minor_locator(locator)

    def _format_resolve_gridline_params(
        self,
        *,
        loninline: bool | None,
        latinline: bool | None,
        inlinelabels: bool | None,
        rotatelabels: bool | None,
        labelrotation: float | None,
        lonlabelrotation: float | None,
        latlabelrotation: float | None,
        labelpad: Any,
        dms: bool | None,
        nsteps: int | None,
    ) -> tuple[
        bool | None,
        bool | None,
        bool | None,
        float | None,
        float | None,
        Any,
        bool | None,
        int | None,
    ]:
        """
        Resolve gridline-related parameters with rc defaults.
        """
        loninline = _not_none(
            loninline, inlinelabels, rc.find("grid.inlinelabels", context=True)
        )
        latinline = _not_none(
            latinline, inlinelabels, rc.find("grid.inlinelabels", context=True)
        )
        rotatelabels = _not_none(
            rotatelabels, rc.find("grid.rotatelabels", context=True)
        )
        lonlabelrotation = _not_none(lonlabelrotation, labelrotation)
        latlabelrotation = _not_none(latlabelrotation, labelrotation)
        labelpad = _not_none(labelpad, rc.find("grid.labelpad", context=True))
        dms = _not_none(dms, rc.find("grid.dmslabels", context=True))
        nsteps = _not_none(nsteps, rc.find("grid.nsteps", context=True))
        return (
            loninline,
            latinline,
            rotatelabels,
            lonlabelrotation,
            latlabelrotation,
            labelpad,
            dms,
            nsteps,
        )

    def _format_update_formatters(
        self,
        *,
        lonformatter: Any,
        latformatter: Any,
        lonformatter_kw: MutableMapping | None,
        latformatter_kw: MutableMapping | None,
        dms: bool | None,
    ) -> None:
        """
        Update longitude/latitude formatters and DMS flags.
        """
        if lonformatter is not None:
            lonformatter_kw = lonformatter_kw or {}
            formatter = constructor.Formatter(lonformatter, **lonformatter_kw)
            self._lonaxis.set_major_formatter(formatter)
        if latformatter is not None:
            latformatter_kw = latformatter_kw or {}
            formatter = constructor.Formatter(latformatter, **latformatter_kw)
            self._lataxis.set_major_formatter(formatter)
        if dms is not None:  # harmless if these are not GeoLocators
            self._lonaxis.get_major_formatter()._dms = dms
            self._lataxis.get_major_formatter()._dms = dms
            self._lonaxis.get_major_locator()._dms = dms
            self._lataxis.get_major_locator()._dms = dms

    def _format_apply_grid_updates(
        self,
        *,
        lonlim: tuple[float | None, float | None] | None,
        latlim: tuple[float | None, float | None] | None,
        boundinglat: float | None,
        longrid: bool | None,
        latgrid: bool | None,
        longridminor: bool | None,
        latgridminor: bool | None,
        lonarray: Sequence[bool | None],
        latarray: Sequence[bool | None],
        loninline: bool | None,
        latinline: bool | None,
        rotatelabels: bool | None,
        lonlabelrotation: float | None,
        latlabelrotation: float | None,
        labelpad: Any,
        nsteps: int | None,
    ) -> tuple[tuple[float | None, float | None], tuple[float | None, float | None]]:
        """
        Apply extent, features, and gridline updates for format().
        """
        lonlim = _not_none(lonlim, default=(None, None))
        latlim = _not_none(latlim, default=(None, None))
        self._update_extent(lonlim=lonlim, latlim=latlim, boundinglat=boundinglat)
        self._update_features()
        self._update_major_gridlines(
            longrid=longrid,
            latgrid=latgrid,  # gridline toggles
            lonarray=lonarray,
            latarray=latarray,  # label toggles
            loninline=loninline,
            latinline=latinline,
            rotatelabels=rotatelabels,
            lonlabelrotation=lonlabelrotation,
            latlabelrotation=latlabelrotation,
            labelpad=labelpad,
            nsteps=nsteps,
        )
        self._update_minor_gridlines(
            longrid=longridminor,
            latgrid=latgridminor,
            nsteps=nsteps,
        )
        return lonlim, latlim

    def _format_apply_ticklen(
        self,
        *,
        lonlim: tuple[float | None, float | None] | None,
        latlim: tuple[float | None, float | None] | None,
        boundinglat: float | None,
        extent_requested: bool,
        ticklen: Any,
        lonticklen: Any,
        latticklen: Any,
    ) -> None:
        """
        Apply tick length updates, including any extent refresh for geoticks.
        """
        lonticklen = _not_none(lonticklen, ticklen)
        latticklen = _not_none(latticklen, ticklen)

        if lonticklen or latticklen:
            # Only add warning when ticks are given
            if _is_rectilinear_projection(self):
                self._add_geoticks("x", lonticklen, ticklen)
                self._add_geoticks("y", latticklen, ticklen)
                # If latlim is set to None it resets
                # the view; this affects the visible range
                # we need to force this to prevent
                # side effects
                if latlim is not None and latlim == (None, None):
                    latlim = self._lataxis.get_view_interval()
                if lonlim is not None and lonlim == (None, None):
                    lonlim = self._lonaxis.get_view_interval()
                if not extent_requested and self._name == "cartopy":
                    extent = (
                        *self._lonaxis.get_view_interval(),
                        *self._lataxis.get_view_interval(),
                    )
                    self.set_extent(extent, crs=ccrs.PlateCarree())
                elif extent_requested and (
                    boundinglat is not None
                    or (lonlim is not None and lonlim != (None, None))
                    or (latlim is not None and latlim != (None, None))
                ):
                    self._update_extent(
                        lonlim=lonlim, latlim=latlim, boundinglat=boundinglat
                    )
            else:
                warnings._warn_ultraplot(
                    f"Projection is not rectilinear. Ignoring {lonticklen=} and {latticklen=} settings."
                )

    # Format flow:
    # 1) init basemap boundary
    # 2) enter rc context and resolve label/locator/formatter inputs
    # 3) apply extent, features, and gridlines
    # 4) apply tick lengths and defer to parent format
    @docstring._snippet_manager
    def format(
        self,
        *,
        extent: str | None = None,
        round: bool | None = None,
        lonlim: tuple[float | None, float | None] | None = None,
        latlim: tuple[float | None, float | None] | None = None,
        boundinglat: float | None = None,
        longrid: bool | None = None,
        latgrid: bool | None = None,
        longridminor: bool | None = None,
        latgridminor: bool | None = None,
        ticklen: Any = None,
        lonticklen: Any = None,
        latticklen: Any = None,
        latmax: float | None = None,
        nsteps: int | None = None,
        lonlocator: Any = None,
        lonlines: Any = None,
        latlocator: Any = None,
        latlines: Any = None,
        lonminorlocator: Any = None,
        lonminorlines: Any = None,
        latminorlocator: Any = None,
        latminorlines: Any = None,
        lonlocator_kw: MutableMapping | None = None,
        lonlines_kw: MutableMapping | None = None,
        latlocator_kw: MutableMapping | None = None,
        latlines_kw: MutableMapping | None = None,
        lonminorlocator_kw: MutableMapping | None = None,
        lonminorlines_kw: MutableMapping | None = None,
        latminorlocator_kw: MutableMapping | None = None,
        latminorlines_kw: MutableMapping | None = None,
        lonformatter: Any = None,
        latformatter: Any = None,
        lonformatter_kw: MutableMapping | None = None,
        latformatter_kw: MutableMapping | None = None,
        labels: Any = None,
        latlabels: Any = None,
        lonlabels: Any = None,
        rotatelabels: bool | None = None,
        labelrotation: float | None = None,
        lonlabelrotation: float | None = None,
        latlabelrotation: float | None = None,
        loninline: bool | None = None,
        latinline: bool | None = None,
        inlinelabels: bool | None = None,
        dms: bool | None = None,
        labelpad: Any = None,
        labelcolor: Any = None,
        labelsize: Any = None,
        labelweight: Any = None,
        **kwargs: Any,
    ) -> None:
        """
        Modify map limits, longitude and latitude
        gridlines, geographic features, and more.

        Parameters
        ----------
        %(geo.format)s

        Other parameters
        ----------------
        %(axes.format)s
        %(figure.format)s
        %(rc.format)s

        See also
        --------
        ultraplot.axes.Axes.format
        ultraplot.config.Configurator.context
        """
        self._format_init_basemap_boundary()
        lonlabels, latlabels = self._format_normalize_label_inputs(
            labels=labels,
            lonlabels=lonlabels,
            latlabels=latlabels,
            loninline=loninline,
            latinline=latinline,
            inlinelabels=inlinelabels,
        )
        rc_kw, rc_mode, ticklen = self._format_rc_context(
            kwargs,
            ticklen=ticklen,
            labelcolor=labelcolor,
            labelsize=labelsize,
            labelweight=labelweight,
        )
        with rc.context(rc_kw, mode=rc_mode):
            # Apply extent mode first
            # NOTE: We deprecate autoextent on _CartopyAxes with _rename_kwargs which
            # does not translate boolean flag. So here apply translation.
            if extent is not None and not isinstance(extent, str):
                extent = ("globe", "auto")[int(bool(extent))]
            extent_requested = (
                boundinglat is not None or lonlim is not None or latlim is not None
            )
            self._update_boundary(round)
            self._update_extent_mode(extent, boundinglat)

            # Retrieve label toggles
            # NOTE: Cartopy 0.18 and 0.19 inline labels require any of
            # top, bottom, left, or right to be toggled then ignores them.
            # Later versions of cartopy permit both or neither labels.
            lonlabels, latlabels, lonarray, latarray = (
                self._format_resolve_label_arrays(
                    labels=labels,
                    lonlabels=lonlabels,
                    latlabels=latlabels,
                )
            )
            self._format_update_latmax(latmax)
            self._format_update_major_locators(
                lonlocator=lonlocator,
                lonlines=lonlines,
                latlocator=latlocator,
                latlines=latlines,
                lonlocator_kw=lonlocator_kw,
                lonlines_kw=lonlines_kw,
                latlocator_kw=latlocator_kw,
                latlines_kw=latlines_kw,
            )
            self._format_update_minor_locators(
                lonminorlocator=lonminorlocator,
                lonminorlines=lonminorlines,
                latminorlocator=latminorlocator,
                latminorlines=latminorlines,
                lonminorlocator_kw=lonminorlocator_kw,
                lonminorlines_kw=lonminorlines_kw,
                latminorlocator_kw=latminorlocator_kw,
                latminorlines_kw=latminorlines_kw,
            )
            (
                loninline,
                latinline,
                rotatelabels,
                lonlabelrotation,
                latlabelrotation,
                labelpad,
                dms,
                nsteps,
            ) = self._format_resolve_gridline_params(
                loninline=loninline,
                latinline=latinline,
                inlinelabels=inlinelabels,
                rotatelabels=rotatelabels,
                labelrotation=labelrotation,
                lonlabelrotation=lonlabelrotation,
                latlabelrotation=latlabelrotation,
                labelpad=labelpad,
                dms=dms,
                nsteps=nsteps,
            )
            self._format_update_formatters(
                lonformatter=lonformatter,
                latformatter=latformatter,
                lonformatter_kw=lonformatter_kw,
                latformatter_kw=latformatter_kw,
                dms=dms,
            )
            lonlim, latlim = self._format_apply_grid_updates(
                lonlim=lonlim,
                latlim=latlim,
                boundinglat=boundinglat,
                longrid=longrid,
                latgrid=latgrid,
                longridminor=longridminor,
                latgridminor=latgridminor,
                lonarray=lonarray,
                latarray=latarray,
                loninline=loninline,
                latinline=latinline,
                rotatelabels=rotatelabels,
                lonlabelrotation=lonlabelrotation,
                latlabelrotation=latlabelrotation,
                labelpad=labelpad,
                nsteps=nsteps,
            )
        self._format_apply_ticklen(
            lonlim=lonlim,
            latlim=latlim,
            boundinglat=boundinglat,
            extent_requested=extent_requested,
            ticklen=ticklen,
            lonticklen=lonticklen,
            latticklen=latticklen,
        )

        # Parent format method
        super().format(rc_kw=rc_kw, rc_mode=rc_mode, **kwargs)

    def _add_geoticks(self, x_or_y: str, itick: Any, ticklen: Any) -> None:
        """
        Add tick marks to the geographic axes.

        Parameters
        ----------
        x_or_y : {'x', 'y'}
            The axis to add ticks to ('x' for longitude, 'y' for latitude).
        itick, ticklen : unit-spec, default: :rc:`tick.len`
            Major tick lengths for the x and y axis.
            %(units.pt)s
            Use the argument `ticklen` to set both at once.

        Notes
        -----
        This method handles proper tick mark drawing for geographic projections
        while respecting the current gridline settings.
        """

        size = _not_none(itick, ticklen)
        # Skip if no tick size specified
        if size is None:
            return
        # Convert unit spec to points and apply rc scaling factor.
        size = units(size) * rc["tick.len"]

        ax = getattr(self, f"{x_or_y}axis")

        # Get the tick positions based on the backend gridliner (adapter-aware).
        adapter = self._gridliner_adapter("major")
        is_basemap = self._name == "basemap"
        tick_positions = self._gridliner_tick_positions(x_or_y, which="major")
        if is_basemap:
            # Turn off the ticks otherwise they are double for basemap.
            ax.set_major_formatter(mticker.NullFormatter())

        # Always show the ticks
        ax.set_ticks(tick_positions)
        ax.set_visible(True)

        # Note: set grid_alpha to 0 as it is controlled through the gridlines_major
        # object (which is not the same ticker)
        params = ax.get_tick_params()
        # Minor ticks are shortened relative to major ticks.
        sizes = [
            size,
            _MINOR_TICK_SCALE * size if isinstance(size, (int, float)) else size,
        ]
        for size, which in zip(sizes, ["major", "minor"]):
            params.update({"length": size})
            params.pop("grid_alpha", None)
            self.tick_params(
                axis=x_or_y,
                which=which,
                grid_alpha=0,
                **params,
            )
        # Apply tick parameters
        # Move the labels outwards if specified
        gl = getattr(self, "_gridlines_major", None)
        if gl is not None and hasattr(gl, f"{x_or_y}padding"):
            # Cartopy gridliner padding is in points; scale matches tick size visually.
            setattr(gl, f"{x_or_y}padding", _GRIDLINER_PAD_SCALE * size)
        elif is_basemap and isinstance(adapter, _BasemapGridlinerAdapter):
            # For basemap backends, emulate the label placement like cartopy.
            self._add_gridline_labels(
                ax, (adapter.lonlines, adapter.latlines), padding=size
            )

        self.stale = True

    def _add_gridline_labels(
        self,
        ax: maxis.Axis,
        gl: tuple[GridlineDict, GridlineDict],
        padding: float | int = 8,
    ) -> None:
        """
        This function is intended for the Basemap backend
        and mirrors the label placement behavior of Cartopy.
        See: https://cartopy.readthedocs.io/stable/reference/generated/cartopy.mpl.gridliner.Gridliner.html
        """
        sides = dict()
        for which, formatter in zip("xy", gl):
            for loc, (lines, labels) in formatter.items():
                for i, label in enumerate(labels):
                    upper_end = True
                    position = label.get_position()

                    if which == "x":
                        if position[1] < 0:
                            upper_end = False
                    elif which == "y":
                        if position[0] < 0:
                            upper_end = False
                    line = lines[0] if upper_end else lines[-1]

                    shift_scale = 1 if upper_end else -1
                    path = line.get_path()
                    vertices = path.vertices
                    label.set_transform(line.get_transform())

                    if len(ax.get_major_ticks()) == 0:
                        continue

                    # Get correct line
                    tick = ax.get_major_ticks()[0]
                    which_line = 1 if shift_scale == 1 else 2
                    tickline = getattr(tick, f"tick{which_line}line")
                    position = np.array(label.get_position())
                    # Convert points to display units using DPI (72 points per inch).
                    size = (
                        _BASEMAP_LABEL_SIZE_SCALE
                        * (tick._size + label.get_fontsize() + padding)
                        * self.figure.dpi
                        / 72
                    )

                    offset = vertices[0]
                    if upper_end:
                        offset = vertices[-1]

                    if which == "x":
                        # Move y position
                        # Empirical scaling to mimic cartopy label spacing.
                        position[1] = (
                            offset[1] + shift_scale * size * _BASEMAP_LABEL_Y_SCALE
                        )
                        ha = "center"
                        va = "top" if shift_scale == 1 else "bottom"
                        if shift_scale == 1:
                            sides.setdefault("top", []).append(label)
                        else:
                            sides.setdefault("bottom", []).append(label)

                    else:
                        # Move x position
                        # Empirical scaling to mimic cartopy label spacing.
                        position[0] = (
                            offset[0] + shift_scale * size * _BASEMAP_LABEL_X_SCALE
                        )
                        ha = "left" if shift_scale == 1 else "right"
                        va = "center"
                        if shift_scale == 1:
                            sides.setdefault("right", []).append(label)
                        else:
                            sides.setdefault("left", []).append(label)

                    label.set_position(position)
                    label.set_horizontalalignment(ha)
                    label.set_verticalalignment(va)

        # Some labels are double in the list not sure why
        # Remove them for now
        for key, labels in sides.items():
            seen = set()
            for label in labels:
                pos = label.get_position()
                txt = label.get_text()
                if (pos, txt) not in seen:
                    seen.add((pos, txt))
                else:
                    label.set_visible(False)

    @property
    def gridlines_major(self) -> Any:
        """
        The cartopy `~cartopy.mpl.gridliner.Gridliner`
        used for major gridlines or a 2-tuple containing the
        (longitude, latitude) major gridlines returned by
        basemap's :func:`~mpl_toolkits.basemap.Basemap.drawmeridians`
        and :func:`~mpl_toolkits.basemap.Basemap.drawparallels`.
        This can be used for customization and debugging.
        """
        # Refresh adapters so external access sees up-to-date gridliner state.
        builder = getattr(self, "_build_gridliner_adapter", None)
        if builder is not None:
            self._set_gridliner_adapter("major", builder("major"))
        if self._name == "basemap":
            return (self._lonlines_major, self._latlines_major)
        else:
            return self._gridlines_major

    @property
    def gridlines_minor(self) -> Any:
        """
        The cartopy `~cartopy.mpl.gridliner.Gridliner`
        used for minor gridlines or a 2-tuple containing the
        (longitude, latitude) minor gridlines returned by
        basemap's :func:`~mpl_toolkits.basemap.Basemap.drawmeridians`
        and :func:`~mpl_toolkits.basemap.Basemap.drawparallels`.
        This can be used for customization and debugging.
        """
        # Refresh adapters so external access sees up-to-date gridliner state.
        builder = getattr(self, "_build_gridliner_adapter", None)
        if builder is not None:
            self._set_gridliner_adapter("minor", builder("minor"))
        if self._name == "basemap":
            return (self._lonlines_minor, self._latlines_minor)
        else:
            return self._gridlines_minor

    @property
    def projection(self) -> Any:
        """
        The cartopy `~cartopy.crs.Projection` or basemap `~mpl_toolkits.basemap.Basemap`
        instance associated with this axes.
        """
        return self._map_projection

    @projection.setter
    def projection(self, map_projection: Any) -> None:
        cls = self._proj_class
        if not isinstance(map_projection, cls):
            raise ValueError(f"Projection must be a {cls} instance.")
        self._map_projection = map_projection
        if hasattr(self, "_lonaxis") or hasattr(self, "_lataxis"):
            # Update the projection of the lon and lat axes
            self._lonaxis.get_major_formatter()._source_projection = map_projection
            self._lataxis.get_major_formatter()._source_projection = map_projection


class _CartopyAxes(GeoAxes, _GeoAxes):
    """
    Axes subclass for plotting cartopy projections.
    """

    _name = "cartopy"
    _name_aliases = ("geo", "geographic")  # default 'geographic' axes
    _proj_class = Projection
    _PANEL_TOL = 1e-9
    _proj_north = (
        pproj.NorthPolarStereo,
        pproj.NorthPolarGnomonic,
        pproj.NorthPolarAzimuthalEquidistant,
        pproj.NorthPolarLambertAzimuthalEqualArea,
    )
    _proj_south = (
        pproj.SouthPolarStereo,
        pproj.SouthPolarGnomonic,
        pproj.SouthPolarAzimuthalEquidistant,
        pproj.SouthPolarLambertAzimuthalEqualArea,
    )
    _proj_polar = _proj_north + _proj_south

    # NOTE: The rename argument wrapper belongs here instead of format() because
    # these arguments were previously only accepted during initialization.
    @warnings._rename_kwargs("0.10", circular="round", autoextent="extent")
    def __init__(self, *args: Any, map_projection: Any = None, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        map_projection : ~cartopy.crs.Projection
            The map projection.
        *args, **kwargs
            Passed to `GeoAxes`.
        """
        # Initialize axes. Note that critical attributes like outline_patch
        # needed by _format_apply are added before it is called.
        import cartopy  # noqa: F401 verify package is available

        self.projection = map_projection  # verify
        polar = isinstance(self.projection, self._proj_polar)
        latmax = 80 if polar else 90  # default latmax
        self._is_round = False
        self._boundinglat = None  # NOTE: must start at None so _update_extent acts
        self._gridlines_major = None
        self._gridlines_minor = None
        self._lonaxis = _LonAxis(self)
        self._lataxis = _LatAxis(self, latmax=latmax)
        # 'map_projection' argument is deprecated since cartopy 0.21 and
        # replaced by 'projection'.
        if _version_cartopy >= "0.21":
            super().__init__(*args, projection=self.projection, **kwargs)
        else:
            super().__init__(*args, map_projection=self.projection, **kwargs)
        for axis in (self.xaxis, self.yaxis):
            axis.set_tick_params(which="both", size=0)  # prevent extra label offset

    @staticmethod
    def _get_circle_path(N: int = 100) -> mpath.Path:
        """
        Return a circle `~matplotlib.path.Path` used as the outline for polar
        stereographic, azimuthal equidistant, Lambert conformal, and gnomonic
        projections. This was developed from `this cartopy example \
    <https://cartopy.readthedocs.io/v0.25.0.post2/gallery/lines_and_polygons/always_circular_stereo.html>`__.
        """
        theta = np.linspace(0, 2 * np.pi, N)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        return mpath.Path(verts * radius + center)

    def _get_global_extent(self) -> list[float]:
        """
        Return the global extent with meridian properly shifted.
        """
        lon0 = self._get_lon0()
        return [-180 + lon0, 180 + lon0, -90, 90]

    def _get_lon0(self) -> float:
        """
        Get the central longitude. Default is ``0``.
        """
        return self.projection.proj4_params.get("lon_0", 0)

    def gridlines(
        self,
        crs: Any = None,
        draw_labels: bool | str | None = False,
        xlocs: mticker.Locator | Sequence[float] | None = None,
        ylocs: mticker.Locator | Sequence[float] | None = None,
        dms: bool = False,
        x_inline: bool | None = None,
        y_inline: bool | None = None,
        auto_inline: bool = True,
        xformatter: Any = None,
        yformatter: Any = None,
        xlim: Sequence[float] | None = None,
        ylim: Sequence[float] | None = None,
        rotate_labels: bool | float | None = None,
        xlabel_style: MutableMapping[str, Any] | None = None,
        ylabel_style: MutableMapping[str, Any] | None = None,
        labels_bbox_style: MutableMapping[str, Any] | None = None,
        xpadding: float | None = 5,
        ypadding: float | None = 5,
        offset_angle: float = 25,
        auto_update: bool | None = None,
        formatter_kwargs: MutableMapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> _CartopyGridlinerProtocol:
        """
        Override cartopy gridlines to use a local Gridliner subclass.
        """
        if crs is None:
            crs = ccrs.PlateCarree(globe=self.projection.globe)
        gridliner_cls = _CartopyGridliner or cgridliner.Gridliner
        gl = gridliner_cls(
            self,
            crs=crs,
            draw_labels=draw_labels,
            xlocator=xlocs,
            ylocator=ylocs,
            collection_kwargs=kwargs,
            dms=dms,
            x_inline=x_inline,
            y_inline=y_inline,
            auto_inline=auto_inline,
            xformatter=xformatter,
            yformatter=yformatter,
            xlim=xlim,
            ylim=ylim,
            rotate_labels=rotate_labels,
            xlabel_style=xlabel_style,
            ylabel_style=ylabel_style,
            labels_bbox_style=labels_bbox_style,
            xpadding=xpadding,
            ypadding=ypadding,
            offset_angle=offset_angle,
            auto_update=auto_update,
            formatter_kwargs=formatter_kwargs,
        )
        self.add_artist(gl)
        return gl

    def _init_gridlines(self) -> _CartopyGridlinerProtocol:
        """
        Create "major" and "minor" gridliners managed by ultraplot.
        """

        # Return gridliner using our subclass to isolate cartopy quirks.
        gl = self.gridlines(crs=ccrs.PlateCarree())
        gl.xlines = gl.ylines = False
        return gl

    def _build_gridliner_adapter(
        self, which: str = "major"
    ) -> Optional[_GridlinerAdapter]:
        gl = getattr(self, f"_gridlines_{which}", None)
        if gl is None:
            return None
        return _CartopyGridlinerAdapter(gl)

    def _update_background(self, **kwargs: Any) -> None:
        """
        Update the map background patches. This is called in `Axes.format`.
        """
        # TODO: Understand issue where setting global linewidth puts map boundary on
        # top of land patches, but setting linewidth with format() (even with separate
        # format() calls) puts map boundary underneath. Zorder seems to be totally
        # ignored and using spines vs. patch makes no difference.
        # NOTE: outline_patch is redundant, use background_patch instead
        kw_face, kw_edge = rc._get_background_props(native=False, **kwargs)
        kw_face["linewidth"] = 0
        kw_edge["facecolor"] = "none"
        if _version_cartopy >= "0.18":
            self.patch.update(kw_face)
            self.spines["geo"].update(kw_edge)
        else:
            self.background_patch.update(kw_face)
            self.outline_patch.update(kw_edge)

    def _update_boundary(self, round: bool | None = None) -> None:
        """
        Update the map boundary path.
        """
        round = _not_none(round, rc.find("geo.round", context=True))
        if round is None or not isinstance(self.projection, self._proj_polar):
            pass
        elif round:
            self._is_round = True
            self.set_boundary(self._get_circle_path(), transform=self.transAxes)
        elif not round and self._is_round:
            if hasattr(self, "_boundary"):
                self._boundary()
            else:
                warnings._warn_ultraplot("Failed to reset round map boundary.")

    def _update_extent_mode(
        self, extent: str | None = None, boundinglat: float | None = None
    ) -> None:
        """
        Update the extent mode.
        """
        # NOTE: Use set_global rather than set_extent() or _update_extent() for
        # simplicity. Uses projection.[xy]_limits which may not be strictly global.
        # NOTE: For some reason initial call to _set_view_intervals may change the
        # default boundary with extent='auto'. Try this in a robinson projection:
        # ax.contour(np.linspace(-90, 180, N), np.linspace(0, 90, N), np.zeros(N, N))
        extent = _not_none(extent, rc.find("geo.extent", context=True))
        if extent is None:
            return
        if extent not in ("globe", "auto"):
            raise ValueError(
                f"Invalid extent mode {extent!r}. Must be 'auto' or 'globe'."
            )
        polar = isinstance(self.projection, self._proj_polar)
        if not polar:
            self.set_global()
        else:
            if isinstance(self.projection, pproj.NorthPolarGnomonic):
                default_boundinglat = 30
            elif isinstance(self.projection, pproj.SouthPolarGnomonic):
                default_boundinglat = -30
            else:
                default_boundinglat = 0
            boundinglat = _not_none(boundinglat, default_boundinglat)
            self._update_extent(boundinglat=boundinglat)
        if extent == "auto":
            # NOTE: This will work even if applied after plotting stuff
            # and fixing the limits. Very easy to toggle on and off.
            self.set_autoscalex_on(True)
            self.set_autoscaley_on(True)

    def _update_extent(
        self,
        lonlim: tuple[float | None, float | None] | None = None,
        latlim: tuple[float | None, float | None] | None = None,
        boundinglat: float | None = None,
    ) -> None:
        """
        Set the projection extent.
        """
        # Projection extent
        # NOTE: Lon axis and lat axis extents are updated by set_extent.
        # WARNING: The set_extent method tries to set a *rectangle* between the *4*
        # (x, y) coordinate pairs (each corner), so something like (-180, 180, -90, 90)
        # will result in *line*, causing error! We correct this here.
        eps_small = 1e-10  # bug with full -180, 180 range when lon_0 != 0
        eps_label = 0.5  # larger epsilon to ensure boundary labels are included
        lon0 = self._get_lon0()
        proj = type(self.projection).__name__
        north = isinstance(self.projection, self._proj_north)
        south = isinstance(self.projection, self._proj_south)
        lonlim = _not_none(lonlim, (None, None))
        latlim = _not_none(latlim, (None, None))
        if north or south:
            if any(_ is not None for _ in (*lonlim, *latlim)):
                warnings._warn_ultraplot(
                    f'{proj!r} extent is controlled by "boundinglat", '
                    f"ignoring lonlim={lonlim!r} and latlim={latlim!r}."
                )
            if boundinglat is not None and boundinglat != self._boundinglat:
                lat0 = 90 if north else -90
                lon0 = self._get_lon0()
                extent = [
                    lon0 - 180 + eps_small,
                    lon0 + 180 - eps_small,
                    boundinglat,
                    lat0,
                ]
                self.set_extent(extent, crs=ccrs.PlateCarree())
                self._boundinglat = boundinglat

        # Rectangular extent
        else:
            if boundinglat is not None:
                warnings._warn_ultraplot(
                    f'{proj!r} extent is controlled by "lonlim" and "latlim", '
                    f"ignoring boundinglat={boundinglat!r}."
                )
            if any(_ is not None for _ in (*lonlim, *latlim)):
                lonlim = list(lonlim)
                if lonlim[0] is None:
                    lonlim[0] = lon0 - 180
                if lonlim[1] is None:
                    lonlim[1] = lon0 + 180
                # Expand limits slightly to ensure boundary labels are included
                # NOTE: We expand symmetrically (subtract from min, add to max) rather
                # than just shifting to avoid excluding boundary gridlines
                lonlim[0] -= eps_label
                lonlim[1] += eps_label
                latlim = list(latlim)
                if latlim[0] is None:
                    latlim[0] = -90
                if latlim[1] is None:
                    latlim[1] = 90
                latlim[0] -= eps_label
                latlim[1] += eps_label
                extent = lonlim + latlim
                self.set_extent(extent, crs=ccrs.PlateCarree())

    def _update_features(self) -> None:
        """
        Update geographic features.
        """
        # NOTE: The e.g. cfeature.COASTLINE features are just for convenience,
        # lo res versions. Use NaturalEarthFeature instead.
        # WARNING: Seems cartopy features cannot be updated! Updating _kwargs
        # attribute does *nothing*.
        reso = rc["reso"]  # resolution cannot be changed after feature created
        try:
            reso = constructor.RESOS_CARTOPY[reso]
        except KeyError:
            raise ValueError(
                f"Invalid resolution {reso!r}. Options are: "
                + ", ".join(map(repr, constructor.RESOS_CARTOPY))
                + "."
            )
        for name, args in constructor.FEATURES_CARTOPY.items():
            # Draw feature or toggle feature off
            b = rc.find(name, context=True)
            attr = f"_{name}_feature"
            feat = getattr(self, attr, None)
            drawn = feat is not None  # if exists, apply *updated* settings
            if b is not None:
                if not b:
                    if drawn:  # toggle existing feature off
                        feat.set_visible(False)
                else:
                    if not drawn:
                        feat = cfeature.NaturalEarthFeature(*args, reso)
                        feat = self.add_feature(feat)  # convert to FeatureArtist
                        setattr(self, attr, feat)

            # Update artist attributes (FeatureArtist._kwargs used back to v0.5).
            # For 'lines', need to specify edgecolor and facecolor
            # See: https://github.com/SciTools/cartopy/issues/803
            if feat is not None:
                kw = rc.category(name, context=drawn)
                if name in ("coast", "rivers", "borders", "innerborders"):
                    if "color" in kw:
                        kw.update({"edgecolor": kw.pop("color"), "facecolor": "none"})
                else:
                    kw.update({"linewidth": 0})
                if "zorder" in kw:
                    # NOTE: Necessary to update zorder directly because _kwargs
                    # attributes are not applied until draw()... at which point
                    # matplotlib is drawing in the order based on the *old* zorder.
                    feat.set_zorder(kw["zorder"])
                if hasattr(feat, "_kwargs"):
                    feat._kwargs.update(kw)
                    if _version_cartopy >= "0.23":
                        feat.set(**feat._kwargs)

    def _update_gridlines(
        self,
        gl: _CartopyGridlinerProtocol,
        which: str = "major",
        longrid: bool | None = None,
        latgrid: bool | None = None,
        nsteps: int | None = None,
    ) -> None:
        """
        Update gridliner object with axis locators, and toggle gridlines on and off.
        """
        # Update gridliner collection properties
        # WARNING: Here we use native matplotlib 'grid' rc param for geographic
        # gridlines. If rc mode is 1 (first format call) use context=False
        kwlines = rc._get_gridline_props(which=which, native=False)
        kwtext = rc._get_ticklabel_props(native=False)
        gl.collection_kwargs.update(kwlines)
        gl.xlabel_style.update(kwtext)
        gl.ylabel_style.update(kwtext)

        # Apply tick locations from dummy _LonAxis and _LatAxis axes
        # NOTE: This will re-apply existing gridline locations if unchanged.
        if nsteps is not None:
            gl.n_steps = nsteps
        # Set xlim and ylim for cartopy >= 0.19 to control which labels are displayed
        # NOTE: Don't set xlim/ylim here - let cartopy determine from the axes extent
        # The extent expansion in _update_extent should be sufficient to include boundary labels
        longrid = rc._get_gridline_bool(longrid, axis="x", which=which, native=False)
        if longrid is not None:
            gl.xlines = longrid
        latgrid = rc._get_gridline_bool(latgrid, axis="y", which=which, native=False)
        if latgrid is not None:
            gl.ylines = latgrid
        lonlines = self._get_lonticklocs(which=which)
        latlines = self._get_latticklocs(which=which)
        if _version_cartopy >= "0.18":  # see lukelbd/ultraplot#208
            lonlines = (np.asarray(lonlines) + 180) % 360 - 180  # only for cartopy
        gl.xlocator = mticker.FixedLocator(lonlines)
        gl.ylocator = mticker.FixedLocator(latlines)
        self.stale = True

    def _update_major_gridlines(
        self,
        longrid: bool | None = None,
        latgrid: bool | None = None,
        lonarray: Sequence[bool | None] | None = None,
        latarray: Sequence[bool | None] | None = None,
        loninline: bool | None = None,
        latinline: bool | None = None,
        labelpad: Any = None,
        rotatelabels: bool | None = None,
        lonlabelrotation: float | None = None,
        latlabelrotation: float | None = None,
        nsteps: int | None = None,
    ) -> None:
        """
        Update major gridlines.
        """
        # Update gridline locations and style
        gl = self._gridlines_major
        if gl is None:
            gl = self._gridlines_major = self._init_gridlines()
        self._update_gridlines(
            gl,
            which="major",
            longrid=longrid,
            latgrid=latgrid,
            nsteps=nsteps,
        )
        gl.xformatter = self._lonaxis.get_major_formatter()
        gl.yformatter = self._lataxis.get_major_formatter()
        # Turn the tick labels off as they are handled
        # separately from the matplotlib defaults
        self.xaxis.set_major_formatter(mticker.NullFormatter())
        self.yaxis.set_major_formatter(mticker.NullFormatter())

        # Update gridline label parameters
        # NOTE: Cartopy 0.18 and 0.19 can not draw both edge and inline labels. Instead
        # requires both a set 'side' and 'x_inline' is True (applied in GeoAxes.format).
        # NOTE: The 'xpadding' and 'ypadding' props were introduced in v0.16
        # with default 5 points, then set to default None in v0.18.
        # TODO: Cartopy has had two formatters for a while but we use the newer one.
        # See https://github.com/SciTools/cartopy/pull/1066
        if labelpad is not None:
            gl.xpadding = labelpad
            gl.ypadding = labelpad
        if loninline is not None:
            gl.x_inline = bool(loninline)
        if latinline is not None:
            gl.y_inline = bool(latinline)
        if rotatelabels is not None:
            gl.rotate_labels = bool(rotatelabels)  # ignored in cartopy < 0.18
        if lonlabelrotation is not None:
            gl.xlabel_style["rotation"] = lonlabelrotation
        if latlabelrotation is not None:
            gl.ylabel_style["rotation"] = latlabelrotation
        if latinline is not None or loninline is not None:
            lon, lat = loninline, latinline
            b = True if lon and lat else "x" if lon else "y" if lat else None
            gl.inline_labels = b  # ignored in cartopy < 0.20

        # Gridline label toggling
        # Issue warning instead of error!
        if _version_cartopy < "0.18" and not isinstance(
            self.projection, (ccrs.Mercator, ccrs.PlateCarree)
        ):
            if any(latarray):
                warnings._warn_ultraplot(
                    "Cannot add gridline labels to cartopy "
                    f"{type(self.projection).__name__} projection."
                )
                latarray = [False] * 5
            if any(lonarray):
                warnings._warn_ultraplot(
                    "Cannot add gridline labels to cartopy "
                    f"{type(self.projection).__name__} projection."
                )
                lonarray = [False] * 5
        # The ordering of these sides are important. The arrays are ordered lrbtg.
        sides = _gridliner_sides_from_arrays(
            lonarray,
            latarray,
            order=_CARTOPY_LABEL_SIDES,
            allow_xy=True,
            include_false=True,
        )
        if not sides and lonarray is not None and latarray is not None:
            # Preserve legacy behavior by calling the toggle even for no-op arrays.
            sides = {side: None for side in _CARTOPY_LABEL_SIDES}
        if sides:
            self._toggle_gridliner_labels(**sides)
        self._set_gridliner_adapter("major", self._build_gridliner_adapter("major"))

    def _update_minor_gridlines(
        self,
        longrid: bool | None = None,
        latgrid: bool | None = None,
        nsteps: int | None = None,
    ) -> None:
        """
        Update minor gridlines.
        """
        gl = self._gridlines_minor
        if gl is None:
            gl = self._gridlines_minor = self._init_gridlines()
        self._update_gridlines(
            gl,
            which="minor",
            longrid=longrid,
            latgrid=latgrid,
            nsteps=nsteps,
        )
        self._set_gridliner_adapter("minor", self._build_gridliner_adapter("minor"))

    def get_extent(self, crs: Any = None) -> Sequence[float]:
        # Get extent and try to repair longitude bounds.
        if crs is None:
            crs = ccrs.PlateCarree()
        extent = super().get_extent(crs=crs)
        if isinstance(crs, ccrs.PlateCarree):
            if np.isclose(extent[0], -180) and np.isclose(extent[-1], 180):
                # Repair longitude bounds to reflect dateline position
                # NOTE: This is critical so we can prevent duplicate gridlines
                # on dateline. See _update_gridlines.
                lon0 = self._get_lon0()
                extent[:2] = [lon0 - 180, lon0 + 180]
        return extent

    @override
    def draw(self, renderer: Any = None, *args: Any, **kwargs: Any) -> None:
        """
        Override draw to adjust panel positions for cartopy axes.

        Cartopy's apply_aspect() can shrink the main axes to enforce the projection
        aspect ratio. Panels occupy separate gridspec slots, so we reposition them
        after the main axes has applied its aspect but before the panel axes are drawn.
        """
        super().draw(renderer, *args, **kwargs)
        self._adjust_panel_positions(tol=self._PANEL_TOL)

    def get_tightbbox(self, renderer: Any, *args: Any, **kwargs: Any) -> Any:
        # Perform extra post-processing steps
        # For now this just draws the gridliners
        self._apply_axis_sharing()
        if self.get_autoscale_on() and self.ignore_existing_data_limits:
            self.autoscale_view()

        # Adjust location
        if _version_cartopy >= "0.18":
            self.patch._adjust_location()  # this does the below steps
        elif getattr(self.background_patch, "reclip", None) and hasattr(
            self.background_patch, "orig_path"
        ):
            clipped_path = self.background_patch.orig_path.clip_to_bbox(self.viewLim)
            self.outline_patch._path = clipped_path
            self.background_patch._path = clipped_path

        # Apply aspect, then ensure panels follow the aspect-constrained box.
        self._apply_aspect_and_adjust_panels(tol=self._PANEL_TOL)

        if _version_cartopy >= "0.23":
            gridliners = [
                a for a in self.artists if isinstance(a, cgridliner.Gridliner)
            ]
        else:
            gridliners = self._gridliners

        for gl in gridliners:
            if _version_cartopy >= "0.18":
                gl._draw_gridliner(renderer=renderer)
            else:
                gl._draw_gridliner(background_patch=self.background_patch)

        # Remove gridliners
        if _version_cartopy < "0.18":
            self._gridliners = []

        return super().get_tightbbox(renderer, *args, **kwargs)

    def set_extent(self, extent: Sequence[float], crs: Any = None) -> Any:
        # Fix paths, so axes tight bounding box gets correct box! From this issue:
        # https://github.com/SciTools/cartopy/issues/1207#issuecomment-439975083
        # Also record the requested longitude latitude extent so we can use these
        # values for LongitudeLocator and LatitudeLocator. Otherwise if longitude
        # extent is across dateline LongitudeLocator fails because get_extent()
        # reports -180 to 180: https://github.com/SciTools/cartopy/issues/1564
        # NOTE: This is *also* not perfect because if set_extent() was called
        # and extent crosses map boundary of rectangular projection, the *actual*
        # resulting extent is the opposite. But that means user has messed up anyway
        # so probably doesn't matter if gridlines are also wrong.
        if crs is None:
            crs = ccrs.PlateCarree()
        if isinstance(crs, ccrs.PlateCarree):
            self._set_view_intervals(extent)
            with rc.context(mode=2):  # do not reset gridline properties!
                if self._gridlines_major is not None:
                    self._update_gridlines(self._gridlines_major, which="major")
                if self._gridlines_minor is not None:
                    self._update_gridlines(self._gridlines_minor, which="minor")
            if _version_cartopy < "0.18":
                clipped_path = self.outline_patch.orig_path.clip_to_bbox(self.viewLim)
                self.outline_patch._path = clipped_path
                self.background_patch._path = clipped_path
        return super().set_extent(extent, crs=crs)

    def set_global(self) -> Any:
        # Set up "global" extent and update _LatAxis and _LonAxis view intervals
        result = super().set_global()
        self._set_view_intervals(self._get_global_extent())
        return result


class _BasemapAxes(GeoAxes):
    """
    Axes subclass for plotting basemap projections.
    """

    _name = "basemap"
    _proj_class = Basemap
    _proj_north = ("npaeqd", "nplaea", "npstere")
    _proj_south = ("spaeqd", "splaea", "spstere")
    _proj_polar = _proj_north + _proj_south
    _proj_non_rectangular = _proj_polar + (  # do not use axes spines as boundaries
        "ortho",
        "geos",
        "nsper",
        "moll",
        "hammer",
        "robin",
        "eck4",
        "kav7",
        "mbtfpq",
        "sinu",
        "vandg",
    )
    _PANEL_TOL = 1e-6

    def __init__(self, *args: Any, map_projection: Any = None, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        map_projection : ~mpl_toolkits.basemap.Basemap
            The map projection.
        *args, **kwargs
            Passed to `GeoAxes`.
        """
        # First assign projection and set axis bounds for locators
        # WARNING: Unlike cartopy projections basemaps cannot normally be reused.
        # To make syntax similar we make a copy.
        # WARNING: Investigated whether Basemap.__init__() could be called
        # twice with updated proj kwargs to modify map bounds after creation
        # and python immmediately crashes. Do not try again.
        import mpl_toolkits.basemap  # noqa: F401 verify package is available

        self.projection = copy.copy(map_projection)  # verify
        lon0 = self._get_lon0()
        if self.projection.projection in self._proj_polar:
            latmax = 80  # default latmax for gridlines
            extent = [-180 + lon0, 180 + lon0]
            bound = getattr(self.projection, "boundinglat", 0)
            north = self.projection.projection in self._proj_north
            extent.extend([bound, 90] if north else [-90, bound])
        else:
            latmax = 90
            attrs = ("lonmin", "lonmax", "latmin", "latmax")
            extent = [getattr(self.projection, attr, None) for attr in attrs]
            if any(_ is None for _ in extent):
                extent = [180 - lon0, 180 + lon0, -90, 90]  # fallback

        # Initialize axes
        self._map_boundary = None  # see format()
        self._has_recurred = False  # use this to override plotting methods
        self._lonlines_major = None  # store gridliner objects this way
        self._lonlines_minor = None
        self._latlines_major = None
        self._latlines_minor = None
        self._lonarray = 4 * [False]  # cached label toggles
        self._latarray = 4 * [False]  # cached label toggles
        self._lonaxis = _LonAxis(self)
        self._lataxis = _LatAxis(self, latmax=latmax)
        self._set_view_intervals(extent)
        super().__init__(*args, **kwargs)

        self._turnoff_tick_labels(self._lonlines_major)
        self._turnoff_tick_labels(self._latlines_major)

    def get_tightbbox(self, renderer: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Get tight bounding box, adjusting panel positions after aspect is applied.

        This ensures panels are properly aligned when saving figures, as apply_aspect()
        may be called during the rendering process.
        """
        # Apply aspect ratio, then ensure panels follow the aspect-constrained box.
        self._apply_aspect_and_adjust_panels(tol=self._PANEL_TOL)

        return super().get_tightbbox(renderer, *args, **kwargs)

    @override
    def draw(self, renderer: Any = None, *args: Any, **kwargs: Any) -> None:
        """
        Override draw to adjust panel positions for basemap axes.

        Basemap projections also rely on apply_aspect() and can shrink the main axes;
        panels must be repositioned to flank the visible map boundaries.
        """
        super().draw(renderer, *args, **kwargs)
        self._adjust_panel_positions(tol=self._PANEL_TOL)

    def _turnoff_tick_labels(self, locator: GridlineDict) -> None:
        """
        For GeoAxes with are dealing with a duality. Basemap axes behave differently than Cartopy axes and vice versa. UltraPlot abstracts away from these by providing GeoAxes. For basemap axes we need to turn off the tick labels as they will be handles by GeoAxis
        """
        for loc, objects in locator.items():
            for object in objects:
                # text is wrapped in a list
                if isinstance(object, list) and len(object) > 0:
                    object = object[0]
                if isinstance(object, mtext.Text):
                    object.set_visible(False)

    def _get_lon0(self) -> float:
        """
        Get the central longitude.
        """
        return getattr(self.projection, "projparams", {}).get("lon_0", 0)

    @staticmethod
    def _iter_gridlines(dict_: GridlineDict | None) -> Iterator[Any]:
        """
        Iterate over longitude latitude lines.
        """
        dict_ = dict_ or {}
        for pi in dict_.values():
            for pj in pi:
                for obj in pj:
                    yield obj

    def _build_gridliner_adapter(
        self, which: str = "major"
    ) -> Optional[_GridlinerAdapter]:
        lonlines = getattr(self, f"_lonlines_{which}", None)
        latlines = getattr(self, f"_latlines_{which}", None)
        if lonlines is None or latlines is None:
            return None
        return _BasemapGridlinerAdapter(lonlines, latlines)

    def _update_background(self, **kwargs: Any) -> None:
        """
        Update the map boundary patches. This is called in `Axes.format`.
        """
        # Non-rectangular projections
        # WARNING: Map boundary must be drawn before all other tasks. See __init__.
        # WARNING: With clipping on boundary lines are clipped by the axes bbox.
        if self.projection.projection in self._proj_non_rectangular:
            self.patch.set_facecolor("none")  # make sure main patch is hidden
            kw_face, kw_edge = rc._get_background_props(native=False, **kwargs)
            kw = {**kw_face, **kw_edge, "rasterized": False, "clip_on": False}
            self._map_boundary.update(kw)
        # Rectangular projections
        else:
            kw_face, kw_edge = rc._get_background_props(native=False, **kwargs)
            self.patch.update({**kw_face, "edgecolor": "none"})
            for spine in self.spines.values():
                spine.update(kw_edge)

    def _update_boundary(self, round: bool | None = None) -> None:
        """
        No-op. Boundary mode cannot be changed in basemap.
        """
        # NOTE: Unlike the cartopy method we do not look up the rc setting here.
        if round is None:
            return
        else:
            warnings._warn_ultraplot(
                f"Got round={round!r}, but you cannot change the bounds of a polar "
                "basemap projection after creating it. Please pass 'round' to uplt.Proj "  # noqa: E501
                "instead (e.g. using the uplt.subplots() dictionary keyword 'proj_kw')."
            )

    def _update_extent_mode(
        self, extent: str | None = None, boundinglat: float | None = None
    ) -> None:  # noqa: U100
        """
        No-op. Extent mode cannot be changed in basemap.
        """
        # NOTE: Unlike the cartopy method we do not look up the rc setting here.
        if extent is None:
            return
        if extent not in ("globe", "auto"):
            raise ValueError(
                f"Invalid extent mode {extent!r}. Must be 'auto' or 'globe'."
            )
        if extent == "auto":
            warnings._warn_ultraplot(
                f"Got extent={extent!r}, but you cannot use auto extent mode "
                "in basemap projections. Please consider switching to cartopy."
            )

    def _update_extent(
        self,
        lonlim: tuple[float | None, float | None] | None = None,
        latlim: tuple[float | None, float | None] | None = None,
        boundinglat: float | None = None,
    ) -> None:
        """
        No-op. Map bounds cannot be changed in basemap.
        """
        lonlim = _not_none(lonlim, (None, None))
        latlim = _not_none(latlim, (None, None))
        if boundinglat is not None or any(_ is not None for _ in (*lonlim, *latlim)):
            warnings._warn_ultraplot(
                f"Got lonlim={lonlim!r}, latlim={latlim!r}, boundinglat={boundinglat!r}"
                ', but you cannot "zoom into" a basemap projection after creating it. '
                "Please pass any of the following keyword arguments to uplt.Proj "
                "instead (e.g. using the uplt.subplots() dictionary keyword 'proj_kw'):"
                "'boundinglat', 'lonlim', 'latlim', 'llcrnrlon', 'llcrnrlat', "
                "'urcrnrlon', 'urcrnrlat', 'llcrnrx', 'llcrnry', 'urcrnrx', 'urcrnry', "
                "'width', or 'height'."
            )

    def _update_features(self) -> None:
        """
        Update geographic features.
        """
        # NOTE: Also notable are drawcounties, blumarble, drawlsmask,
        # shadedrelief, and etopo methods.
        for name, method in constructor.FEATURES_BASEMAP.items():
            # Draw feature or toggle on and off
            b = rc.find(name, context=True)
            attr = f"_{name}_feature"
            feat = getattr(self, attr, None)
            drawn = feat is not None  # if exists, apply *updated* settings
            if b is not None:
                if not b:
                    if drawn:  # toggle existing feature off
                        for obj in feat:
                            feat.set_visible(False)
                else:
                    if not drawn:
                        feat = getattr(self.projection, method)(ax=self)
                    if not isinstance(feat, (list, tuple)):  # list of artists?
                        feat = (feat,)
                    setattr(self, attr, feat)

            # Update settings
            if feat is not None:
                kw = rc.category(name, context=drawn)
                for obj in feat:
                    obj.update(kw)

    def _update_gridlines(
        self,
        which: str = "major",
        longrid: bool | None = None,
        latgrid: bool | None = None,
        lonarray: Sequence[bool | None] | None = None,
        latarray: Sequence[bool | None] | None = None,
        lonlabelrotation: float | None = None,
        latlabelrotation: float | None = None,
    ) -> None:
        """
        Apply changes to the basemap axes.
        """
        latmax = self._lataxis.get_latmax()
        for axis, name, grid, array, method, rotation in zip(
            ("x", "y"),
            ("lon", "lat"),
            (longrid, latgrid),
            (lonarray, latarray),
            ("drawmeridians", "drawparallels"),
            (lonlabelrotation, latlabelrotation),
        ):
            # Correct lonarray and latarray label toggles by changing from lrbt to lrtb.
            # Then update the cahced toggle array. This lets us change gridline locs
            # while preserving the label toggle setting from a previous format() call.
            grid = rc._get_gridline_bool(grid, axis=axis, which=which, native=False)
            axis = getattr(self, f"_{name}axis")
            if len(array) == 5:  # should be always
                array = array[:4]
            bools = 4 * [False] if which == "major" else getattr(self, f"_{name}array")
            array = [*array[:2], *array[2:4][::-1]]  # flip lrbt to lrtb and skip geo
            for i, b in enumerate(array):
                if b is not None:
                    bools[i] = b  # update toggles

            # Get gridlines
            # NOTE: This may re-apply existing gridlines.
            lines = list(getattr(self, f"_get_{name}ticklocs")(which=which))
            if name == "lon" and np.isclose(lines[0] + 360, lines[-1]):
                lines = lines[:-1]  # prevent double labels
            # Figure out whether we have to redraw meridians/parallels
            # NOTE: Always update minor gridlines if major locator also changed
            attr = f"_{name}lines_{which}"
            objs = getattr(self, attr)  # dictionary of previous objects
            attrs = ["isDefault_majloc"]  # always check this one
            attrs.append("isDefault_majfmt" if which == "major" else "isDefault_minloc")
            rebuild = lines and (
                not objs
                or any(_ is not None for _ in array)  # user-input or initial toggles
                or any(not getattr(axis, attr) for attr in attrs)  # none tracked yet
            )
            if rebuild and objs and grid is None:  # get *previous* toggle state
                grid = all(obj.get_visible() for obj in self._iter_gridlines(objs))

            # Draw or redraw meridian or parallel lines
            # Also mark formatters and locators as 'default'
            if rebuild:
                kwdraw = {}
                formatter = axis.get_major_formatter()
                if formatter is not None:  # use functional formatter
                    kwdraw["fmt"] = formatter
                for obj in self._iter_gridlines(objs):
                    obj.set_visible(False)
                objs = getattr(self.projection, method)(
                    lines, ax=self, latmax=latmax, labels=bools, **kwdraw
                )
                setattr(self, attr, objs)

            # Update gridline settings
            # We use native matplotlib 'grid' rc param for geographic gridlines
            kwlines = rc._get_gridline_props(which=which, native=False, rebuild=rebuild)
            kwtext = rc._get_ticklabel_props(native=False, rebuild=rebuild)
            for obj in self._iter_gridlines(objs):
                if isinstance(obj, mtext.Text):
                    obj.update(kwtext)
                    # Apply rotation if specified
                    if rotation is not None:
                        obj.set_rotation(rotation)
                else:
                    obj.update(kwlines)

            # Toggle existing gridlines on and off
            if grid is not None:
                for obj in self._iter_gridlines(objs):
                    if not isinstance(obj, mtext.Text):
                        obj.set_visible(grid)

    def _update_major_gridlines(
        self,
        longrid: bool | None = None,
        latgrid: bool | None = None,
        lonarray: Sequence[bool | None] | None = None,
        latarray: Sequence[bool | None] | None = None,
        loninline: bool | None = None,
        latinline: bool | None = None,
        rotatelabels: bool | None = None,
        lonlabelrotation: float | None = None,
        latlabelrotation: float | None = None,
        labelpad: Any = None,
        nsteps: int | None = None,
    ) -> None:
        """
        Update major gridlines.
        """
        loninline, latinline, labelpad, rotatelabels, nsteps  # avoid U100 error
        self._update_gridlines(
            which="major",
            longrid=longrid,
            latgrid=latgrid,
            lonarray=lonarray,
            latarray=latarray,
            lonlabelrotation=lonlabelrotation,
            latlabelrotation=latlabelrotation,
        )
        sides = _gridliner_sides_from_arrays(
            lonarray,
            latarray,
            order=_BASEMAP_LABEL_SIDES,
            allow_xy=False,
            include_false=False,
        )
        if sides:
            self._toggle_gridliner_labels(**sides)
        self._set_gridliner_adapter("major", self._build_gridliner_adapter("major"))

    def _update_minor_gridlines(
        self,
        longrid: bool | None = None,
        latgrid: bool | None = None,
        nsteps: int | None = None,
    ) -> None:
        """
        Update minor gridlines.
        """
        # Update gridline locations
        nsteps  # avoid U100 error
        array = [None] * 4  # NOTE: must be None not False (see _update_gridlines)
        self._update_gridlines(
            which="minor",
            longrid=longrid,
            latgrid=latgrid,
            lonarray=array,
            latarray=array,
            lonlabelrotation=None,
            latlabelrotation=None,
        )
        self._set_gridliner_adapter("minor", self._build_gridliner_adapter("minor"))
        # Set isDefault_majloc, etc. to True for both axes
        # NOTE: This cannot be done inside _update_gridlines or minor gridlines
        # will not update to reflect new major gridline locations.
        for axis in (self._lonaxis, self._lataxis):
            axis.isDefault_majfmt = True
            axis.isDefault_majloc = True
            axis.isDefault_minloc = True


# Apply signature obfuscation after storing previous signature
GeoAxes._format_signatures[GeoAxes] = inspect.signature(GeoAxes.format)
GeoAxes.format = docstring._obfuscate_kwargs(GeoAxes.format)


def _is_rectilinear_projection(ax: Any) -> bool:
    """Check if the axis has a flat projection (works with Cartopy)."""
    # Determine what the projection function is
    # Create a square and determine if the lengths are preserved
    # For geoaxes projc is always set in format, and thus is not None
    proj = getattr(ax, "projection", None)
    transform = None
    if hasattr(proj, "transform_point"):  # cartopy
        if proj.transform_point is not None:
            transform = partial(proj.transform_point, src_crs=proj.as_geodetic())
    elif hasattr(proj, "projection"):  # basemap
        transform = proj

    if transform is not None:
        # Create three collinear points (in a straight line)
        line_points = [(0, 0), (10, 10), (20, 20)]

        # Transform the points using the projection
        transformed_points = [transform(x, y) for x, y in line_points]

        # Check if the transformed points are still collinear
        # Points are collinear if the slopes between consecutive points are equal
        x0, y0 = transformed_points[0]
        x1, y1 = transformed_points[1]
        x2, y2 = transformed_points[2]

        # Calculate slopes
        xdiff1 = x1 - x0
        xdiff2 = x2 - x1
        if np.allclose(xdiff1, 0) or np.allclose(xdiff2, 0):  # Avoid division by zero
            # Check if both are vertical lines
            return np.allclose(xdiff1, 0) and np.allclose(xdiff2, 0)

        slope1 = (y1 - y0) / xdiff1
        slope2 = (y2 - y1) / xdiff2

        # If slopes are equal (within a small tolerance), the projection preserves straight lines
        return np.allclose(slope1 - slope2, 0)
    # Cylindrical projections are generally rectilinear
    rectilinear_projections = {
        # Cartopy projections
        "platecarree",
        "mercator",
        "lambertcylindrical",
        "miller",
        # Basemap projections
        "cyl",
        "merc",
        "mill",
        "rect",
        "rectilinear",
        "unknown",
    }

    # For Cartopy
    if hasattr(proj, "name"):
        return proj.name.lower() in rectilinear_projections
    # For Basemap
    elif hasattr(proj, "projection"):
        return proj.projection.lower() in rectilinear_projections
    # If we can't determine, assume it's not rectilinear
    return False
