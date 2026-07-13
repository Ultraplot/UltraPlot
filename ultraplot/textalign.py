#!/usr/bin/env python3
"""
Automatic repositioning of text and annotation boxes so they do not overlap.

The solver works entirely in display (pixel) space, so it is agnostic to the
transform attached to each label -- data, axes, log-scaled, polar and
geographic labels are all handled the same way. Labels are reset to their
original anchors before every pass, which keeps the result stable across
repeated draws, resizes and dpi changes.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

import matplotlib.collections as mcollections
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.text as mtext
import matplotlib.transforms as mtransforms
import numpy as np

__all__ = ["align_text"]

_ZERO = np.zeros(2)

#: Above this many labels, fall back to a single relaxation schedule (see below).
_RESTART_LIMIT = 120


def _points_to_pixels(fig, value) -> float:
    return float(value) * fig.dpi / 72.0


def _expand_bbox(bbox, padx: float, pady: float):
    return mtransforms.Bbox.from_extents(
        bbox.x0 - padx, bbox.y0 - pady, bbox.x1 + padx, bbox.y1 + pady
    )


def _fits(box, sx, sy, bounds) -> bool:
    """
    Whether shifting ``box`` (x0, y0, x1, y1) by half of (sx, sy) keeps it inside
    ``bounds`` -- half, because a box only takes half of a pairwise push.
    """
    if bounds is None:
        return True
    dx, dy = 0.5 * sx, 0.5 * sy
    return (
        box[0] + dx >= bounds[0] - 1e-6
        and box[2] + dx <= bounds[2] + 1e-6
        and box[1] + dy >= bounds[1] - 1e-6
        and box[3] + dy <= bounds[3] + 1e-6
    )


def _overlap_shift(b1, b2, bounds=None):
    """
    Return the translation ``(sx, sy)`` separating box ``b1`` from ``b2``, or zeros.

    Boxes are ``(x0, y0, x1, y1)``. Both axis-aligned escape routes are considered
    and the shallower one wins, because every pixel a label moves is a pixel further
    from the thing it describes. If that route would push the label out of
    ``bounds`` the other one is used instead -- without this, a stack of labels
    jammed against the edge of the axes gets shoved straight back into the wall on
    every iteration and can never spread out sideways.

    This runs once per colliding pair per iteration, so it deals in plain floats:
    building a two-element numpy array here costs more than all the arithmetic.
    """
    dx = min(b1[2], b2[2]) - max(b1[0], b2[0])
    if dx <= 0:
        return 0.0, 0.0
    dy = min(b1[3], b2[3]) - max(b1[1], b2[1])
    if dy <= 0:
        return 0.0, 0.0
    sx = dx if (b1[0] + b1[2]) >= (b2[0] + b2[2]) else -dx
    sy = dy if (b1[1] + b1[3]) >= (b2[1] + b2[3]) else -dy
    if dx < dy:
        first, second = (sx, 0.0), (0.0, sy)
    else:
        first, second = (0.0, sy), (sx, 0.0)
    if _fits(b1, first[0], first[1], bounds) or not _fits(
        b1, second[0], second[1], bounds
    ):
        return first
    return second


def _point_shift(box, px, py):
    """
    Return the shortest translation ``(sx, sy)`` that moves ``box`` off a point.
    """
    left = px - box[0]
    right = box[2] - px
    down = py - box[1]
    up = box[3] - py
    best = min(left, right, down, up)
    if best == left:
        return left, 0.0
    if best == right:
        return -right, 0.0
    if best == down:
        return 0.0, down
    return 0.0, -up


def _colliding_pairs(boxes, live):
    """
    Indices (i, j), i < j, of every pair of live boxes that currently overlap.

    One vectorised sweep. A k-d tree radius query is asymptotically better and is
    genuinely faster at this step in isolation, but it does not pay for itself
    here: even at 800 labels this sweep is a low single-digit percentage of the
    solve, which is dominated by resolving the collisions it finds. It is not worth
    a SciPy dependency to speed up something that is not the bottleneck.
    """
    x0, y0, x1, y1 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    hit = (
        (x0[:, None] < x1[None, :])
        & (x0[None, :] < x1[:, None])
        & (y0[:, None] < y1[None, :])
        & (y0[None, :] < y1[:, None])
    )
    hit &= live[:, None] & live[None, :]
    return np.argwhere(np.triu(hit, k=1))


def _count_overlaps(boxes, padx, pady) -> int:
    """
    Number of label pairs that visibly overlap, ignoring the padding cushion.
    """
    if len(boxes) < 2:
        return 0
    x0 = boxes[:, 0] + padx
    y0 = boxes[:, 1] + pady
    x1 = boxes[:, 2] - padx
    y1 = boxes[:, 3] - pady
    inter_x = np.minimum(x1[:, None], x1[None, :]) - np.maximum(
        x0[:, None], x0[None, :]
    )
    inter_y = np.minimum(y1[:, None], y1[None, :]) - np.maximum(
        y0[:, None], y0[None, :]
    )
    hits = (inter_x > 0) & (inter_y > 0)
    return int(np.count_nonzero(np.triu(hits, k=1)))


def _crowd_seed(anchors, obstacles, sizes) -> np.ndarray:
    """
    Initial offsets that push every label away from its local crowd.

    Relaxing from the original positions is a purely local search, so a dense
    cluster can settle into a knot that no amount of further iteration undoes.
    Starting from a pre-exploded configuration puts the solver in a different
    basin, which is what the restarts are for.
    """
    crowd = anchors if not len(obstacles) else np.vstack([anchors, obstacles])
    seed = np.zeros_like(anchors)
    for i, point in enumerate(anchors):
        delta = point - crowd  # vectors pointing away from each neighbour
        dist = np.hypot(delta[:, 0], delta[:, 1])
        near = (dist > 1e-9) & (dist < 3 * sizes[i])
        if not np.any(near):
            continue
        # Weight nearer neighbours more heavily, then step out along the escape
        direction = np.sum(delta[near] / dist[near, None] ** 2, axis=0)
        norm = np.hypot(*direction)
        if norm > 1e-9:
            seed[i] = direction / norm * sizes[i]
    return seed


def _artist_points(artist, renderer) -> Optional[np.ndarray]:
    """
    Sample the display-space points an artist occupies, or None if unsupported.
    """
    if isinstance(artist, mlines.Line2D):
        data = artist.get_xydata()
        if data is None or len(data) == 0:
            return None
        return artist.get_transform().transform(np.asarray(data, dtype=float))
    if isinstance(artist, mcollections.PathCollection):
        offsets = artist.get_offsets()
        if offsets is None or len(offsets) == 0:
            return None
        return artist.get_offset_transform().transform(np.asarray(offsets, dtype=float))
    if isinstance(artist, mcollections.LineCollection):
        segs = artist.get_segments()
        if not segs:
            return None
        pts = np.concatenate([np.asarray(s, dtype=float) for s in segs])
        return artist.get_transform().transform(pts)
    return None


def _gather_obstacles(ax, renderer, labels, avoid_points: bool):
    """
    Collect display-space points (data markers/vertices) that labels avoid.
    """
    if not avoid_points:
        return np.empty((0, 2))
    points = []
    for artist in (*ax.lines, *ax.collections):
        if not artist.get_visible() or artist in labels:
            continue
        pts = _artist_points(artist, renderer)
        if pts is not None and len(pts):
            points.append(pts)
    if not points:
        return np.empty((0, 2))
    points = np.concatenate(points)
    finite = np.all(np.isfinite(points), axis=1)
    return points[finite]


def _label_bbox(label, renderer, padx, pady):
    try:
        if isinstance(label, mtext.Annotation):
            # Annotation.get_window_extent() unions the text with its arrow, and
            # the arrow only grows as the label moves away. Measure the box alone.
            label._renderer = renderer
            label.update_positions(renderer)
            bbox = mtext.Text.get_window_extent(label)
        else:
            bbox = label.get_window_extent(renderer=renderer)
    except Exception:
        return None
    if not np.all(np.isfinite(bbox.get_points())):
        return None
    return _expand_bbox(bbox, padx, pady)


def _reset_label(label) -> np.ndarray:
    """
    Restore a label to its user-specified anchor and return that anchor.

    The anchor is cached in the label's own coordinate system the first time we
    see it, so re-running the solver on every draw is idempotent rather than
    cumulative.
    """
    if isinstance(label, mtext.Annotation):
        if not hasattr(label, "_uplt_align_anchor"):
            label._uplt_align_anchor = tuple(label.xyann)
        label.xyann = label._uplt_align_anchor
        return np.asarray(label._uplt_align_anchor, dtype=float)
    if not hasattr(label, "_uplt_align_anchor"):
        label._uplt_align_anchor = tuple(label.get_position())
    label.set_position(label._uplt_align_anchor)
    return np.asarray(label._uplt_align_anchor, dtype=float)


def _text_transform(label, renderer):
    """
    Return the transform mapping a label's stored position to display space.
    """
    if isinstance(label, mtext.Annotation):
        return label._get_xy_transform(renderer, label.anncoords)
    return label.get_transform()


def _move_label(label, delta_display, anchor, transform) -> None:
    """
    Offset a label by ``delta_display`` pixels from its anchor.
    """
    if not np.any(delta_display):
        return
    anchor_display = transform.transform(anchor)
    target = anchor_display + delta_display
    try:
        new = transform.inverted().transform(target)
    except Exception:
        return
    if not np.all(np.isfinite(new)):
        return
    if isinstance(label, mtext.Annotation):
        label.xyann = tuple(new)
    else:
        label.set_position(tuple(new))


def _target_display(label, renderer):
    """
    Display-space point the label refers to (the annotated point, or its anchor).
    """
    if isinstance(label, mtext.Annotation):
        trans = label._get_xy_transform(renderer, label.xycoords)
        return np.asarray(trans.transform(label.xy), dtype=float)
    return np.asarray(
        label.get_transform().transform(label._uplt_align_anchor), dtype=float
    )


def align_text(
    ax,
    labels: Optional[Sequence[mtext.Text]] = None,
    *,
    renderer=None,
    pad: float = 2.0,
    avoid_points: bool = True,
    avoid: Iterable = (),
    only_move: str = "xy",
    max_iter: int = 60,
    spring: float = 0.05,
    step: float = 0.6,
    clip: bool = True,
    arrows: bool | dict = False,
    min_arrow_dist: float = 8.0,
) -> list:
    """
    Nudge text objects until they no longer overlap each other or the data.

    Parameters
    ----------
    ax : ultraplot.axes.Axes
        The axes whose labels are aligned.
    labels : sequence of `~matplotlib.text.Text`, optional
        The labels to move. Default is every text registered for alignment on
        the axes (see `~ultraplot.axes.Axes.text` with ``avoid_overlap=True``).
    pad : float, default: 2.0
        Padding in points added around every label bounding box.
    avoid_points : bool, default: True
        Whether labels also repel the data points of lines and scatter plots.
    avoid : sequence of `~matplotlib.artist.Artist`, optional
        Additional artists (a legend, an inset, ...) whose bounding boxes the
        labels must stay clear of.
    only_move : {'xy', 'x', 'y'}, default: 'xy'
        Restrict movement to a single axis. Useful when the horizontal position
        of a label is meaningful, e.g. labels on a time series.
    max_iter : int, default: 60
        Maximum number of relaxation iterations.
    spring : float, default: 0.05
        Strength of the pull back towards the original anchor. Larger values
        keep labels closer to where they were placed at the cost of overlap.
    step : float, default: 0.6
        Damping applied to each iteration's displacement.
    clip : bool, default: True
        Whether to keep labels inside the axes.
    arrows : bool or dict, default: False
        Whether to draw a connector from displaced labels back to their anchor.
        A dict is passed to `~matplotlib.patches.FancyArrowPatch`.
    min_arrow_dist : float, default: 8.0
        Only draw connectors for labels displaced further than this (in points).

    Returns
    -------
    list
        The connector patches that were drawn, if any.
    """
    if only_move not in ("xy", "x", "y"):
        raise ValueError(f"Invalid only_move={only_move!r}. Choose 'xy', 'x' or 'y'.")
    mask = np.array([float(only_move != "y"), float(only_move != "x")])

    fig = ax.figure
    if fig is None:
        return []
    if renderer is None:
        renderer = fig._get_renderer()
    if labels is None:
        labels = list(getattr(ax, "_align_texts", ()))
    labels = [t for t in labels if t.get_visible() and t.get_text().strip()]
    if not labels:
        return []

    padx = pady = _points_to_pixels(fig, pad)

    # Reset to anchors first so repeated draws converge to the same layout
    anchors = [_reset_label(t) for t in labels]
    transforms = [_text_transform(t, renderer) for t in labels]
    anchor_display = np.array(
        [tr.transform(a) for tr, a in zip(transforms, anchors)], dtype=float
    )

    obstacles = _gather_obstacles(ax, renderer, labels, avoid_points)
    static_bboxes = []
    for artist in avoid:
        try:
            static_bboxes.append(artist.get_window_extent(renderer=renderer))
        except Exception:
            continue

    axes_bbox = ax.get_window_extent(renderer=renderer) if clip else None

    # Measure each label exactly once. Translating a text does not change the size
    # of its bounding box, so every later box is just this one plus an offset --
    # which keeps the whole relaxation in numpy and off the renderer. Keep the raw
    # boxes: the padding cushion is a solver knob, but the score must always be
    # judged on the boxes the reader actually sees.
    raw = []
    for label in labels:
        bbox = _label_bbox(label, renderer, 0, 0)
        raw.append(
            (np.nan, np.nan, np.nan, np.nan)
            if bbox is None
            else (bbox.x0, bbox.y0, bbox.x1, bbox.y1)
        )
    raw = np.array(raw, dtype=float)
    live = np.all(np.isfinite(raw), axis=1)
    order = [i for i in range(len(labels)) if live[i]]

    statics = np.array(
        [(bb.x0, bb.y0, bb.x1, bb.y1) for bb in static_bboxes], dtype=float
    ).reshape(-1, 4)

    obs_x = obstacles[:, 0] if len(obstacles) else np.empty(0)
    obs_y = obstacles[:, 1] if len(obstacles) else np.empty(0)

    def _solve(step, spring, seed=None, cushion=1.0):
        """One relaxation run; returns (score, offsets)."""
        base = raw + cushion * np.array([-padx, -pady, padx, pady])
        offsets = np.zeros((len(labels), 2)) if seed is None else seed * mask
        best_offsets = offsets.copy()
        best_score = (np.inf, np.inf, np.inf)

        for it in range(max_iter):
            boxes = base + np.hstack([offsets, offsets])

            # Score the layout that `offsets` actually produces, on the true boxes,
            # and before the sweep below starts mutating `boxes` in place. Scoring
            # afterwards would rank the provisional fully-resolved state while
            # saving the damped offsets that do not correspond to it.
            overlaps = _count_overlaps(
                (raw + np.hstack([offsets, offsets]))[live], 0.0, 0.0
            )

            # Resolve collisions one at a time, each push applied immediately so that
            # later pairs see the updated box (Gauss-Seidel). Accumulating all the
            # pushes and applying them together lets a label squeezed between two
            # neighbours take equal and opposite shifts that cancel, deadlocking the
            # stack instead of expanding it.
            #
            # This sweep is the hot loop of the whole module, so it runs on plain
            # Python floats. Indexing a row of a numpy array and adding a length-two
            # array to it costs several times the arithmetic it performs.
            work = boxes.tolist()
            fx = [0.0] * len(labels)
            fy = [0.0] * len(labels)
            px_ = [0.0] * len(labels)
            py_ = [0.0] * len(labels)

            def _push(i, sx, sy):
                if sx or sy:
                    fx[i] += sx
                    fy[i] += sy
                    box = work[i]
                    box[0] += sx
                    box[1] += sy
                    box[2] += sx
                    box[3] += sy

            # Points and static artists cannot move, so settle the labels against
            # them first and give label-on-label collisions the last word: a label
            # shoved off a marker must not come to rest on top of a neighbour.
            for i in order:
                for k in range(len(statics)):
                    _push(i, *_overlap_shift(work[i], statics[k], bounds))
                if len(obstacles):
                    b = work[i]
                    inside = (
                        (obs_x > b[0])
                        & (obs_x < b[2])
                        & (obs_y > b[1])
                        & (obs_y < b[3])
                    )
                    for ox, oy in zip(obs_x[inside], obs_y[inside]):
                        _push(i, *_point_shift(work[i], ox, oy))

            # Look for label-on-label collisions only now, so the pairs reflect where
            # the pushes above actually left the labels. One vectorised sweep finds
            # them; the loop then resolves just those. Pairs that a push creates
            # mid-sweep are picked up on the next iteration.
            for i, j in _colliding_pairs(np.array(work), live):
                sx, sy = _overlap_shift(work[i], work[j], bounds)
                if not (sx or sy):
                    continue  # an earlier push in this sweep already separated them
                hx, hy = 0.5 * sx, 0.5 * sy
                px_[i] += hx
                py_[i] += hy
                px_[j] -= hx
                py_[j] -= hy
                _push(i, hx, hy)
                _push(j, -hx, -hy)

            forces = np.column_stack([fx, fy])
            pair_forces = np.column_stack([px_, py_])

            # Rank on the overlap count taken above: what the eye objects to is
            # labels sitting on each other, so that comes first and sitting on a
            # marker is only a tie-break. Ranking on the summed force instead would
            # let a state with stacked labels but clear markers beat the reverse.
            crowding = float(np.sum(np.hypot(pair_forces[:, 0], pair_forces[:, 1])))
            displacement = float(np.sum(np.hypot(offsets[:, 0], offsets[:, 1])))
            score = (overlaps, crowding, displacement)
            if score < best_score:
                best_score = score
                best_offsets = offsets.copy()
            if not forces.any():
                break

            # Pull labels that are already free back towards their anchor. Springing
            # a colliding label would merely balance the repulsion and leave the
            # overlap in place. Fade the spring out so late iterations prioritise
            # separation over staying close to the anchor.
            free = ~np.any(forces, axis=1)
            forces[free] -= spring * (1 - it / max_iter) * offsets[free]
            forces *= mask
            offsets = offsets + step * forces

            if bounds is not None:
                boxes = base + np.hstack([offsets, offsets])
                lo = bounds[:2] - boxes[:, :2]
                hi = bounds[2:] - boxes[:, 2:]
                nudge = np.clip(0.0, np.minimum(lo, hi), np.maximum(lo, hi))
                offsets += np.where(live[:, None], nudge * mask, 0.0)

        return best_score, best_offsets

    bounds = (
        None
        if axes_bbox is None
        else np.array([axes_bbox.x0, axes_bbox.y0, axes_bbox.x1, axes_bbox.y1])
    )

    # No single relaxation schedule wins on every layout: a decisive step clears
    # dense stacks but can overshoot into a worse arrangement, a gentle one does
    # the reverse, and relaxing from the original positions cannot always escape a
    # knotted cluster at all. The solve is cheap now that nothing re-measures, so
    # run a handful and keep the best. The schedules are fixed rather than random,
    # so the same figure always lands on the same layout.
    centres = 0.5 * (raw[:, :2] + raw[:, 2:])
    sizes = 0.5 * np.hypot(raw[:, 2] - raw[:, 0], raw[:, 3] - raw[:, 1])
    seed = _crowd_seed(np.nan_to_num(centres), obstacles, np.nan_to_num(sizes))

    schedules = [
        (step, spring, None, 1.0),
        (1.0, spring, None, 1.0),
        (step, spring, seed, 1.0),
        (1.0, 0.0, seed, 1.0),
        (step, spring, None, 1.5),
        (step, spring, None, 0.5),
        (0.4, 0.5 * spring, None, 1.0),
    ]
    # Each restart costs a full relaxation. Past a few hundred labels they cannot
    # all fit anyway, so the restarts buy nothing but seconds of redraw time.
    if len(order) > _RESTART_LIMIT:
        schedules = schedules[:2]

    offsets = None
    best = (np.inf, np.inf, np.inf)
    for step_i, spring_i, seed_i, cushion_i in schedules:
        score, candidate = _solve(step_i, spring_i, seed_i, cushion_i)
        if score < best:
            best, offsets = score, candidate
        if best[0] == 0:
            break  # nothing overlaps any more; no need to try the rest

    # Apply the final offsets
    for label, anchor, trans, offset in zip(labels, anchors, transforms, offsets):
        _move_label(label, offset, anchor, trans)

    # Connectors from displaced labels back to what they describe
    patches = []
    for patch in getattr(ax, "_align_arrows", ()):
        try:
            patch.remove()
        except Exception:
            pass
    ax._align_arrows = patches
    if not arrows:
        return patches
    props = dict(arrowstyle="-", color="0.5", linewidth=0.8, shrinkA=2, shrinkB=2)
    if isinstance(arrows, dict):
        props.update(arrows)
    threshold = _points_to_pixels(fig, min_arrow_dist)
    inv = ax.transData.inverted()
    for label, offset in zip(labels, offsets):
        if np.hypot(*offset) < threshold:
            continue
        if isinstance(label, mtext.Annotation) and label.arrowprops:
            continue  # matplotlib already draws this one
        target = _target_display(label, renderer)
        bbox = _label_bbox(label, renderer, 0, 0)
        if bbox is None:
            continue
        center = np.array([0.5 * (bbox.x0 + bbox.x1), 0.5 * (bbox.y0 + bbox.y1)])
        patch = mpatches.FancyArrowPatch(
            posA=inv.transform(center),
            posB=inv.transform(target),
            transform=ax.transData,
            zorder=label.get_zorder() - 0.1,
            **props,
        )
        # add_artist, not add_patch: a connector is decoration, and letting it
        # widen the data limits would move the very labels it is drawn from,
        # changing the layout on every redraw.
        ax.add_artist(patch)
        patch.set_clip_path(ax.patch)
        patches.append(patch)
    return patches
