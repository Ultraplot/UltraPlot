#!/usr/bin/env python3
"""
Text-related artists and helpers.
"""
from __future__ import annotations

from typing import Iterable, Tuple

import matplotlib.text as mtext
import numpy as np

from .internals import labels

__all__ = ["CurvedText"]


# Courtesy of Thomas Kühn in https://stackoverflow.com/questions/19353576/curved-text-rendering-in-matplotlib
class CurvedText(mtext.Text):
    """
    A text object that follows an arbitrary curve.

    Parameters
    ----------
    x, y : array-like
        Curve coordinates.
    text : str
        Text to render along the curve.
    axes : matplotlib.axes.Axes
        Target axes.
    **kwargs
        Passed to `matplotlib.text.Text` for character styling.
    """

    def __init__(self, x, y, text, axes, **kwargs):
        if axes is None:
            raise ValueError("'axes' is required for CurvedText.")

        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        if x.size != y.size:
            raise ValueError("'x' and 'y' must be the same length.")
        if x.size < 2:
            raise ValueError("'x' and 'y' must contain at least two points.")

        if kwargs.get("transform") is None:
            kwargs["transform"] = axes.transData

        # Initialize storage before Text.__init__ triggers set_text()
        self._characters = []
        self._curve_text = "" if text is None else str(text)
        self._text_kwargs = kwargs.copy()
        self._initializing = True

        super().__init__(x[0], y[0], " ", **kwargs)
        axes.add_artist(self)

        self._curve_x = x
        self._curve_y = y
        self._zorder = self.get_zorder()
        self._initializing = False

        self._build_characters(self._curve_text)

    def _build_characters(self, text: str) -> None:
        # Remove previous character artists
        for _, artist in self._characters:
            artist.remove()
        self._characters = []

        for char in text:
            if char == " ":
                t = mtext.Text(0, 0, " ", **self._text_kwargs)
                t.set_alpha(0.0)
            else:
                t = mtext.Text(0, 0, char, **self._text_kwargs)

            t.set_ha("center")
            t.set_va("center")
            t.set_rotation(0)
            t.set_zorder(self._zorder + 1)
            add_text = getattr(self.axes, "_add_text", None)
            if add_text is not None:
                add_text(t)
            else:
                self.axes.add_artist(t)
            self._characters.append((char, t))

    def set_text(self, s):
        if getattr(self, "_initializing", False):
            return super().set_text(" ")
        self._curve_text = "" if s is None else str(s)
        self._build_characters(self._curve_text)
        super().set_text(" ")

    def get_text(self):
        return self._curve_text

    def set_curve(self, x: Iterable[float], y: Iterable[float]) -> None:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        if x.size != y.size:
            raise ValueError("'x' and 'y' must be the same length.")
        if x.size < 2:
            raise ValueError("'x' and 'y' must contain at least two points.")
        self._curve_x = x
        self._curve_y = y

    def get_curve(self) -> Tuple[np.ndarray, np.ndarray]:
        return self._curve_x.copy(), self._curve_y.copy()

    def _apply_label_props(self, props) -> None:
        for _, t in self._characters:
            t.update = labels._update_label.__get__(t)
            t.update(props)

    def set_zorder(self, zorder):
        super().set_zorder(zorder)
        self._zorder = self.get_zorder()
        for _, t in self._characters:
            t.set_zorder(self._zorder + 1)

    def draw(self, renderer, *args, **kwargs):
        """
        Overload `Text.draw()` to update character positions and rotations.
        """
        self.update_positions(renderer)

    def update_positions(self, renderer) -> None:
        """
        Update positions and rotations of the individual text elements.
        """
        if not self._characters:
            return

        trans = self.get_transform()
        pts = trans.transform(np.column_stack([self._curve_x, self._curve_y]))
        x_disp = pts[:, 0]
        y_disp = pts[:, 1]

        dx = x_disp[1:] - x_disp[:-1]
        dy = y_disp[1:] - y_disp[:-1]
        seg_len = np.hypot(dx, dy)

        if np.allclose(seg_len, 0):
            for _, t in self._characters:
                t.set_alpha(0.0)
            return

        arc = np.concatenate([[0.0], np.cumsum(seg_len)])
        rads = np.arctan2(dy, dx)
        degs = np.degrees(rads)

        # Precompute widths for alignment
        widths = []
        for _, t in self._characters:
            t.set_rotation(0)
            t.set_ha("center")
            t.set_va("center")
            bbox = t.get_window_extent(renderer=renderer)
            widths.append(bbox.width)

        total = float(np.sum(widths))
        ha = self.get_ha()
        if ha in ("center", "middle"):
            rel_pos = max(0.0, 0.5 * (arc[-1] - total))
        elif ha in ("right", "center right"):
            rel_pos = max(0.0, arc[-1] - total)
        else:
            rel_pos = 0.0

        for (char, t), width in zip(self._characters, widths):
            target = rel_pos + width / 2.0
            if target > arc[-1] or seg_len.size == 0:
                t.set_alpha(0.0)
                rel_pos += width
                continue
            if char != " ":
                t.set_alpha(1.0)

            idx = np.searchsorted(arc, target, side="right") - 1
            idx = int(np.clip(idx, 0, seg_len.size - 1))
            if seg_len[idx] == 0:
                rel_pos += width
                continue

            fraction = (target - arc[idx]) / seg_len[idx]
            base = np.array(
                [x_disp[idx] + fraction * dx[idx], y_disp[idx] + fraction * dy[idx]]
            )

            # Alignment offset in display coordinates (unrotated)
            t.set_va("center")
            bbox_center = t.get_window_extent(renderer=renderer)
            t.set_va(self.get_va())
            bbox_target = t.get_window_extent(renderer=renderer)
            dr = bbox_target.get_points()[0] - bbox_center.get_points()[0]

            c = np.cos(rads[idx])
            s = np.sin(rads[idx])
            dr_rot = np.array([c * dr[0] - s * dr[1], s * dr[0] + c * dr[1]])

            pos_disp = base + dr_rot
            pos_data = trans.inverted().transform(pos_disp)

            t.set_position(pos_data)
            t.set_rotation(degs[idx])
            t.set_ha("center")
            t.set_va("center")

            rel_pos += width
