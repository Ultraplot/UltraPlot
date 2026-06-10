#!/usr/bin/env python3
"""
Polar axes using azimuth and radius instead of *x* and *y*.
"""

import inspect

try:
    from typing import override
except:
    from typing_extensions import override

import matplotlib.projections.polar as mpolar
import matplotlib.transforms as mtransforms
import numpy as np
from matplotlib.font_manager import FontProperties

from .. import constructor
from .. import ticker as pticker
from ..config import rc
from ..internals import ic  # noqa: F401
from ..internals import _not_none, _pop_rc, docstring
from . import plot, shared

__all__ = ["PolarAxes"]

# CurvedText sampling resolution along the label arc / spoke.
_POLAR_LABEL_NPOINTS = 50
# Half-span (degrees) used when the label sits on a closed (full) circle.
_POLAR_LABEL_FULL_HALFSPAN_DEG = 15.0
# Fraction of an open sector occupied by `thetalabel`; remainder is endpoint margin.
_POLAR_LABEL_SECTOR_FRAC = 0.8


# Format docstring
_format_docstring = """
r0 : float, default: 0
    The radial origin.
theta0 : {'N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NE'}, optional
    The zero azimuth location.
thetadir : {1, -1, 'anticlockwise', 'counterclockwise', 'clockwise'}, optional
    The positive azimuth direction. Clockwise corresponds to
    ``-1`` and anticlockwise corresponds to ``1``.
thetamin, thetamax : float, optional
    The lower and upper azimuthal bounds in degrees. If
    ``thetamax != thetamin + 360``, this produces a sector plot.
thetalim : 2-tuple of float or None, optional
    Specifies `thetamin` and `thetamax` at once.
rmin, rmax : float, optional
    The inner and outer radial limits. If ``r0 != rmin``, this
    produces an annular plot.
rlim : 2-tuple of float or None, optional
    Specifies `rmin` and `rmax` at once.
rborder : bool, optional
    Whether to draw the polar axes border. Visibility of the "inner"
    radial spine and "start" and "end" azimuthal spines is controlled
    automatically by matplotlib.
thetagrid, rgrid, grid : bool, optional
    Whether to draw major gridlines for the azimuthal and radial axis.
    Use the keyword `grid` to toggle both.
thetagridminor, rgridminor, gridminor : bool, optional
    Whether to draw minor gridlines for the azimuthal and radial axis.
    Use the keyword `gridminor` to toggle both.
thetagridcolor, rgridcolor, gridcolor : color-spec, optional
    Color for the major and minor azimuthal and radial gridlines.
    Use the keyword `gridcolor` to set both at once.
thetalocator, rlocator : locator-spec, optional
    Used to determine the azimuthal and radial gridline positions.
    Passed to the `~ultraplot.constructor.Locator` constructor. Can be
    float, list of float, string, or `matplotlib.ticker.Locator` instance.
thetalines, rlines
    Aliases for `thetalocator`, `rlocator`.
thetalocator_kw, rlocator_kw : dict-like, optional
    The azimuthal and radial locator settings. Passed to
    `~ultraplot.constructor.Locator`.
thetaminorlocator, rminorlocator : optional
    As for `thetalocator`, `rlocator`, but for the minor gridlines.
thetaminorticks, rminorticks : optional
    Aliases for `thetaminorlocator`, `rminorlocator`.
thetaminorlocator_kw, rminorlocator_kw
    As for `thetalocator_kw`, `rlocator_kw`, but for the minor locator.
rlabelpos : float, optional
    The azimuth at which radial coordinates are labeled. Also used as the
    spoke angle for ``rlabel`` when you want an explicit radial-label
    position.
thetaformatter, rformatter : formatter-spec, optional
    Used to determine the azimuthal and radial label format.
    Passed to the `~ultraplot.constructor.Formatter` constructor.
    Can be string, list of string, or `matplotlib.ticker.Formatter`
    instance. Use ``[]``, ``'null'``, or ``'none'`` for no labels.
thetalabels, rlabels : optional
    Aliases for `thetaformatter`, `rformatter`.
thetaformatter_kw, rformatter_kw : dict-like, optional
    The azimuthal and radial label formatter settings. Passed to
    `~ultraplot.constructor.Formatter`.
xlabel, ylabel : str, optional
    The x and y axis labels. Applied with `~matplotlib.axes.Axes.set_xlabel`
    and `~matplotlib.axes.Axes.set_ylabel`.
xlabel_kw, ylabel_kw : dict-like, optional
    Additional axis label settings applied with `~matplotlib.axes.Axes.set_xlabel`
    and `~matplotlib.axes.Axes.set_ylabel`. See also `labelpad`, `labelcolor`,
    `labelsize`, and `labelweight`.
thetalabel, rlabel : str, optional
    Polar-aware axis labels rendered via `~ultraplot.text.CurvedText`.
    ``thetalabel`` follows the outer arc just beyond ``r=rmax``.
    ``rlabel`` follows a radial spoke, centered between ``rmin`` and
    ``rmax``. On a full circle it uses ``get_rlabel_position()`` unless
    ``rlabelpos`` is explicit; on a sector it uses the spoke selected by
    ``rlabelloc`` unless ``rlabelpos`` is explicit. Both labels include a
    built-in tick-clearance offset, and ``labelpad`` adds extra padding in
    points on top of that offset. Pass ``""`` to clear a previously set
    label.
thetalabelloc : float, optional
    Center theta angle (in degrees) for ``thetalabel``. Defaults to the
    midpoint of the directed ``thetalim`` interval (or ``0`` for a full
    circle).
rlabelloc : {'right', 'left'}, default: 'right'
    Where to place ``rlabel``. When the spoke angle is fixed by a full
    circle or by explicit ``rlabelpos``, ``rlabelloc`` selects the
    perpendicular side of that spoke and ``'left'`` flips the default
    side. On a sector with no explicit ``rlabelpos``, ``'right'``
    (default) anchors to ``thetamin`` and ``'left'`` anchors to
    ``thetamax``; the label is then offset outward from the sector.
thetalabel_kw, rlabel_kw : dict-like, optional
    Additional `~ultraplot.text.CurvedText` settings for the polar-aware
    labels (e.g. ``border``, ``bbox``, or rendering hints like
    ``min_advance``). See also `labelpad`, `labelcolor`, `labelsize`,
    and `labelweight`.
color : color-spec, default: :rc:`meta.color`
    Color for the axes edge. Propagates to `labelcolor` unless specified
    otherwise (similar to :func:`~ultraplot.axes.CartesianAxes.format`).
labelcolor, gridlabelcolor : color-spec, default: `color` or :rc:`grid.labelcolor`
    Color for the gridline labels.
labelpad, gridlabelpad : unit-spec, default: :rc:`grid.labelpad`
    The padding between the axes edge and the radial and azimuthal labels.
    For ``thetalabel`` and ``rlabel``, this is added on top of the built-in
    tick-clearance offset.
    %(units.pt)s
labelsize, gridlabelsize : unit-spec or str, default: :rc:`grid.labelsize`
    Font size for the gridline labels.
    %(units.pt)s
labelweight, gridlabelweight : str, default: :rc:`grid.labelweight`
    Font weight for the gridline labels.
"""
docstring._snippet_manager["polar.format"] = _format_docstring


