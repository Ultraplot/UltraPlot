#!/usr/bin/env python3
"""
Figure-level spanning-label and super-label helpers.
"""

import matplotlib.text as mtext
import matplotlib.transforms as mtransforms

from .. import axes as paxes
from ..config import rc
from . import labels, warnings


class FigureLabels:
    """
    Figure-level label coordination for spanning and super labels.
    """

    def __init__(self, figure):
        self.figure = figure

    def align_axis_label(self, axis):
        figure = self.figure
        seen = set()
        span = getattr(figure, "_span" + axis)
        align = getattr(figure, "_align" + axis)
        for ax in figure._subplot_dict.values():
            if not isinstance(ax, paxes.CartesianAxes):
                continue
            ax._apply_axis_sharing()
            side = getattr(ax, axis + "axis").get_label_position()
            if ax in seen or side not in ("bottom", "left"):
                continue
            axs = ax._get_span_axes(side, panels=False)
            if self.has_share_label_groups(axis) and any(
                self.is_share_label_group_member(axi, axis) for axi in axs
            ):
                continue
            if any(getattr(ax, "_share" + axis) for ax in axs):
                continue
            seen.update(axs)
            if span or align:
                group = self._get_align_label_group(axis)
                if group is not None:
                    for other in axs[1:]:
                        group.join(axs[0], other)
            if span:
                self.update_axis_label(side, axs)
        self.apply_share_label_groups(axis=axis)

    def _get_align_label_group(self, axis):
        figure = self.figure
        if hasattr(figure, "_align_label_groups"):
            return figure._align_label_groups[axis]
        return getattr(figure, "_align_" + axis + "label_grp", None)

    def register_share_label_group(self, axes, *, target, source=None):
        axes = self._normalize_group_axes(axes)
        if len(axes) < 2:
            return
        axes_by_side = self._split_axes_by_side(axes, target)
        if len(axes_by_side) > 1:
            for side, side_axes in axes_by_side.items():
                side_source = source if source in side_axes else None
                self.register_share_label_group_for_side(
                    side_axes,
                    target=target,
                    side=side,
                    source=side_source,
                )
            return
        side, side_axes = next(iter(axes_by_side.items()))
        self.register_share_label_group_for_side(
            side_axes,
            target=target,
            side=side,
            source=source,
        )

    def _normalize_group_axes(self, axes):
        figure = self.figure
        if not axes:
            return []
        axes = [ax for ax in list(axes) if ax is not None and ax.figure is figure]
        seen = set()
        unique = []
        for ax in axes:
            ax_id = id(ax)
            if ax_id in seen:
                continue
            seen.add(ax_id)
            unique.append(ax)
        return unique

    def _split_axes_by_side(self, axes, target):
        axes_by_side = {}
        if target == "x":
            for ax in axes:
                axes_by_side.setdefault(ax.xaxis.get_label_position(), []).append(ax)
        else:
            for ax in axes:
                axes_by_side.setdefault(ax.yaxis.get_label_position(), []).append(ax)
        return axes_by_side

    def register_share_label_group_for_side(self, axes, *, target, side, source=None):
        figure = self.figure
        axes = [ax for ax in axes if ax is not None and ax.figure is figure]
        if len(axes) < 2:
            return

        label = self._find_group_label(axes, target, source=source)
        text = label.get_text() if label else ""
        props = self._label_props(label)
        group_key = tuple(sorted(id(ax) for ax in axes))
        groups = figure._share_label_groups[target]
        group = groups.get(group_key)
        payload = {
            "axes": axes,
            "side": side,
            "text": text if text.strip() else "",
            "props": props,
        }
        if group is None:
            groups[group_key] = payload
            return
        group.update(payload)
        if not text.strip():
            group.setdefault("text", "")

    def _find_group_label(self, axes, target, *, source=None):
        if source in axes:
            candidate = getattr(source, f"{target}axis").label
            if candidate.get_text().strip():
                return candidate
        for ax in axes:
            candidate = getattr(ax, f"{target}axis").label
            if candidate.get_text().strip():
                return candidate
        return None

    def _label_props(self, label):
        if label is None:
            return None
        return {
            "color": label.get_color(),
            "fontproperties": label.get_font_properties(),
            "rotation": label.get_rotation(),
            "rotation_mode": label.get_rotation_mode(),
            "ha": label.get_ha(),
            "va": label.get_va(),
        }

    def is_share_label_group_member(self, ax, axis):
        groups = self.figure._share_label_groups.get(axis, {})
        return any(ax in group["axes"] for group in groups.values())

    def has_share_label_groups(self, axis):
        return bool(self.figure._share_label_groups.get(axis, {}))

    def clear_share_label_groups(self, axes=None, *, target=None):
        figure = self.figure
        targets = ("x", "y") if target is None else (target,)
        axes_set = None if axes is None else {ax for ax in axes if ax is not None}
        for axis in targets:
            groups = figure._share_label_groups.get(axis, {})
            if axes_set is None:
                groups.clear()
            else:
                for key in list(groups):
                    if any(ax in axes_set for ax in groups[key]["axes"]):
                        del groups[key]
            if axes_set is None:
                continue
            label_dict = (
                figure._supxlabel_dict if axis == "x" else figure._supylabel_dict
            )
            for ax in axes_set:
                if ax in label_dict:
                    label_dict[ax].set_text("")

    def apply_share_label_groups(self, axis=None):
        figure = self.figure
        layout = figure._layout_helper
        axes = (axis,) if axis in ("x", "y") else ("x", "y")
        for target in axes:
            groups = figure._share_label_groups.get(target, {})
            for group in groups.values():
                axs = [
                    ax
                    for ax in group["axes"]
                    if ax.figure is figure and ax.get_visible()
                ]
                if len(axs) < 2:
                    continue
                side = group["side"]
                ordered_axs = self._order_axes_for_side(axs, side)
                text, props = self._refresh_group_label(group, ordered_axs, target)
                if not text:
                    continue
                try:
                    _, ax = layout.get_align_coord(
                        side,
                        ordered_axs,
                        includepanels=figure._includepanels,
                    )
                except Exception:
                    continue
                axlab = getattr(ax, f"{target}axis").label
                axlab.set_text(text)
                if props is not None:
                    self._apply_label_props(axlab, props)
                self.update_axis_label(side, ordered_axs)

    def _order_axes_for_side(self, axs, side):
        if side in ("bottom", "top"):
            key = (
                (lambda ax: ax._range_subplotspec("y")[1])
                if side == "bottom"
                else (lambda ax: ax._range_subplotspec("y")[0])
            )
            reverse = side == "bottom"
        else:
            key = (
                (lambda ax: ax._range_subplotspec("x")[1])
                if side == "right"
                else (lambda ax: ax._range_subplotspec("x")[0])
            )
            reverse = side == "right"
        try:
            return sorted(axs, key=key, reverse=reverse)
        except Exception:
            return list(axs)

    def _refresh_group_label(self, group, ordered_axs, target):
        label = self._find_group_label(ordered_axs, target)
        text = group["text"]
        props = group["props"]
        if label is not None:
            text = label.get_text()
            props = self._label_props(label)
            group["text"] = text
            group["props"] = props
        return text, props

    def _apply_label_props(self, label, props):
        label.set_color(props["color"])
        label.set_fontproperties(props["fontproperties"])
        label.set_rotation(props["rotation"])
        label.set_rotation_mode(props["rotation_mode"])
        label.set_ha(props["ha"])
        label.set_va(props["va"])

    def align_super_labels(self, side, renderer):
        figure = self.figure
        for ax in figure._subplot_dict.values():
            ax._apply_title_above()
        if side not in ("left", "right", "bottom", "top"):
            raise ValueError(f"Invalid side {side!r}.")
        labs = figure._suplabel_dict[side]
        axs = tuple(ax for ax, lab in labs.items() if lab.get_text())
        if not axs:
            return
        coord = figure._layout_helper.get_offset_coord(side, axs, renderer)
        attr = "x" if side in ("left", "right") else "y"
        for lab in labs.values():
            lab.update({attr: coord})

    def align_super_title(self, renderer):
        figure = self.figure
        layout = figure._layout_helper
        if not figure._suptitle.get_text():
            return
        axs = layout.get_align_axes("top")
        if not axs:
            return
        labs = tuple(t for t in figure._suplabel_dict["top"].values() if t.get_text())
        pad = (figure._suptitle_pad / 72) / figure.get_size_inches()[1]
        ha = figure._suptitle.get_ha()
        va = figure._suptitle.get_va()
        x, _ = layout.get_align_coord(
            "top",
            axs,
            includepanels=figure._includepanels,
            align=ha,
        )
        y_target = layout.get_offset_coord("top", axs, renderer, pad=pad, extra=labs)
        figure._suptitle.set_ha(ha)
        figure._suptitle.set_va(va)
        figure._suptitle.set_position((x, 0))
        bbox = figure._suptitle.get_window_extent(renderer)
        y_bbox = figure.transFigure.inverted().transform((0, bbox.ymin))[1]
        figure._suptitle.set_position((x, y_target - y_bbox))

    def update_axis_label(self, side, axs):
        figure = self.figure
        layout = figure._layout_helper
        x, y = "xy" if side in ("bottom", "top") else "yx"
        coord, ax = layout.get_align_coord(
            side, axs, includepanels=figure._includepanels
        )
        axlab = getattr(ax, x + "axis").label
        suplabs = getattr(figure, "_sup" + x + "label_dict")
        suplab = suplabs.get(ax, None)
        if suplab is None and not axlab.get_text().strip():
            return
        if suplab is not None and not suplab.get_text().strip():
            return
        if suplab is None:
            props = ("ha", "va", "rotation", "rotation_mode")
            suplab = suplabs[ax] = figure.text(0, 0, "")
            suplab.update({prop: getattr(axlab, "get_" + prop)() for prop in props})
        suplab.set_in_layout(False)
        labels._transfer_label(axlab, suplab)
        count = 1 + suplab.get_text().count("\n")
        space = "\n".join(" " * count)
        for ax in axs:
            getattr(ax, x + "axis").label.set_text(space)

        transform = mtransforms.IdentityTransform()
        cx, cy = axlab.get_position()
        if x == "x":
            trans = mtransforms.blended_transform_factory(figure.transFigure, transform)
            position = (coord, cy)
        else:
            trans = mtransforms.blended_transform_factory(transform, figure.transFigure)
            position = (cx, coord)
        suplab.set_transform(trans)
        suplab.set_position(position)
        setpos = getattr(mtext.Text, "set_" + y)

        def _set_coord(self, *args, **kwargs):
            setpos(self, *args, **kwargs)
            setpos(suplab, *args, **kwargs)

        setattr(axlab, "set_" + y, _set_coord.__get__(axlab))

    def update_super_labels(self, side, label_values, **kwargs):
        figure = self.figure
        layout = figure._layout_helper
        if side not in ("left", "right", "bottom", "top"):
            raise ValueError(f"Invalid side {side!r}.")
        kw = rc.fill(
            {
                "color": side + "label.color",
                "rotation": side + "label.rotation",
                "size": side + "label.size",
                "weight": side + "label.weight",
                "family": "font.family",
            },
            context=True,
        )
        kw.update(kwargs)
        props = figure._suplabel_props[side]
        props.update(kw)

        axs = layout.get_align_axes(side)
        if not axs:
            return
        if not label_values:
            label_values = [None for _ in axs]
        if not kw and all(_ is None for _ in label_values):
            return
        if len(label_values) != len(axs):
            raise ValueError(
                f"Got {len(label_values)} {side} labels but found {len(axs)} axes "
                f"along the {side} side of the figure."
            )
        src = figure._suplabel_dict[side]
        extra = src.keys() - set(axs)
        for ax in extra:
            text = src[ax].get_text()
            if text:
                warnings._warn_ultraplot(
                    f"Removing {side} label with text {text!r} from axes {ax.number}."
                )
            src[ax].remove()

        for ax, label in zip(axs, label_values):
            obj = self._get_or_create_super_label(src, side, ax, props)
            if kw:
                obj.update(kw)
            if label is not None:
                obj.set_text(label)

    def _get_or_create_super_label(self, src, side, ax, props):
        figure = self.figure
        if ax in src:
            return src[ax]
        tf = figure.transFigure
        if side in ("left", "right"):
            trans = mtransforms.blended_transform_factory(tf, ax.transAxes)
            obj = src[ax] = figure.text(0, 0.5, "", transform=trans)
        else:
            trans = mtransforms.blended_transform_factory(ax.transAxes, tf)
            obj = src[ax] = figure.text(0.5, 0, "", transform=trans)
        obj.update(props)
        return obj

    def update_super_title(self, title, **kwargs):
        figure = self.figure
        kw = rc.fill(
            {
                "size": "suptitle.size",
                "weight": "suptitle.weight",
                "color": "suptitle.color",
                "family": "font.family",
            },
            context=True,
        )
        kw.update(kwargs)
        if kw:
            figure._suptitle.update(kw)
        if title is not None:
            figure._suptitle.set_text(title)
