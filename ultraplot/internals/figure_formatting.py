#!/usr/bin/env python3
"""
Figure-level formatting helpers.
"""

from .. import axes as paxes
from ..config import rc
from . import _not_none, _pop_params, _pop_rc, warnings


class FigureFormatting:
    """
    Figure-wide formatting coordinator.
    """

    def __init__(self, figure):
        self.figure = figure

    def format(
        self,
        axs=None,
        *,
        figtitle=None,
        suptitle=None,
        suptitle_kw=None,
        llabels=None,
        leftlabels=None,
        leftlabels_kw=None,
        rlabels=None,
        rightlabels=None,
        rightlabels_kw=None,
        blabels=None,
        bottomlabels=None,
        bottomlabels_kw=None,
        tlabels=None,
        toplabels=None,
        toplabels_kw=None,
        rowlabels=None,
        collabels=None,
        includepanels=None,
        **kwargs,
    ):
        figure = self.figure
        figure._layout_dirty = True
        axs = axs or figure._subplot_dict.values()
        skip_axes = kwargs.pop("skip_axes", False)
        rc_kw, rc_mode = _pop_rc(kwargs)
        with rc.context(rc_kw, mode=rc_mode):
            self._apply_figure_state(
                figtitle=figtitle,
                suptitle=suptitle,
                suptitle_kw=suptitle_kw,
                llabels=llabels,
                leftlabels=leftlabels,
                leftlabels_kw=leftlabels_kw,
                rlabels=rlabels,
                rightlabels=rightlabels,
                rightlabels_kw=rightlabels_kw,
                blabels=blabels,
                bottomlabels=bottomlabels,
                bottomlabels_kw=bottomlabels_kw,
                tlabels=tlabels,
                toplabels=toplabels,
                toplabels_kw=toplabels_kw,
                rowlabels=rowlabels,
                collabels=collabels,
                includepanels=includepanels,
            )
        if skip_axes:
            return

        projection_kwargs = {
            cls: _pop_params(kwargs, sig)
            for cls, sig in paxes.Axes._format_signatures.items()
        }
        used_classes = set()
        for number, ax in enumerate(axs, start=1):
            store_old_number = ax.number
            if ax.number != number:
                ax.number = number
            per_axes_kwargs = self._collect_axes_kwargs(
                ax,
                projection_kwargs,
                used_classes,
            )
            ax.format(
                rc_kw=rc_kw,
                rc_mode=rc_mode,
                skip_figure=True,
                **per_axes_kwargs,
                **kwargs,
            )
            ax.number = store_old_number
        self._warn_unused_projection_kwargs(projection_kwargs, used_classes)

    def _apply_figure_state(
        self,
        *,
        figtitle=None,
        suptitle=None,
        suptitle_kw=None,
        llabels=None,
        leftlabels=None,
        leftlabels_kw=None,
        rlabels=None,
        rightlabels=None,
        rightlabels_kw=None,
        blabels=None,
        bottomlabels=None,
        bottomlabels_kw=None,
        tlabels=None,
        toplabels=None,
        toplabels_kw=None,
        rowlabels=None,
        collabels=None,
        includepanels=None,
    ):
        figure = self.figure
        kw = rc.fill({"facecolor": "figure.facecolor"}, context=True)
        figure.patch.update(kw)

        pad = rc.find("suptitle.pad", context=True)
        if pad is not None:
            figure._suptitle_pad = pad
        for side in tuple(figure._suplabel_pad):
            pad = rc.find(side + "label.pad", context=True)
            if pad is not None:
                figure._suplabel_pad[side] = pad
        if includepanels is not None:
            figure._includepanels = includepanels

        suptitle_kw = suptitle_kw or {}
        leftlabels_kw = leftlabels_kw or {}
        rightlabels_kw = rightlabels_kw or {}
        bottomlabels_kw = bottomlabels_kw or {}
        toplabels_kw = toplabels_kw or {}
        figure._update_super_title(
            _not_none(figtitle=figtitle, suptitle=suptitle),
            **suptitle_kw,
        )
        figure._update_super_labels(
            "left",
            _not_none(rowlabels=rowlabels, leftlabels=leftlabels, llabels=llabels),
            **leftlabels_kw,
        )
        figure._update_super_labels(
            "right",
            _not_none(rightlabels=rightlabels, rlabels=rlabels),
            **rightlabels_kw,
        )
        figure._update_super_labels(
            "bottom",
            _not_none(bottomlabels=bottomlabels, blabels=blabels),
            **bottomlabels_kw,
        )
        figure._update_super_labels(
            "top",
            _not_none(collabels=collabels, toplabels=toplabels, tlabels=tlabels),
            **toplabels_kw,
        )

    def _collect_axes_kwargs(self, ax, projection_kwargs, used_classes):
        kw = {
            key: value
            for cls, cls_kwargs in projection_kwargs.items()
            for key, value in cls_kwargs.items()
            if isinstance(ax, cls) and not used_classes.add(cls)
        }
        self._drop_shared_label_kwargs(ax, kw)
        return kw

    def _drop_shared_label_kwargs(self, ax, kw):
        if kw.get("xlabel") is not None and self._has_conflicting_share_label(ax, "x"):
            kw.pop("xlabel", None)
        if kw.get("ylabel") is not None and self._has_conflicting_share_label(ax, "y"):
            kw.pop("ylabel", None)

    def _has_conflicting_share_label(self, ax, axis):
        figure = self.figure
        if not figure._label_helper.has_share_label_groups(axis):
            return False
        return self._axis_has_share_label_text(ax, axis) or self._axis_has_label_text(
            ax, axis
        )

    def _axis_has_share_label_text(self, ax, axis):
        groups = self.figure._share_label_groups.get(axis, {})
        for group in groups.values():
            if ax in group["axes"] and str(group.get("text", "")).strip():
                return True
        return False

    def _axis_has_label_text(self, ax, axis):
        text = ax.get_xlabel() if axis == "x" else ax.get_ylabel()
        return bool(text and text.strip())

    def _warn_unused_projection_kwargs(self, projection_kwargs, used_classes):
        kw = {
            key: value
            for name in projection_kwargs.keys() - used_classes
            for key, value in projection_kwargs[name].items()
        }
        if kw:
            warnings._warn_ultraplot(
                f"Ignoring unused projection-specific format() keyword argument(s): {kw}"
            )
