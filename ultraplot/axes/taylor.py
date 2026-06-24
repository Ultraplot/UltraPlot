#!/usr/bin/env python3
"""
Taylor diagram axes.
"""

import inspect

import matplotlib.projections.polar as mpolar
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
import numpy as np

from ..config import rc
from ..internals import _not_none, _pop_rc, docstring
from .polar import PolarAxes

__all__ = ["TaylorAxes"]


_format_docstring = """
xlabel, ylabel : str, optional
    Labels for the standard-deviation axes. These are drawn as Taylor-specific
    text artists while the native polar axis labels are kept hidden.
corrlabel : str, default: 'Correlation'
    Label for the correlation-coefficient grid.
thetaunit : {'corr', 'deg', 'rad'}, default: 'corr'
    Units used for the angular grid labels. The default labels angular ticks
    as correlation coefficients.
quadrant : {1, 2, 3, 4} or str, default: 1
    The quadrant used for the Taylor diagram. Quadrants follow the Cartesian
    convention: ``1`` is upper right and ``4`` is lower right.
corrlocator, corrlines, corrticks : float or sequence of float, optional
    Correlation coefficients used for the angular gridlines.
labelcolor, labelsize, labelweight : optional
    Label text properties.
"""
docstring._snippet_manager["taylor.format"] = _format_docstring