class PolarAxes(shared._SharedAxes, plot.PlotAxes, mpolar.PolarAxes):
    """
    Axes subclass for plotting in polar coordinates. Adds the `~PolarAxes.format`
    method and overrides several existing methods.

    Important
    ---------
    This axes subclass can be used by passing ``proj='polar'``
    to axes-creation commands like `~ultraplot.figure.Figure.add_axes`,
    `~ultraplot.figure.Figure.add_subplot`, and `~ultraplot.figure.Figure.subplots`.
    """

    _name = "polar"

    @docstring._snippet_manager
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args
            Passed to `matplotlib.axes.Axes`.
        %(polar.format)s

        Other parameters
        ----------------
        %(axes.format)s
        %(rc.init)s

        See also
        --------
        PolarAxes.format
        ultraplot.axes.Axes
        ultraplot.axes.PlotAxes
        matplotlib.projections.PolarAxes
        ultraplot.figure.Figure.subplot
        ultraplot.figure.Figure.add_subplot
        """
        # Set tick length to zero so azimuthal labels are not too offset
        # Change default radial axis formatter but keep default theta one
        super().__init__(*args, **kwargs)
        self.yaxis.set_major_formatter(pticker.AutoFormatter())
        self.yaxis.isDefault_majfmt = True
        for axis in (self.xaxis, self.yaxis):
            axis.set_tick_params(which="both", size=0)
        self._thetalabel_artist = None
        self._rlabel_artist = None

    @override
    def _apply_axis_sharing(self):
        # Not implemented. Silently pass
        return

    def _update_formatter(self, x, *, formatter=None, formatter_kw=None):
        """
        Update the gridline label formatter.
        """
        # Tick formatter and toggling
        axis = getattr(self, x + "axis")
        formatter_kw = formatter_kw or {}
        if formatter is not None:
            formatter = constructor.Formatter(formatter, **formatter_kw)  # noqa: E501
            axis.set_major_formatter(formatter)

    def _update_limits(self, x, *, min_=None, max_=None, lim=None):
        """
        Update the limits.
        """
        # Try to use public API where possible
        r = "theta" if x == "x" else "r"
        min_, max_ = self._min_max_lim(r, min_, max_, lim)
        if min_ is not None:
            getattr(self, f"set_{r}min")(min_)
        if max_ is not None:
            getattr(self, f"set_{r}max")(max_)

    def _update_locators(
        self,
        x,
        *,
        locator=None,
        locator_kw=None,
        minorlocator=None,
        minorlocator_kw=None,
    ):
        """
        Update the gridline locator.
        """
        # TODO: Add minor tick 'toggling' as with cartesian axes?
        # NOTE: Must convert theta locator input to radians, then back to deg.
        r = "theta" if x == "x" else "r"
        axis = getattr(self, x + "axis")
        min_ = getattr(self, f"get_{r}min")()
        max_ = getattr(self, f"get_{r}max")()
        for i, (loc, loc_kw) in enumerate(
            zip((locator, minorlocator), (locator_kw, minorlocator_kw))
        ):
            if loc is None:
                continue
            # Get locator
            loc_kw = loc_kw or {}
            loc = constructor.Locator(loc, **loc_kw)
            # Sanitize values
            array = loc.tick_values(min_, max_)
            array = array[(array >= min_) & (array <= max_)]
            if x == "x":
                array = np.deg2rad(array)
                if np.isclose(array[-1], min_ + 2 * np.pi):  # exclusive if 360 deg
                    array = array[:-1]
            # Assign fixed location
            loc = constructor.Locator(array)  # convert to FixedLocator
            if i == 0:
                axis.set_major_locator(loc)
            else:
                axis.set_minor_locator(loc)

    def _update_labels(self, x, *args, **kwargs):
        """
        Apply axis labels via `set_xlabel` / `set_ylabel`.
        """
        # NOTE: Critical to test whether arguments are None or else this
        # will set isDefault_label to False every time format() is called.
        kwargs = rc._get_label_props(**kwargs)
        no_args = all(a is None for a in args)
        no_kwargs = all(v is None for v in kwargs.values())
        if no_args and no_kwargs:
            return
        setter = getattr(self, f"set_{x}label")
        getter = getattr(self, f"get_{x}label")
        if no_args:  # otherwise label text is reset!
            args = (getter(),)
        setter(*args, **kwargs)

    def _get_directed_thetalim(self):
        """Return the directed theta interval in degrees from the raw x-limits."""
        thetamin, thetamax = np.rad2deg(self.get_xlim())
        return float(thetamin), float(thetamax)

    @staticmethod
    def _is_full_circle_thetalim(thetamin, thetamax):
        """Return whether the directed theta interval spans a full circle."""
        return np.isclose((thetamax - thetamin) % 360.0, 0.0)

    def _polar_tick_clearance_in(self, axis):
        """Tick mark + tick pad + ~font height(s), in inches."""
        axis_obj = getattr(self, f"{axis}axis")
        size_pt = rc[f"{axis}tick.major.size"]
        pad_pt = rc[f"{axis}tick.major.pad"]
        label_pt = FontProperties(size=rc[f"{axis}tick.labelsize"]).get_size_in_points()
        ticks = axis_obj.get_major_ticks()
        if ticks:
            tick = ticks[0]
            size_pt = max(
                tick.tick1line.get_markersize(), tick.tick2line.get_markersize()
            )
            pad_pt = (
                tick.get_pad()
                if hasattr(tick, "get_pad")
                else getattr(tick, "_pad", pad_pt)
            )
            label_pt = max(tick.label1.get_size(), tick.label2.get_size(), label_pt)
        labels = axis_obj.get_ticklabels()
        if labels:
            label_pt = max(float(label.get_size()) for label in labels)
        n = 2 if axis == "x" else 1.5
        return (size_pt + pad_pt + n * label_pt) / 72.0

    def _build_thetalabel_curve(self, loc, total_pad_in):
        """
        Curve along the outer arc at r = rmax + delta_r (data coords). The
        radial offset is computed in data space so clearance is angle-
        independent — figure-space ScaledTranslation undershoots when the
        outward direction points toward a tight bbox edge (e.g. 180–230°).
        """
        thetamin, thetamax = self._get_directed_thetalim()
        span = (thetamax - thetamin) % 360.0
        is_full_circle = self._is_full_circle_thetalim(thetamin, thetamax)
        if is_full_circle:
            mid = 0.0 if loc is None else float(loc)
            half_span = _POLAR_LABEL_FULL_HALFSPAN_DEG
        elif loc is None:
            mid = thetamin + 0.5 * span
            half_span = 0.5 * span * _POLAR_LABEL_SECTOR_FRAC
        else:
            # Explicit thetalabelloc on a sector: localize the label around
            # the requested angle instead of spanning the whole sector arc.
            mid = float(loc)
            half_span = _POLAR_LABEL_FULL_HALFSPAN_DEG
        x = np.deg2rad(
            np.linspace(mid - half_span, mid + half_span, _POLAR_LABEL_NPOINTS)
        )
        rmax_val = self.get_rmax()
        p0 = self.transData.transform(np.array([0.0, rmax_val]))
        p1 = self.transData.transform(np.array([0.0, rmax_val + 1.0]))
        px_per_r = float(np.linalg.norm(np.asarray(p1) - np.asarray(p0)))
        delta_r = total_pad_in * self.figure.dpi / px_per_r if px_per_r > 1e-6 else 0.0
        y = np.full_like(x, rmax_val + delta_r)
        return x, y, self.transData

    def _get_sector_rlabel_outside_sign(self, rpos):
        """Return the sign that offsets a sector rlabel outside the wedge."""
        thetamin, thetamax = self._get_directed_thetalim()
        span = (thetamax - thetamin) % 360.0
        inside_step = min(1.0, 0.25 * span)
        inside_theta = (
            rpos - inside_step
            if np.isclose((rpos - thetamax) % 360.0, 0.0)
            else rpos + inside_step
        )
        rmid = 0.5 * (self.get_rmin() + self.get_rmax())
        edge = self.transData.transform(np.array([np.deg2rad(rpos), rmid]))
        inside = self.transData.transform(np.array([np.deg2rad(inside_theta), rmid]))
        normal = self._get_rlabel_right_normal(np.deg2rad(rpos))
        return (
            -1.0 if np.dot(np.asarray(inside) - np.asarray(edge), normal) > 0.0 else 1.0
        )

    def _resolve_rlabel_geometry(self, loc, rlabelpos):
        """
        Resolve ``(rpos, sign)`` for the radial label given ``rlabelloc`` and
        an optional explicit ``rlabelpos``. On a full circle, ``loc`` flips
        the perpendicular offset; on a sector with no explicit ``rlabelpos``,
        ``loc`` instead selects the spoke (``thetamin`` vs ``thetamax``) and
        the perpendicular sign is auto-chosen to fall outside the wedge.
        """
        if loc not in (None, "left", "right"):
            raise ValueError(f"rlabelloc must be 'right' or 'left'; got {loc!r}")
        thetamin, thetamax = self._get_directed_thetalim()
        is_full_circle = self._is_full_circle_thetalim(thetamin, thetamax)
        if rlabelpos is not None:
            rpos = float(rlabelpos)
            if is_full_circle:
                base_sign = 1.0
            else:
                base_sign = -1.0 if np.isclose((rpos - thetamax) % 360.0, 0.0) else 1.0
        elif is_full_circle:
            rpos = self.get_rlabel_position()
            base_sign = 1.0
        else:
            rpos = thetamax if loc == "left" else thetamin
            base_sign = self._get_sector_rlabel_outside_sign(rpos)
        flip = loc == "left" and (is_full_circle or rlabelpos is not None)
        sign = -base_sign if flip else base_sign
        return rpos, sign

    def _get_rlabel_right_normal(self, rad):
        """Return the display-space right normal for the radial spoke at ``rad``."""
        rmin, rmax = self.get_rmin(), self.get_rmax()
        p0 = self.transData.transform(np.array([rad, rmin]))
        p1 = self.transData.transform(np.array([rad, rmax]))
        tangent = np.asarray(p1, dtype=float) - np.asarray(p0, dtype=float)
        norm = np.linalg.norm(tangent)
        if norm <= 1e-6:
            return np.array([np.sin(rad), -np.cos(rad)])
        tangent /= norm
        return np.array([tangent[1], -tangent[0]])

    def _build_rlabel_curve(self, loc, pad_in, rlabelpos):
        """
        Curve along the radial spoke from rmin to rmax with a perpendicular
        ScaledTranslation offset so the label clears the r-tick labels.
        """
        rpos, sign = self._resolve_rlabel_geometry(loc, rlabelpos)
        rad = np.deg2rad(rpos)
        x = np.full(_POLAR_LABEL_NPOINTS, rad)
        y = np.linspace(self.get_rmin(), self.get_rmax(), _POLAR_LABEL_NPOINTS)
        normal = self._get_rlabel_right_normal(rad)
        tick_clearance_in = self._polar_tick_clearance_in("y")
        total_pad_in = pad_in + tick_clearance_in
        dx_in, dy_in = sign * total_pad_in * normal
        transform = self.transData + mtransforms.ScaledTranslation(
            dx_in, dy_in, self.figure.dpi_scale_trans
        )
        return x, y, transform

    def _refresh_polar_label_geometry(self, kind):
        """Refresh the stored curve and transform for an existing polar label."""
        attr = f"_{kind}label_artist"
        artist = getattr(self, attr, None)
        if artist is None:
            return
        state = getattr(self, f"_{kind}label_state", None) or {}
        loc = state.get("loc")
        labelpad = state.get("labelpad")
        pad_in = _not_none(labelpad, rc["grid.labelpad"]) / 72.0
        axis = "x" if kind == "theta" else "y"
        total_pad_in = pad_in + self._polar_tick_clearance_in(axis)
        if kind == "theta":
            x, y, transform = self._build_thetalabel_curve(loc, total_pad_in)
        else:
            x, y, transform = self._build_rlabel_curve(
                loc, pad_in, state.get("rlabelpos")
            )
        artist.set_curve(x, y)
        artist.set_transform(transform)

    def _update_polar_label(
        self, kind, text, *, loc=None, labelpad=None, rlabelpos=None, **kwargs
    ):
        """
        Apply a polar-aware axis label along the outer arc (`thetalabel`) or
        along the radial spoke (`rlabel`), both via CurvedText.
        """
        # NOTE: Critical to test whether arguments are None or else we'd
        # overwrite styling and clear text on every format() call.
        kwargs = rc._get_label_props(**kwargs)
        kwargs.pop("labelpad", None)  # injected by _get_label_props; not a Text prop
        attr = f"_{kind}label_artist"
        artist = getattr(self, attr, None)
        # Sticky state: previously-applied loc/labelpad/rlabelpos so a generic
        # format() call (e.g. ``axs.format(suptitle=...)``) doesn't reset them
        # back to the default when the user didn't pass them again.
        state_attr = f"_{kind}label_state"
        state = getattr(self, state_attr, None) or {}
        nothing_to_do = (
            text is None
            and loc is None
            and labelpad is None
            and rlabelpos is None
            and all(v is None for v in kwargs.values())
        )
        if artist is None and nothing_to_do:
            return

        if loc is not None:
            state["loc"] = loc
        if labelpad is not None:
            state["labelpad"] = labelpad
        if kind == "r" and rlabelpos is not None:
            state["rlabelpos"] = rlabelpos
        setattr(self, state_attr, state)
        loc = state.get("loc")
        labelpad = state.get("labelpad")
        rlabelpos = state.get("rlabelpos") if kind == "r" else None

        pad_in = _not_none(labelpad, rc["grid.labelpad"]) / 72.0
        style_props = {k: v for k, v in kwargs.items() if v is not None}
        if kind == "theta":
            total_pad_in = pad_in + self._polar_tick_clearance_in("x")
            x, y, transform = self._build_thetalabel_curve(loc, total_pad_in)
        else:
            x, y, transform = self._build_rlabel_curve(loc, pad_in, rlabelpos)

        if artist is None:
            artist = self.text(
                x,
                y,
                text or "",
                transform=transform,
                ha="center",
                va="center",
                clip_on=False,
                **style_props,
            )
            setattr(self, attr, artist)
            return
        artist.set_curve(x, y)
        artist.set_transform(transform)
        if text is not None:
            artist.set_text(text)
        if style_props:
            artist._apply_label_props(style_props)

    @override
    def draw(self, renderer=None, *args, **kwargs):
        self._refresh_polar_label_geometry("theta")
        self._refresh_polar_label_geometry("r")
        super().draw(renderer, *args, **kwargs)

    @override
    def get_tightbbox(self, renderer, *args, **kwargs):
        self._refresh_polar_label_geometry("theta")
        self._refresh_polar_label_geometry("r")
        return super().get_tightbbox(renderer, *args, **kwargs)

    @docstring._snippet_manager
    def format(
        self,
        *,
        r0=None,
        theta0=None,
        thetadir=None,
        thetamin=None,
        thetamax=None,
        thetalim=None,
        rmin=None,
        rmax=None,
        rlim=None,
        thetagrid=None,
        rgrid=None,
        thetagridminor=None,
        rgridminor=None,
        thetagridcolor=None,
        rgridcolor=None,
        rlabelpos=None,
        rscale=None,
        rborder=None,
        thetalocator=None,
        rlocator=None,
        thetalines=None,
        rlines=None,
        thetalocator_kw=None,
        rlocator_kw=None,
        thetaminorlocator=None,
        rminorlocator=None,
        thetaminorlines=None,
        rminorlines=None,  # noqa: E501
        thetaminorlocator_kw=None,
        rminorlocator_kw=None,
        thetaformatter=None,
        rformatter=None,
        thetalabels=None,
        rlabels=None,
        thetaformatter_kw=None,
        rformatter_kw=None,
        labelpad=None,
        labelsize=None,
        labelcolor=None,
        labelweight=None,
        xlabel=None,
        ylabel=None,
        xlabel_kw=None,
        ylabel_kw=None,
        thetalabel=None,
        rlabel=None,
        thetalabelloc=None,
        rlabelloc=None,
        thetalabel_kw=None,
        rlabel_kw=None,
        **kwargs,
    ):
        """
        Modify axes limits, radial and azimuthal gridlines, and more. Note that
        all of the ``theta`` arguments are specified in degrees, not radians.

        Parameters
        ----------
        %(polar.format)s

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
        # NOTE: Here we capture 'label.pad' rc argument normally used for
        # x and y axis labels as shorthand for 'tick.labelpad'.
        rc_kw, rc_mode = _pop_rc(kwargs)
        labelcolor = _not_none(labelcolor, kwargs.get("color", None))
        with rc.context(rc_kw, mode=rc_mode):
            edgecolor = _not_none(
                kwargs.get("color", None),
                rc.find("axes.edgecolor", context=True),
                rc["axes.edgecolor"],
            )
            linewidth = _not_none(
                kwargs.get("linewidth", None),
                rc.find("axes.linewidth", context=True),
                rc["axes.linewidth"],
            )
            tickcolor = _not_none(
                kwargs.get("tickcolor", None),
                kwargs.get("color", None),
                rc.find("xtick.color", context=True),
                rc["xtick.color"],
            )
            tickwidth = _not_none(
                kwargs.get("tickwidth", None),
                kwargs.get("linewidth", None) and linewidth,
                rc.find("tick.width", context=True),
                rc["tick.width"],
            )
            tickwidthratio = _not_none(
                kwargs.get("tickwidthratio", None),
                rc.find("tick.widthratio", context=True),
                rc["tick.widthratio"],
            )

            # Not mutable default args
            thetalocator_kw = thetalocator_kw or {}
            thetaminorlocator_kw = thetaminorlocator_kw or {}
            thetaformatter_kw = thetaformatter_kw or {}
            rlocator_kw = rlocator_kw or {}
            rminorlocator_kw = rminorlocator_kw or {}
            rformatter_kw = rformatter_kw or {}

            # Flexible input
            thetalocator = _not_none(thetalines=thetalines, thetalocator=thetalocator)
            thetaformatter = _not_none(
                thetalabels=thetalabels, thetaformatter=thetaformatter
            )  # noqa: E501
            thetaminorlocator = _not_none(
                thetaminorlines=thetaminorlines, thetaminorlocator=thetaminorlocator
            )  # noqa: E501
            rlocator = _not_none(rlines=rlines, rlocator=rlocator)
            rformatter = _not_none(rlabels=rlabels, rformatter=rformatter)
            rminorlocator = _not_none(
                rminorlines=rminorlines, rminorlocator=rminorlocator
            )  # noqa: E501

            # Special radius settings
            if r0 is not None:
                self.set_rorigin(r0)
            if rlabelpos is not None:
                self.set_rlabel_position(rlabelpos)
            if rscale is not None:
                self.set_rscale(rscale)
            if rborder is not None:
                self.spines["polar"].set_visible(bool(rborder))

            # Special azimuth settings
            if theta0 is not None:
                self.set_theta_zero_location(theta0)
            if thetadir is not None:
                self.set_theta_direction(thetadir)

            # Polar frame styling used to come from the shared background helper.
            # Apply it explicitly now that patch and frame styling are separated.
            self._update_frame(
                "x",
                edgecolor=edgecolor,
                linewidth=linewidth,
                tickcolor=tickcolor,
                tickwidth=tickwidth,
                tickwidthratio=tickwidthratio,
            )
            self._update_frame(
                "y",
                tickcolor=tickcolor,
                tickwidth=tickwidth,
                tickwidthratio=tickwidthratio,
            )

            # Loop over axes
            for (
                x,
                min_,
                max_,
                lim,
                grid,
                gridminor,
                gridcolor,
                locator,
                locator_kw,
                formatter,
                formatter_kw,
                minorlocator,
                minorlocator_kw,
                label,
                label_kw,
            ) in zip(
                ("x", "y"),
                (thetamin, rmin),
                (thetamax, rmax),
                (thetalim, rlim),
                (thetagrid, rgrid),
                (thetagridminor, rgridminor),
                (thetagridcolor, rgridcolor),
                (thetalocator, rlocator),
                (thetalocator_kw, rlocator_kw),
                (thetaformatter, rformatter),
                (thetaformatter_kw, rformatter_kw),
                (thetaminorlocator, rminorlocator),
                (thetaminorlocator_kw, rminorlocator_kw),
                (xlabel, ylabel),
                (xlabel_kw, ylabel_kw),
            ):
                # Axis limits
                self._update_limits(x, min_=min_, max_=max_, lim=lim)

                # Axis tick settings
                # NOTE: Here use 'grid.labelpad' instead of 'tick.labelpad'. Default
                # offset for grid labels is larger than for tick labels.
                self._update_ticks(
                    x,
                    grid=grid,
                    gridminor=gridminor,
                    gridcolor=gridcolor,
                    gridpad=True,
                    labelpad=labelpad,
                    labelcolor=labelcolor,
                    labelsize=labelsize,
                    labelweight=labelweight,
                )

                # Axis locator
                self._update_locators(
                    x,
                    locator=locator,
                    locator_kw=locator_kw,
                    minorlocator=minorlocator,
                    minorlocator_kw=minorlocator_kw,
                )

                # Axis formatter
                self._update_formatter(
                    x, formatter=formatter, formatter_kw=formatter_kw
                )

                # Axis label
                kw = dict(
                    labelpad=labelpad,
                    color=labelcolor,
                    size=labelsize,
                    weight=labelweight,
                )
                kw.update(label_kw or {})
                self._update_labels(x, label, **kw)

            # Polar-aware axis labels (rendered along the arc / radial spoke)
            for kind, text, loc, label_kw in (
                ("theta", thetalabel, thetalabelloc, thetalabel_kw),
                ("r", rlabel, rlabelloc, rlabel_kw),
            ):
                kw = dict(
                    loc=loc,
                    labelpad=labelpad,
                    color=labelcolor,
                    size=labelsize,
                    weight=labelweight,
                )
                if kind == "r":
                    kw["rlabelpos"] = rlabelpos
                kw.update(label_kw or {})
                self._update_polar_label(kind, text, **kw)

        # Parent format method
        super().format(rc_kw=rc_kw, rc_mode=rc_mode, **kwargs)


# Apply signature obfuscation after storing previous signature
# NOTE: This is needed for __init__
PolarAxes._format_signatures[PolarAxes] = inspect.signature(PolarAxes.format)
PolarAxes.format = docstring._obfuscate_kwargs(PolarAxes.format)
