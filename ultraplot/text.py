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
    upright : bool, default: True
        Whether to flip the curve direction to keep text upright.
    ellipsis : bool, default: False
        Whether to show an ellipsis when the text exceeds curve length.
        avoid_overlap : bool, default: True
        Whether to hide glyphs that overlap after rotation.
    overlap_tol : float, default: 0.1
        Fractional overlap area (0–1) required before hiding a glyph.
    curvature_pad : float, default: 2.0
        Extra spacing in pixels per radian of local curvature.
    min_advance : float, default: 1.0
        Minimum additional spacing (pixels) enforced between glyph centers.
    **kwargs
        Passed to `matplotlib.text.Text` for character styling.
    """

    def __init__(
        self,
        x,
        y,
        text,
        axes,
        *,
        upright=True,
        ellipsis=False,
        avoid_overlap=True,
        overlap_tol=0.1,
        curvature_pad=2.0,
        min_advance=1.0,
        **kwargs,
    ):
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
        self._upright = bool(upright)
        self._ellipsis = bool(ellipsis)
        self._avoid_overlap = bool(avoid_overlap)
        self._overlap_tol = float(overlap_tol)
        self._curvature_pad = float(curvature_pad)
        self._min_advance = float(min_advance)
        self._ellipsis_text = "..."
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
        for char, t in self._characters:
            if t.get_text() != char:
                t.set_text(char)

        x_curve = self._curve_x
        y_curve = self._curve_y

        trans = self.get_transform()
        try:
            trans_inv = trans.inverted()
        except Exception:
            return
        pts = trans.transform(np.column_stack([x_curve, y_curve]))
        x_disp = pts[:, 0]
        y_disp = pts[:, 1]

        dx = np.diff(x_disp)
        dy = np.diff(y_disp)
        dx = np.asarray(dx, dtype=float).reshape(-1)
        dy = np.asarray(dy, dtype=float).reshape(-1)
        seg_len = np.asarray(np.hypot(dx, dy), dtype=float).reshape(-1)

        if np.allclose(seg_len, 0):
            for _, t in self._characters:
                t.set_alpha(0.0)
            return

        arc = np.concatenate([[0.0], np.cumsum(seg_len)])
        rads = np.arctan2(dy, dx)
        degs = np.degrees(rads)

        if self._upright and seg_len.size:
            mid = len(rads) // 2
            angle = np.degrees(rads[mid])
            if angle > 90 or angle < -90:
                x_curve = x_curve[::-1]
                y_curve = y_curve[::-1]
                pts = trans.transform(np.column_stack([x_curve, y_curve]))
                x_disp = pts[:, 0]
                y_disp = pts[:, 1]
                dx = np.diff(x_disp)
                dy = np.diff(y_disp)
                dx = np.asarray(dx, dtype=float).reshape(-1)
                dy = np.asarray(dy, dtype=float).reshape(-1)
                seg_len = np.asarray(np.hypot(dx, dy), dtype=float).reshape(-1)
                arc = np.concatenate([[0.0], np.cumsum(seg_len)])
                rads = np.arctan2(dy, dx)
                degs = np.degrees(rads)

        # Curvature proxy per segment (rad / pixel)
        kappa = np.zeros_like(seg_len)
        if len(rads) > 1:
            dtheta = np.diff(rads)
            dtheta = np.arctan2(np.sin(dtheta), np.cos(dtheta))  # wrap
            ds = 0.5 * (seg_len[1:] + seg_len[:-1])
            valid = ds > 0
            kappa_mid = np.zeros_like(dtheta)
            kappa_mid[valid] = np.abs(dtheta[valid]) / ds[valid]
            if kappa.size >= 2:
                kappa[1:] = kappa_mid
                kappa[0] = kappa_mid[0]
            else:
                kappa[:] = kappa_mid[0] if kappa_mid.size else 0.0
            if kappa.size >= 3:
                kernel = np.array([0.25, 0.5, 0.25])
                kappa = np.convolve(kappa, kernel, mode="same")

        # Precompute widths for alignment
        widths = []
        for _, t in self._characters:
            t.set_rotation(0)
            t.set_ha("center")
            t.set_va("center")
            bbox = t.get_window_extent(renderer=renderer)
            widths.append(bbox.width)

        total = float(np.sum(widths))
        ellipsis_active = False
        ellipsis_widths = []
        if self._ellipsis and self._characters:
            if total > arc[-1]:
                ellipsis_active = True
                dot = mtext.Text(0, 0, ".", **self._text_kwargs)
                dot.set_ha("center")
                dot.set_va("center")
                if self.figure is not None:
                    dot.set_figure(self.figure)
                dot.set_transform(self.get_transform())
                dot_width = dot.get_window_extent(renderer=renderer).width
                ellipsis_widths = [dot_width, dot_width, dot_width]
        ellipsis_count = min(3, len(self._characters)) if ellipsis_active else 0
        ellipsis_width = sum(ellipsis_widths[:ellipsis_count])
        limit = arc[-1] - ellipsis_width if ellipsis_active else arc[-1]

        ha = self.get_ha()
        if ha in ("center", "middle"):
            rel_pos = max(0.0, 0.5 * (arc[-1] - total))
        elif ha in ("right", "center right"):
            rel_pos = max(0.0, arc[-1] - total)
        else:
            rel_pos = 0.0

        prev_bbox = None

        def _place_at(target, t):
            if seg_len.size == 0:
                t.set_alpha(0.0)
                return None
            idx = np.searchsorted(arc, target, side="right") - 1
            idx = int(np.clip(idx, 0, seg_len.size - 1))
            dx_arr = np.atleast_1d(dx)
            dy_arr = np.atleast_1d(dy)
            seg_arr = np.atleast_1d(seg_len)
            if idx < 0 or idx >= seg_arr.size:
                t.set_alpha(0.0)
                return None
            if seg_arr[idx] == 0:
                t.set_alpha(0.0)
                return None
            fraction = (target - arc[idx]) / seg_arr[idx]
            base = np.array(
                [
                    x_disp[idx] + fraction * dx_arr[idx],
                    y_disp[idx] + fraction * dy_arr[idx],
                ]
            )
            t.set_va("center")
            bbox_center = t.get_window_extent(renderer=renderer)
            t.set_va(self.get_va())
            bbox_target = t.get_window_extent(renderer=renderer)
            dr = bbox_target.get_points()[0] - bbox_center.get_points()[0]
            c = np.cos(rads[idx])
            s = np.sin(rads[idx])
            dr_rot = np.array([c * dr[0] - s * dr[1], s * dr[0] + c * dr[1]])
            pos_disp = base + dr_rot
            pos_data = trans_inv.transform(pos_disp)
            t.set_position(pos_data)
            t.set_rotation(degs[idx])
            t.set_ha("center")
            t.set_va("center")
            t.set_alpha(1.0 if t.get_text().strip() else 0.0)
            return t.get_window_extent(renderer=renderer)

        # Precompute target centers (in arc-length units)
        n = len(self._characters)
        targets = np.zeros(n)
        advances = np.zeros(n)
        pos = rel_pos
        for i, width in enumerate(widths):
            base_target = pos + width / 2.0
            base_idx = int(
                np.clip(
                    np.searchsorted(arc, base_target, side="right") - 1,
                    0,
                    seg_len.size - 1,
                )
            )
            extra_pad = self._curvature_pad * kappa[base_idx] * width
            advance = width + extra_pad + self._min_advance
            targets[i] = pos + advance / 2.0
            advances[i] = advance
            pos += advance

        # Relax targets to enforce minimum spacing if requested
        if self._avoid_overlap and n > 1:
            for _ in range(3):  # a few passes is enough
                for i in range(1, n):
                    min_sep = 0.5 * (advances[i - 1] + advances[i])
                    if targets[i] < targets[i - 1] + min_sep:
                        targets[i] = targets[i - 1] + min_sep
                for i in range(n - 2, -1, -1):
                    min_sep = 0.5 * (advances[i] + advances[i + 1])
                    if targets[i] > targets[i + 1] - min_sep:
                        targets[i] = targets[i + 1] - min_sep

            # Clamp to curve length by shifting the whole sequence if needed
            span_left = targets[0] - 0.5 * advances[0]
            span_right = targets[-1] + 0.5 * advances[-1]
            max_right = limit if ellipsis_active else arc[-1]
            shift = 0.0
            if span_left < 0:
                shift = -span_left
            if span_right + shift > max_right:
                shift = max_right - span_right
            if shift != 0.0:
                targets = targets + shift

        # Place main glyphs
        for idx, ((char, t), width) in enumerate(zip(self._characters, widths)):
            if ellipsis_active and idx >= len(self._characters) - ellipsis_count:
                t.set_alpha(0.0)
                continue
            target = targets[idx]
            if ellipsis_active and target > limit:
                t.set_alpha(0.0)
                continue
            _place_at(target, t)

        # Place ellipsis at the end if needed
        if ellipsis_active and ellipsis_count:
            rel_end = arc[-1] - ellipsis_width
            rel_end = max(0.0, rel_end)
            targets = []
            running = rel_end
            for w in ellipsis_widths[:ellipsis_count]:
                targets.append(running + w / 2.0)
                running += w
            start = len(self._characters) - ellipsis_count
            for (char, t), target in zip(self._characters[start:], targets):
                t.set_text(".")
                bbox = _place_at(target, t)
                if bbox is not None and self._avoid_overlap and prev_bbox is not None:
                    attempts = 0
                    while (
                        bbox is not None and bbox.overlaps(prev_bbox) and attempts < 20
                    ):
                        ov_dx = min(bbox.x1, prev_bbox.x1) - max(bbox.x0, prev_bbox.x0)
                        ov_dy = min(bbox.y1, prev_bbox.y1) - max(bbox.y0, prev_bbox.y0)
                        if ov_dx <= 0 or ov_dy <= 0:
                            break
                        overlap_area = ov_dx * ov_dy
                        min_area = min(
                            bbox.width * bbox.height, prev_bbox.width * prev_bbox.height
                        )
                        if not min_area or overlap_area / min_area <= self._overlap_tol:
                            break
                        target += max(1.0, ov_dx + 1.0)
                        bbox = _place_at(target, t)
                        attempts += 1
                    if bbox is not None:
                        prev_bbox = bbox
                elif bbox is not None:
                    prev_bbox = bbox