class TaylorAxes(PolarAxes):
    """
    Axes subclass for Taylor diagrams.

    Important
    ---------
    This axes subclass can be used by passing ``proj='taylor'`` to
    axes-creation commands like `~ultraplot.figure.Figure.add_axes`,
    `~ultraplot.figure.Figure.add_subplot`, and
    `~ultraplot.figure.Figure.subplots`.
    """

    _name = "taylor"
    _name_aliases = ()
    _default_corrs = np.array((1.0, 0.95, 0.9, 0.8, 0.6, 0.4, 0.2, 0.0))
    _quadrant_aliases = {
        "1": 1,
        "i": 1,
        "ur": 1,
        "upper right": 1,
        "upright": 1,
        "2": 2,
        "ii": 2,
        "ul": 2,
        "upper left": 2,
        "upleft": 2,
        "3": 3,
        "iii": 3,
        "ll": 3,
        "lower left": 3,
        "lowleft": 3,
        "4": 4,
        "iv": 4,
        "lr": 4,
        "lower right": 4,
        "lowright": 4,
        "upside down": 4,
    }

    @docstring._snippet_manager
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        *args
            Passed to `matplotlib.axes.Axes`.
        %(taylor.format)s
        %(polar.format)s

        Other parameters
        ----------------
        %(axes.format)s
        %(rc.init)s

        See also
        --------
        TaylorAxes.format
        ultraplot.axes.PolarAxes
        """
        self._taylor_corrs = self._default_corrs.copy()
        self._taylor_thetaunit = "corr"
        self._taylor_quadrant = 1
        self._taylor_labelpad = None
        super().__init__(*args, **kwargs)
        self._ensure_taylor_artists()
        self._apply_taylor_defaults()

    @staticmethod
    def correlation_to_angle(correlation):
        """
        Convert correlation coefficients to Taylor-diagram polar angles.
        """
        correlation = np.asarray(correlation)
        return np.arccos(np.clip(correlation, -1, 1))

    @classmethod
    def _parse_quadrant(cls, quadrant):
        """
        Normalize Taylor quadrant input.
        """
        if quadrant is None:
            return None
        if isinstance(quadrant, str):
            key = quadrant.strip().lower().replace("-", " ")
            key = " ".join(key.split())
            quadrant = cls._quadrant_aliases.get(key)
        if quadrant in (1, 2, 3, 4):
            return int(quadrant)
        raise ValueError(
            "Invalid Taylor quadrant={!r}. Expected 1, 2, 3, 4, or an alias like "
            "'upper right' or 'lower right'.".format(quadrant)
        )

    @staticmethod
    def _quadrant_bounds(quadrant):
        """
        Return theta bounds in degrees for a Taylor quadrant.
        """
        return {
            1: (0, 90),
            2: (90, 180),
            3: (180, 270),
            4: (0, -90),
        }[quadrant]

    def _correlation_to_theta(self, correlation):
        """
        Convert correlation coefficients to displayed polar angles.
        """
        angle = self.correlation_to_angle(correlation)
        quadrant = self._taylor_quadrant
        if quadrant == 1:
            return angle
        if quadrant == 2:
            return np.pi / 2 + angle
        if quadrant == 3:
            return np.pi + angle
        return -angle

    def plot_corr(self, correlation, stddev, *args, **kwargs):
        """
        Plot values specified as correlation coefficient and standard deviation.
        """
        return self.plot(self._correlation_to_theta(correlation), stddev, *args, **kwargs)

    def scatter_corr(self, correlation, stddev, *args, **kwargs):
        """
        Scatter values specified as correlation coefficient and standard deviation.
        """
        return mpolar.PolarAxes.scatter(
            self, self._correlation_to_theta(correlation), stddev, *args, **kwargs
        )

    def get_tightbbox(self, renderer, *args, **kwargs):
        """
        Return a stable tight bbox before the first draw.

        Matplotlib's polar radial axis can report a spurious far-left bbox for
        Taylor's quarter-sector view before the first draw. This feeds back into
        UltraPlot's reference-width autosizing and creates excessive left margin.
        """
        bbox = super().get_tightbbox(renderer, *args, **kwargs.copy())
        axis_bbox = self.yaxis.get_tightbbox(renderer)
        window = self.get_window_extent(renderer)
        bogus_radial_bbox = (
            bbox is not None
            and axis_bbox is not None
            and axis_bbox.x0 < window.x0 - 0.25 * window.width
            and axis_bbox.width > 0.5 * window.width
        )
        if not bogus_radial_bbox:
            return bbox

        visible = self.yaxis.get_visible()
        try:
            self.yaxis.set_visible(False)
            bbox_no_yaxis = super().get_tightbbox(renderer, *args, **kwargs.copy())
        finally:
            self.yaxis.set_visible(visible)
        if bbox_no_yaxis is None:
            return bbox
        bbox = mtransforms.Bbox.from_extents(
            bbox_no_yaxis.x0,
            min(bbox.y0, bbox_no_yaxis.y0),
            max(bbox_no_yaxis.x1, window.x1),
            max(bbox.y1, bbox_no_yaxis.y1),
        )
        self._tight_bbox = bbox
        return bbox

    def set_xlabel(self, xlabel, fontdict=None, labelpad=None, **kwargs):
        """
        Set the Taylor x label while keeping the native polar label hidden.
        """
        text = super().set_xlabel(
            xlabel, fontdict=fontdict, labelpad=labelpad, **kwargs
        )
        self._ensure_taylor_artists()
        self.xaxis.label.set_visible(False)
        self._taylor_xlabel_artist.set_text(xlabel)
        if labelpad is not None:
            self._update_taylor_label_positions(labelpad)
        if fontdict:
            self._taylor_xlabel_artist.update(fontdict)
        kwargs.pop("loc", None)
        self._taylor_xlabel_artist.update(kwargs)
        return text

    def set_ylabel(self, ylabel, fontdict=None, labelpad=None, **kwargs):
        """
        Set the Taylor y label while keeping the native polar label hidden.
        """
        text = super().set_ylabel(
            ylabel, fontdict=fontdict, labelpad=labelpad, **kwargs
        )
        self._ensure_taylor_artists()
        self.yaxis.label.set_visible(False)
        self._taylor_ylabel_artist.set_text(ylabel)
        if labelpad is not None:
            self._update_taylor_label_positions(labelpad)
        if fontdict:
            self._taylor_ylabel_artist.update(fontdict)
        kwargs.pop("loc", None)
        self._taylor_ylabel_artist.update(kwargs)
        return text

    def _apply_taylor_defaults(self):
        """
        Apply the fixed quarter-polar Taylor diagram defaults.
        """
        thetamin, thetamax = self._quadrant_bounds(self._taylor_quadrant)
        self.set_thetamin(thetamin)
        self.set_thetamax(thetamax)
        self.set_theta_zero_location("E")
        self.set_theta_direction(1)
        self.set_rorigin(0)
        self.set_rlabel_position({1: 135, 2: 45, 3: 315, 4: 225}[self._taylor_quadrant])
        self.spines["polar"].set_visible(True)
        self.xaxis.label.set_visible(False)
        self.yaxis.label.set_visible(False)
        self._update_taylor_ticks()

    def _ensure_taylor_artists(self):
        """
        Create Taylor-specific label artists on demand.
        """
        if hasattr(self, "_taylor_xlabel_artist"):
            return

        kw = {
            "transform": self.transAxes,
            "clip_on": False,
            "zorder": 3.5,
        }
        self._taylor_xlabel_artist = self.text(
            0.5, -0.12, "", ha="center", va="top", **kw
        )
        self._taylor_ylabel_artist = self.text(
            -0.12,
            0.5,
            "",
            ha="center",
            va="bottom",
            rotation=90,
            rotation_mode="anchor",
            **kw,
        )
        self._taylor_corrlabel_artist = self.text(
            0.72,
            0.72,
            "Correlation",
            ha="center",
            va="bottom",
            rotation=-45,
            rotation_mode="anchor",
            **kw,
        )

    def _format_correlation(self, value):
        """
        Format one angular tick according to the active Taylor theta unit.
        """
        if self._taylor_thetaunit == "corr":
            return f"{value:.2f}"
        angle = np.arccos(np.clip(value, -1, 1))
        if self._taylor_thetaunit == "deg":
            return f"{np.rad2deg(angle):g}\N{DEGREE SIGN}"
        if self._taylor_thetaunit == "rad":
            return f"{angle:g}"
        raise ValueError(
            "Invalid thetaunit={!r}. Expected 'corr', 'deg', or 'rad'.".format(
                self._taylor_thetaunit
            )
        )

    def _update_taylor_label_positions(self, labelpad=None):
        """
        Update fixed Taylor label locations.
        """
        if labelpad is not None:
            self._taylor_labelpad = labelpad
        pad = _not_none(self._taylor_labelpad, rc["axes.labelpad"])
        try:
            pad = float(pad)
        except (TypeError, ValueError):
            pad = float(rc["axes.labelpad"])
        offset = 0.09 + 0.004 * pad
        quadrant = self._taylor_quadrant

        x_top = quadrant in (2, 3)
        y_right = quadrant in (3, 4)
        self._taylor_xlabel_artist.set_position(
            (0.5, 1 + offset if x_top else -offset)
        )
        self._taylor_xlabel_artist.set_verticalalignment(
            "bottom" if x_top else "top"
        )
        self._taylor_ylabel_artist.set_position(
            (1 + offset if y_right else -offset, 0.5)
        )
        self._taylor_ylabel_artist.set_horizontalalignment("left" if y_right else "center")
        self._taylor_ylabel_artist.set_verticalalignment(
            "center" if y_right else "bottom"
        )
        self._taylor_ylabel_artist.set_rotation(270 if y_right else 90)

        corr_positions = {
            1: (np.deg2rad(45), -45),
            2: (np.deg2rad(135), 45),
            3: (np.deg2rad(225), -45),
            4: (np.deg2rad(-45), 45),
        }
        theta, rotation = corr_positions[quadrant]
        _, rmax = self.get_ylim()
        radius = rmax + 0.22 * abs(rmax)
        self._taylor_corrlabel_artist.set_transform(self.transData)
        self._taylor_corrlabel_artist.set_position((theta, radius))
        self._taylor_corrlabel_artist.set_rotation(rotation)
        self._taylor_corrlabel_artist.set_horizontalalignment("center")
        self._taylor_corrlabel_artist.set_verticalalignment("bottom")

    def _update_taylor_labels(
        self,
        *,
        xlabel=None,
        ylabel=None,
        corrlabel=None,
        labelpad=None,
        labelcolor=None,
        labelsize=None,
        labelweight=None,
        xlabel_kw=None,
        ylabel_kw=None,
        corrlabel_kw=None,
    ):
        """
        Update Taylor-specific axis labels.
        """
        self._ensure_taylor_artists()
        xlabel_kw = xlabel_kw or {}
        ylabel_kw = ylabel_kw or {}
        corrlabel_kw = corrlabel_kw or {}
        props = rc._get_label_props(
            color=labelcolor,
            size=labelsize,
            weight=labelweight,
            labelpad=labelpad,
        )
        labelpad = props.pop("labelpad", None)
        self._update_taylor_label_positions(labelpad)

        if xlabel is not None:
            self.xaxis.set_label_text(xlabel)
            self.xaxis.label.set_visible(False)
            self._taylor_xlabel_artist.set_text(xlabel)
        if ylabel is not None:
            self.yaxis.set_label_text(ylabel)
            self.yaxis.label.set_visible(False)
            self._taylor_ylabel_artist.set_text(ylabel)
        if corrlabel is not None:
            self._taylor_corrlabel_artist.set_text(corrlabel)

        for artist, kw in (
            (self._taylor_xlabel_artist, xlabel_kw),
            (self._taylor_ylabel_artist, ylabel_kw),
            (self._taylor_corrlabel_artist, corrlabel_kw),
        ):
            artist.update(props)
            artist.update(kw)

    def _update_taylor_ticks(self, corrs=None):
        """
        Update angular grid labels from correlation coefficients.
        """
        if corrs is not None:
            corrs = np.asarray(corrs, dtype=float)
            if corrs.ndim == 0:
                step = float(corrs)
                if step <= 0:
                    raise ValueError("Taylor correlation tick step must be positive.")
                corrs = np.arange(1, -0.5 * step, -step)
                corrs = np.clip(corrs, 0, 1)
            self._taylor_corrs = corrs
        corrs = np.asarray(self._taylor_corrs, dtype=float)
        if np.any((corrs < -1) | (corrs > 1)):
            raise ValueError("Taylor correlation ticks must be between -1 and 1.")
        angles = self._correlation_to_theta(corrs)
        labels = [self._format_correlation(corr) for corr in corrs]
        self.xaxis.set_major_locator(mticker.FixedLocator(angles))
        self.xaxis.set_major_formatter(mticker.FixedFormatter(labels))

    @docstring._snippet_manager
    def format(
        self,
        *,
        xlabel=None,
        ylabel=None,
        corrlabel=None,
        thetaunit=None,
        quadrant=None,
        corrlocator=None,
        corrlines=None,
        corrticks=None,
        xlabel_kw=None,
        ylabel_kw=None,
        corrlabel_kw=None,
        labelpad=None,
        labelcolor=None,
        labelsize=None,
        labelweight=None,
        **kwargs,
    ):
        """
        Modify Taylor diagram labels, correlation gridlines, and polar settings.

        Parameters
        ----------
        %(taylor.format)s

        Other parameters
        ----------------
        %(polar.format)s
        %(axes.format)s
        %(figure.format)s
        %(rc.format)s

        See also
        --------
        ultraplot.axes.PolarAxes.format
        ultraplot.axes.Axes.format
        """
        rc_kw, rc_mode = _pop_rc(kwargs)
        with rc.context(rc_kw, mode=rc_mode):
            self._ensure_taylor_artists()
            quadrant = self._parse_quadrant(quadrant)
            if quadrant is not None:
                self._taylor_quadrant = quadrant
            self._apply_taylor_defaults()
            if thetaunit is not None:
                thetaunit = thetaunit.lower()
                if thetaunit not in ("corr", "deg", "rad"):
                    raise ValueError(
                        "Invalid thetaunit={!r}. Expected 'corr', 'deg', or 'rad'.".format(
                            thetaunit
                        )
                    )
                self._taylor_thetaunit = thetaunit
            corrs = _not_none(
                corrlocator=corrlocator, corrlines=corrlines, corrticks=corrticks
            )
            self._update_taylor_ticks(corrs)
            self._update_taylor_labels(
                xlabel=xlabel,
                ylabel=ylabel,
                corrlabel=corrlabel,
                labelpad=labelpad,
                labelcolor=labelcolor,
                labelsize=labelsize,
                labelweight=labelweight,
                xlabel_kw=xlabel_kw,
                ylabel_kw=ylabel_kw,
                corrlabel_kw=corrlabel_kw,
            )

        super().format(
            rc_kw=rc_kw,
            rc_mode=rc_mode,
            labelpad=labelpad,
            labelcolor=labelcolor,
            labelsize=labelsize,
            labelweight=labelweight,
            **kwargs,
        )
        self.xaxis.label.set_visible(False)
        self.yaxis.label.set_visible(False)
        self._update_taylor_label_positions()


TaylorAxes._format_signatures[TaylorAxes] = inspect.signature(TaylorAxes.format)
TaylorAxes.format = docstring._obfuscate_kwargs(TaylorAxes.format)
