#!/usr/bin/env python3
"""
Sharing compatibility helpers used by Figure.
"""

from collections import defaultdict

from .. import axes as paxes
from . import warnings


class FigureSharing:
    """
    Share compatibility and warning policy for a figure.
    """

    def __init__(self, figure):
        self.figure = figure

    def axis_unit_signature(self, ax, which: str):
        axis_obj = getattr(ax, f"{which}axis", None)
        if axis_obj is None:
            return None
        if hasattr(axis_obj, "get_converter"):
            converter = axis_obj.get_converter()
        else:
            converter = getattr(axis_obj, "converter", None)
        units = getattr(axis_obj, "units", None)
        if hasattr(axis_obj, "get_units"):
            units = axis_obj.get_units()
        if converter is None and units is None:
            return None
        if isinstance(units, (str, bytes)):
            unit_tag = units
        elif units is not None:
            unit_tag = type(units).__name__
        else:
            unit_tag = None
        converter_tag = type(converter).__name__ if converter is not None else None
        return (converter_tag, unit_tag)

    def share_axes_compatible(self, ref, other, which: str):
        """Check whether two axes are compatible for sharing along one axis."""
        if ref is None or other is None:
            return False, "missing reference axis"
        if ref is other or which not in ("x", "y"):
            return True, None

        checks = (
            self._check_external_compatibility,
            self._check_geo_compatibility,
            self._check_polar_compatibility,
            self._check_family_compatibility,
            self._check_scale_compatibility,
            self._check_unit_compatibility,
        )
        for check in checks:
            ok, reason = check(ref, other, which)
            if not ok:
                return ok, reason
        return True, None

    def warn_incompatible_share(self, which: str, ref, other, reason: str) -> None:
        """Warn once per figure for explicit incompatible sharing."""
        figure = self.figure
        if figure._is_auto_share_mode(which):
            return
        if bool(figure._share_incompat_warned):
            return
        figure._share_incompat_warned = True
        warnings._warn_ultraplot(
            f"Skipping incompatible {which}-axis sharing for {type(ref).__name__} and {type(other).__name__}: {reason}."
        )

    def _check_external_compatibility(self, ref, other, which):
        del which
        ref_external = hasattr(ref, "has_external_axes") and ref.has_external_axes()
        other_external = (
            hasattr(other, "has_external_axes") and other.has_external_axes()
        )
        if not (ref_external or other_external):
            return True, None
        if not (ref_external and other_external):
            return False, "external and non-external axes cannot be shared"
        ref_ext = ref.get_external_axes()
        other_ext = other.get_external_axes()
        if type(ref_ext) is not type(other_ext):
            return False, "different external projection classes"
        return True, None

    def _check_geo_compatibility(self, ref, other, which):
        del which
        ref_geo = isinstance(ref, paxes.GeoAxes)
        other_geo = isinstance(other, paxes.GeoAxes)
        if not (ref_geo or other_geo):
            return True, None
        if not (ref_geo and other_geo):
            return False, "geo and non-geo axes cannot be shared"
        if not ref._is_rectilinear() or not other._is_rectilinear():
            return False, "non-rectilinear GeoAxes cannot be shared"
        if type(getattr(ref, "projection", None)) is not type(
            getattr(other, "projection", None)
        ):
            return False, "different Geo projection classes"
        return True, None

    def _check_polar_compatibility(self, ref, other, which):
        del which
        ref_polar = isinstance(ref, paxes.PolarAxes)
        other_polar = isinstance(other, paxes.PolarAxes)
        if ref_polar != other_polar:
            return False, "polar and non-polar axes cannot be shared"
        return True, None

    def _check_family_compatibility(self, ref, other, which):
        del which
        ref_geo = isinstance(ref, paxes.GeoAxes)
        other_geo = isinstance(other, paxes.GeoAxes)
        ref_external = hasattr(ref, "has_external_axes") and ref.has_external_axes()
        other_external = (
            hasattr(other, "has_external_axes") and other.has_external_axes()
        )
        if ref_geo or other_geo or ref_external or other_external:
            return True, None
        if not (
            isinstance(ref, paxes.CartesianAxes)
            and isinstance(other, paxes.CartesianAxes)
        ):
            return False, "different axis families"
        return True, None

    def _check_scale_compatibility(self, ref, other, which):
        get_scale_ref = getattr(ref, f"get_{which}scale", None)
        get_scale_other = getattr(other, f"get_{which}scale", None)
        if callable(get_scale_ref) and callable(get_scale_other):
            if get_scale_ref() != get_scale_other():
                return False, "different axis scales"
        return True, None

    def _check_unit_compatibility(self, ref, other, which):
        uref = self.axis_unit_signature(ref, which)
        uother = self.axis_unit_signature(other, which)
        if uref != uother and (uref is not None or uother is not None):
            return False, "different axis unit domains"
        return True, None

    def partition_share_axes(self, axes, which: str):
        """Partition a candidate share list into compatible sub-groups."""
        groups = []
        for ax in axes:
            if ax is None:
                continue
            placed = False
            first_mismatch = None
            for group in groups:
                ok, reason = self.share_axes_compatible(group[0], ax, which)
                if ok:
                    group.append(ax)
                    placed = True
                    break
                if first_mismatch is None:
                    first_mismatch = (group[0], reason)
            if not placed:
                groups.append([ax])
                if first_mismatch is not None:
                    ref, reason = first_mismatch
                    self.warn_incompatible_share(which, ref, ax, reason)
        return groups

    def iter_shared_groups(self, which: str, *, panels: bool = True):
        """Yield unique shared groups for one axis direction."""
        figure = self.figure
        if which not in ("x", "y"):
            return
        get_grouper = f"get_shared_{which}_axes"
        seen = set()
        for ax in figure._iter_axes(hidden=False, children=False, panels=panels):
            get_shared = getattr(ax, get_grouper, None)
            if not callable(get_shared):
                continue
            siblings = list(get_shared().get_siblings(ax))
            if len(siblings) < 2:
                continue
            key = frozenset(map(id, siblings))
            if key in seen:
                continue
            seen.add(key)
            yield siblings

    def join_shared_group(self, which: str, ref, other) -> None:
        """Join an axis to a shared group and copy the shared axis state."""
        ref._shared_axes[which].join(ref, other)
        axis = getattr(other, f"{which}axis")
        ref_axis = getattr(ref, f"{which}axis")
        setattr(other, f"_share{which}", ref)
        axis.major = ref_axis.major
        axis.minor = ref_axis.minor
        if which == "x":
            lim = ref.get_xlim()
            other.set_xlim(*lim, emit=False, auto=ref.get_autoscalex_on())
        else:
            lim = ref.get_ylim()
            other.set_ylim(*lim, emit=False, auto=ref.get_autoscaley_on())
        axis._scale = ref_axis._scale

    def refresh_auto_share(self, which=None) -> None:
        """Recompute auto-sharing groups after local axis-state changes."""
        figure = self.figure
        axes = list(figure._iter_axes(hidden=False, children=True, panels=True))
        targets = ("x", "y") if which is None else (which,)
        for target in targets:
            if not figure._is_auto_share_mode(target):
                continue
            for ax in axes:
                if hasattr(ax, "_unshare"):
                    ax._unshare(which=target)
            for ax in figure._iter_axes(hidden=False, children=False, panels=False):
                if hasattr(ax, "_apply_auto_share"):
                    ax._apply_auto_share()
            self.autoscale_shared_limits(target)

    def autoscale_shared_limits(self, which: str) -> None:
        """Recompute shared data limits for each compatible shared-axis group."""
        figure = self.figure
        if which not in ("x", "y"):
            return

        share_level = figure._sharex if which == "x" else figure._sharey
        if share_level <= 1:
            return

        get_auto = f"get_autoscale{which}_on"
        for siblings in self.iter_shared_groups(which, panels=True):
            for sib in siblings:
                relim = getattr(sib, "relim", None)
                if callable(relim):
                    relim()

            ref = siblings[0]
            for sib in siblings:
                auto = getattr(sib, get_auto, None)
                if callable(auto) and auto():
                    ref = sib
                    break

            autoscale_view = getattr(ref, "autoscale_view", None)
            if callable(autoscale_view):
                autoscale_view(scalex=(which == "x"), scaley=(which == "y"))

    def share_ticklabels(self, *, axis: str) -> None:
        """
        Share ticklabel visibility at the figure level.
        """
        figure = self.figure
        if not figure.stale:
            return

        outer_axes = figure._get_border_axes()
        sides = ("top", "bottom") if axis == "x" else ("left", "right")
        axes = list(figure._iter_axes(panels=True, hidden=False))
        groups = self.group_axes_by_axis(axes, axis)
        label_keys = self.label_key_map()

        for group_axes in groups.values():
            baseline, skip_group = self.compute_baseline_tick_state(
                group_axes, axis, label_keys
            )
            if skip_group:
                continue
            for axi in group_axes:
                masked = self.apply_border_mask(axi, baseline, sides, outer_axes)
                if self.effective_share_level(axi, axis, sides) < 3:
                    continue
                self.set_ticklabel_state(axi, axis, masked)

        figure.stale = True

    def label_key_map(self):
        """
        Return a mapping for version-dependent label keys for Matplotlib tick params.
        """
        figure = self.figure
        first_axi = next(figure._iter_axes(panels=True), None)
        if first_axi is None:
            return {
                "labelleft": "labelleft",
                "labelright": "labelright",
                "labeltop": "labeltop",
                "labelbottom": "labelbottom",
            }
        return {
            name: first_axi._label_key(name)
            for name in ("labelleft", "labelright", "labeltop", "labelbottom")
        }

    def group_axes_by_axis(self, axes, axis: str):
        """
        Group axes by row (x) or column (y). Panels included.
        """

        def _group_key(ax):
            ss = ax.get_subplotspec()
            return ss.rowspan.start if axis == "x" else ss.colspan.start

        groups = defaultdict(list)
        for axi in axes:
            try:
                key = _group_key(axi)
            except Exception:
                continue
            groups[key].append(axi)
        return groups

    def compute_baseline_tick_state(self, group_axes, axis: str, label_keys):
        """
        Build a baseline ticklabel visibility dict from main axes only.
        """
        baseline = {}
        subplot_types = set()
        unsupported_found = False
        sides = ("top", "bottom") if axis == "x" else ("left", "right")

        for axi in group_axes:
            if getattr(axi, "_panel_side", None):
                continue
            if isinstance(axi, paxes.GeoAxes) and not axi._is_rectilinear():
                return {}, True
            if not isinstance(
                axi, (paxes.CartesianAxes, paxes._CartopyAxes, paxes._BasemapAxes)
            ):
                warnings._warn_ultraplot(
                    f"Tick label sharing not implemented for {type(axi)} subplots."
                )
                unsupported_found = True
                break

            subplot_types.add(type(axi))
            if isinstance(axi, paxes.CartesianAxes):
                params = getattr(axi, f"{axis}axis").get_tick_params()
                for side in sides:
                    key = label_keys[f"label{side}"]
                    if params.get(key):
                        baseline[key] = params[key]
            elif isinstance(axi, paxes.GeoAxes):
                for side in sides:
                    key = f"label{side}"
                    if axi._is_ticklabel_on(key):
                        baseline[key] = axi._is_ticklabel_on(key)

        if unsupported_found:
            return {}, True
        if len(subplot_types) > 1:
            warnings._warn_ultraplot(
                "Tick label sharing not implemented for mixed subplot types."
            )
            return {}, True
        return baseline, False

    def apply_border_mask(
        self, axi, baseline: dict, sides: tuple[str, str], outer_axes
    ):
        """
        Apply figure-border constraints and panel opposite-side suppression.
        """
        from ..axes.cartesian import OPPOSITE_SIDE

        masked = baseline.copy()
        for side in sides:
            label = f"label{side}"
            if isinstance(axi, paxes.CartesianAxes):
                label = axi._label_key(label)
            if axi not in outer_axes[side]:
                masked[label] = False
            if (
                getattr(axi, "_panel_side", None)
                and OPPOSITE_SIDE[axi._panel_side] == side
            ):
                masked[label] = False
        return masked

    def effective_share_level(self, axi, axis: str, sides: tuple[str, str]) -> int:
        """
        Compute the effective share level for an axes.
        """
        level = getattr(self.figure, f"_share{axis}")
        if not level or (isinstance(level, (int, float)) and level < 1):
            return level
        if getattr(axi, f"_panel_share{axis}_group", None):
            return 3
        if getattr(axi, "_panel_side", None) and getattr(axi, f"_share{axis}", None):
            return 3
        panel_dict = getattr(axi, "_panel_dict", {})
        for side in sides:
            side_panels = panel_dict.get(side) or []
            if side_panels and getattr(side_panels[0], f"_share{axis}", False):
                return 3
        return level

    def set_ticklabel_state(self, axi, axis: str, state: dict):
        """Apply the computed ticklabel state to cartesian or geo axes."""
        if state:
            cleaned = {k: (True if v in ("x", "y") else v) for k, v in state.items()}
            if isinstance(axi, paxes.GeoAxes):
                axi._toggle_gridliner_labels(**cleaned)
            else:
                getattr(axi, f"{axis}axis").set_tick_params(**cleaned)

    def toggle_axis_sharing(
        self,
        *,
        which="y",
        share=True,
        panels=False,
        children=False,
        hidden=False,
    ):
        """
        Share or unshare axes in the figure along a given direction.
        """
        figure = self.figure
        if which not in ("x", "y", "z", "view"):
            warnings._warn_ultraplot(
                f"Attempting to (un)share {which=}. Options are ('x', 'y', 'z', 'view')"
            )
            return
        axes = list(figure._iter_axes(hidden=hidden, children=children, panels=panels))

        if which == "x":
            figure._sharex = share
        elif which == "y":
            figure._sharey = share

        if share == 0:
            for ax in axes:
                ax._unshare(which=which)
            return

        groups = {}
        for ax in axes:
            ss = ax.get_subplotspec()
            key = ss.rowspan.start if which == "x" else ss.colspan.start
            groups.setdefault(key, []).append(ax)

        for raw_group in groups.values():
            if which in ("x", "y"):
                subgroups = self.partition_share_axes(raw_group, which)
            else:
                subgroups = [raw_group]
            for group in subgroups:
                if not group:
                    continue
                ref = group[0]
                for other in group[1:]:
                    if which in ("x", "y"):
                        self.join_shared_group(which, ref, other)
                    else:
                        ref._shared_axes[which].join(ref, other)
