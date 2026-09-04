#!/usr/bin/env python3
"""Axis-sharing policy and format-plan construction."""

from dataclasses import dataclass
from numbers import Integral

import numpy as np

_GENERIC_AXIS_LABEL_FORMAT_KEYS = {
    "labelpad",
    "labelcolor",
    "labelsize",
    "labelweight",
}

AXIS_LABEL_FORMAT_KEYS = {
    axis: {
        f"{axis}label",
        f"{axis}labelloc",
        f"{axis}labelpad",
        f"{axis}labelcolor",
        f"{axis}labelsize",
        f"{axis}labelweight",
        f"{axis}label_kw",
    }
    | _GENERIC_AXIS_LABEL_FORMAT_KEYS
    for axis in "xy"
}
AXIS_SHARED_STATE_FORMAT_KEYS = {
    axis: {
        f"{axis}lim",
        f"{axis}min",
        f"{axis}max",
        f"{axis}scale",
        f"{axis}reverse",
        f"{axis}margin",
        f"{axis}formatter",
        f"{axis}ticklabels",
        f"{axis}ticks",
        f"{axis}locator",
        f"{axis}minorticks",
        f"{axis}minorlocator",
        f"{axis}tickrange",
        f"{axis}wraprange",
        f"{axis}scale_kw",
        f"{axis}locator_kw",
        f"{axis}formatter_kw",
        f"{axis}minorlocator_kw",
    }
    for axis in "xy"
}
AXIS_TICKLABEL_SHARING_FORMAT_KEYS = {
    axis: {
        f"{axis}loc",
        f"{axis}spineloc",
        f"{axis}tickloc",
        f"{axis}ticklabelloc",
    }
    for axis in "xy"
}

# Geographic axes use longitude as their x-like coordinate and latitude as
# their y-like coordinate. Sparse figure calls and direct axes calls therefore
# make the same sharing decision.
AXIS_SHARED_STATE_FORMAT_KEYS["x"].update(
    {
        "extent",
        "lonlim",
        "lonlocator",
        "lonlines",
        "lonminorlocator",
        "lonminorlines",
        "lonformatter",
        "lonlocator_kw",
        "lonlines_kw",
        "lonminorlocator_kw",
        "lonminorlines_kw",
        "lonformatter_kw",
        "dms",
    }
)
AXIS_SHARED_STATE_FORMAT_KEYS["y"].update(
    {
        "extent",
        "latlim",
        "boundinglat",
        "latmax",
        "latlocator",
        "latlines",
        "latminorlocator",
        "latminorlines",
        "latformatter",
        "latlocator_kw",
        "latlines_kw",
        "latminorlocator_kw",
        "latminorlines_kw",
        "latformatter_kw",
        "dms",
    }
)
AXIS_TICKLABEL_SHARING_FORMAT_KEYS["x"].update(
    {"labels", "lonlabels", "loninline", "inlinelabels"}
)
AXIS_TICKLABEL_SHARING_FORMAT_KEYS["y"].update(
    {"labels", "latlabels", "latinline", "inlinelabels"}
)

AXIS_SHARING_FORMAT_KEYS = frozenset(
    key
    for mapping in (
        AXIS_LABEL_FORMAT_KEYS,
        AXIS_SHARED_STATE_FORMAT_KEYS,
        AXIS_TICKLABEL_SHARING_FORMAT_KEYS,
    )
    for keys in mapping.values()
    for key in keys
)

_LIMIT_KEYS = {"xlim", "ylim", "lonlim", "latlim"}


def get_axis_sharing_format_keys(*mappings, exclude=()):
    """Return non-null format keys that can contradict axis sharing."""
    values = {}
    for mapping in mappings:
        values.update(mapping)
    excluded = set(exclude)
    return {
        key
        for key, value in values.items()
        if value is not None and key in AXIS_SHARING_FORMAT_KEYS and key not in excluded
    }


def axis_supports_format_key(ax, key):
    """Return whether the concrete axis accepts a sharing-sensitive key."""
    if key in _GENERIC_AXIS_LABEL_FORMAT_KEYS:
        return True
    return any(
        isinstance(ax, axis_class) and key in signature.parameters
        for axis_class, signature in ax._format_signatures.items()
    )


def _selector_numbers(selector):
    """Return normalized one-based axis numbers for a mapping selector."""
    if isinstance(selector, Integral) and not isinstance(selector, bool):
        return (int(selector),)
    if isinstance(selector, (tuple, list, range)) and all(
        isinstance(item, Integral) and not isinstance(item, bool) for item in selector
    ):
        return tuple(int(item) for item in selector)
    return None


def _validate_limit(key, value):
    """Validate a single two-value Cartesian or geographic limit."""
    if value is None:
        return
    try:
        valid = not isinstance(value, str) and np.iterable(value) and len(value) == 2
    except TypeError:
        valid = False
    if not valid:
        raise ValueError(f"Invalid {key}={value!r}. Must be 2-tuple of values.")


def validate_axis_format_values(values):
    """Validate sharing-sensitive values before changing sharing state."""
    for key in _LIMIT_KEYS & values.keys():
        _validate_limit(key, values[key])


def axes_participate(figure, axes, which):
    """Return whether any selected main axis belongs to a directional group."""
    main_axes = tuple(figure._iter_subplots())
    main_set = set(main_axes)
    for ax in axes:
        if ax not in main_set:
            continue
        get_shared = getattr(ax, f"get_shared_{which}_axes", None)
        if get_shared is not None:
            try:
                siblings = get_shared().get_siblings(ax)
                if any(
                    sibling in main_set and sibling is not ax for sibling in siblings
                ):
                    return True
            except (AttributeError, TypeError):
                pass
        # Label-only sharing uses UltraPlot parent links rather than Matplotlib's
        # limit-sharing grouper, so inspect links in both directions.
        parent = getattr(ax, f"_share{which}", None)
        if parent in main_set or any(
            getattr(other, f"_share{which}", None) is ax for other in main_axes
        ):
            return True
    return False


def update_sharing_for_format_keys(figure, keys, *, axes=None):
    """Apply sharing changes implied by validated, supported format keys."""
    keys = set(keys)
    for which in "xy":
        participates = axes is None or axes_participate(figure, axes, which)
        figure._update_axis_sharing_for_format(
            which,
            labels=bool(participates and keys & AXIS_LABEL_FORMAT_KEYS[which]),
            limits=bool(participates and keys & AXIS_SHARED_STATE_FORMAT_KEYS[which]),
            ticklabels=bool(
                participates and keys & AXIS_TICKLABEL_SHARING_FORMAT_KEYS[which]
            ),
        )


def snapshot_axis_sharing(figure):
    """Capture figure sharing policy so a failed format call can restore it."""
    state = {}
    for which in "xy":
        state[which] = {
            name: getattr(figure, f"_share{which}_{name}")
            for name in ("labels", "limits", "ticklabels", "auto")
        }
        state[which]["level"] = getattr(figure, f"_share{which}")
        state[which]["span"] = getattr(figure, f"_span{which}")
        state[which]["groups"] = {
            key: {
                **group,
                "axes": list(group["axes"]),
                "props": None if group.get("props") is None else dict(group["props"]),
            }
            for key, group in figure._share_label_groups[which].items()
        }
    return state


def restore_axis_sharing(figure, state):
    """Restore sharing policy and topology after a failed format call."""
    for which, values in state.items():
        setattr(figure, f"_share{which}", values["level"])
        setattr(figure, f"_span{which}", values["span"])
        for name in ("labels", "limits", "ticklabels", "auto"):
            setattr(figure, f"_share{which}_{name}", values[name])
        figure._share_label_groups[which] = values["groups"]
        rebuild_axis_sharing(figure, which)


def rebuild_axis_sharing(figure, which):
    """Rebuild main-axis sharing while preserving intrinsic twin relations."""
    axes = list(figure._iter_axes(hidden=False, children=False, panels=False))
    parents = list(figure._iter_axes(hidden=True, children=False, panels=True))
    intrinsic = []
    for parent in parents:
        for child in parent.child_axes:
            if (
                which == "y"
                and getattr(child, "_altx_parent", None) is parent
                or which == "x"
                and getattr(child, "_alty_parent", None) is parent
            ):
                intrinsic.append((parent, child))

    for ax in axes:
        if hasattr(ax, "_unshare"):
            ax._unshare(which=which)
    for ax in axes:
        if hasattr(ax, "_apply_auto_share"):
            ax._apply_auto_share()

    # Alternate/twin axes intrinsically share their orthogonal coordinate with
    # their parent. This relationship is independent of figure-wide sharing.
    for parent, child in intrinsic:
        child._share_axis_with(parent, which=which)
        setattr(child, f"_share{which}", parent)


@dataclass
class AxisFormatPlan:
    """A validated plan for dispatching one ``Figure.format`` call."""

    axes: tuple
    kwargs: dict
    mappings: dict
    label_sequences: dict
    limit_sequences: dict
    signatures: dict
    generic_keys: frozenset

    @classmethod
    def build(cls, axes, kwargs, signatures, generic_keys):
        """Normalize mappings and per-axis sequences without changing state."""
        axes = tuple(axes)
        kwargs = dict(kwargs)
        signatures = dict(signatures)
        generic_keys = frozenset(generic_keys)
        axis_format_keys = generic_keys | {
            key for signature in signatures.values() for key in signature.parameters
        }

        mappings = {}
        for key, value in tuple(kwargs.items()):
            if key not in axis_format_keys or not isinstance(value, dict) or not value:
                continue
            parsed = [
                (_selector_numbers(selector), item) for selector, item in value.items()
            ]
            if not any(numbers is not None for numbers, _ in parsed):
                continue
            if any(numbers is None for numbers, _ in parsed):
                raise ValueError(f"Invalid mixed axes mapping for {key!r}: {value!r}.")
            mapping = {}
            for numbers, item in parsed:
                for number in numbers:
                    if number not in range(1, len(axes) + 1):
                        raise ValueError(
                            f"Invalid axes number {number} for {key!r}; "
                            f"expected 1 through {len(axes)}."
                        )
                    mapping[number] = item
            mappings[key] = mapping
            kwargs[key] = next(
                (item for item in mapping.values() if item is not None), None
            )

        label_sequences = {}
        for key in ("xlabel", "ylabel"):
            value = kwargs.get(key)
            if key in mappings or isinstance(value, str) or not np.iterable(value):
                continue
            value = tuple(value)
            if not all(isinstance(item, str) for item in value):
                continue
            if len(value) != len(axes):
                raise ValueError(
                    f"Invalid {key} list length {len(value)} "
                    f"for {len(axes)} formatted axes."
                )
            label_sequences[key] = value
            kwargs[key] = value

        limit_sequences = {}
        for key in ("xlim", "ylim"):
            value = kwargs.get(key)
            if key in mappings or value is None or isinstance(value, str):
                continue
            if not np.iterable(value):
                continue
            value = tuple(value)
            if not all(
                np.iterable(item) and not isinstance(item, str) for item in value
            ):
                continue
            if len(value) != len(axes):
                raise ValueError(
                    f"Invalid {key} list length {len(value)} "
                    f"for {len(axes)} formatted axes."
                )
            for item in value:
                _validate_limit(key, item)
            limit_sequences[key] = value
            kwargs[key] = value

        plan = cls(
            axes,
            kwargs,
            mappings,
            label_sequences,
            limit_sequences,
            signatures,
            generic_keys,
        )
        plan.validate()
        return plan

    def supports(self, ax, key):
        """Return whether an axis accepts a format key."""
        return key in self.generic_keys or any(
            isinstance(ax, axis_class) and key in signature.parameters
            for axis_class, signature in self.signatures.items()
        )

    def affects_sharing(self, ax, key):
        """Return whether a supported key has sharing semantics for an axis."""
        return self.supports(ax, key) and key not in getattr(
            ax, "_format_sharing_exclude", ()
        )

    def validate(self):
        """Validate values that will actually be dispatched to an axis."""
        for key, mapping in self.mappings.items():
            for number, value in mapping.items():
                if self.supports(self.axes[number - 1], key):
                    validate_axis_format_values({key: value})
        ordinary = {
            key: value
            for key, value in self.kwargs.items()
            if key not in self.mappings
            and key not in self.limit_sequences
            and any(self.supports(ax, key) for ax in self.axes)
        }
        validate_axis_format_values(ordinary)

    def update_sharing(self, figure):
        """Apply all sharing changes after successful plan validation."""
        all_axes = set(figure._iter_subplots())
        if len(all_axes) < 2 or not (set(self.axes) & all_axes):
            return

        for key, mapping in self.mappings.items():
            targets = tuple(
                self.axes[number - 1]
                for number, value in mapping.items()
                if value is not None
                and self.affects_sharing(self.axes[number - 1], key)
            )
            if targets:
                update_sharing_for_format_keys(figure, {key}, axes=targets)

        is_subset = bool(self.axes) and set(self.axes) != all_axes
        if is_subset:
            local_keys = {
                key
                for keys in (
                    *AXIS_SHARED_STATE_FORMAT_KEYS.values(),
                    *AXIS_TICKLABEL_SHARING_FORMAT_KEYS.values(),
                )
                for key in keys
            }
            if len(self.axes) == 1:
                local_keys.update(
                    key for keys in AXIS_LABEL_FORMAT_KEYS.values() for key in keys
                )
            keys = {
                key
                for key, value in self.kwargs.items()
                if value is not None
                and key not in self.mappings
                and key not in self.label_sequences
                and key not in self.limit_sequences
                and key in local_keys
            }
            for key in keys:
                targets = tuple(ax for ax in self.axes if self.affects_sharing(ax, key))
                if targets:
                    update_sharing_for_format_keys(figure, {key}, axes=targets)

        for key in self.label_sequences:
            update_sharing_for_format_keys(
                figure,
                {key},
                axes=tuple(ax for ax in self.axes if self.affects_sharing(ax, key)),
            )
        for key in self.limit_sequences:
            update_sharing_for_format_keys(
                figure,
                {key},
                axes=tuple(ax for ax in self.axes if self.affects_sharing(ax, key)),
            )

    def apply_overrides(self, number, ax, projection_kw, generic_kw):
        """Apply mapped and sequential values for one dispatch target."""
        for key, mapping in self.mappings.items():
            destination = generic_kw if key in self.generic_keys else projection_kw
            if number in mapping and self.supports(ax, key):
                destination[key] = mapping[number]
                if key in ("xlabel", "ylabel"):
                    getattr(ax, f"{key[0]}axis").label.set_visible(True)
            else:
                destination.pop(key, None)
        for sequences in (self.label_sequences, self.limit_sequences):
            for key, values in sequences.items():
                if self.supports(ax, key):
                    projection_kw[key] = values[number - 1]
                    if key in ("xlabel", "ylabel"):
                        getattr(ax, f"{key[0]}axis").label.set_visible(True)

    def implicit_label_directions(self, figure):
        """Return scalar labels that should span this multi-axis subset."""
        all_axes = set(figure._iter_subplots())
        if len(self.axes) < 2 or not all_axes or set(self.axes) == all_axes:
            return ()
        directions = []
        compatible_sides = {"x": {"top", "bottom"}, "y": {"left", "right"}}
        for which in "xy":
            key = f"{which}label"
            if (
                self.kwargs.get(key) is None
                or key in self.mappings
                or key in self.label_sequences
                or self.kwargs.get(f"share_{which}labels") is not None
                or any(
                    getattr(ax, "_panel_side", None)
                    not in (None, *compatible_sides[which])
                    for ax in self.axes
                )
            ):
                continue
            directions.append(which)
        return tuple(directions)
