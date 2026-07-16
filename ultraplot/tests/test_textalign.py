#!/usr/bin/env python3
"""
Test automatic alignment of overlapping text and annotations.
"""

import numpy as np
import pytest

import ultraplot as uplt
from ultraplot.textalign import _label_bbox


def _count_overlaps(fig, texts) -> int:
    # Measure the text box alone: an Annotation's window extent also covers its
    # arrow, which legitimately crosses other labels.
    renderer = fig._get_renderer()
    bboxes = [_label_bbox(t, renderer, 0, 0) for t in texts]
    return sum(
        bboxes[i].overlaps(bboxes[j])
        for i in range(len(bboxes))
        for j in range(i + 1, len(bboxes))
    )


@pytest.fixture
def crowded():
    """Points clustered tightly enough that their labels collide."""
    rng = np.random.default_rng(0)
    x = np.concatenate([rng.normal(c, 0.12, 12) for c in (0.3, 0.7)])
    y = np.concatenate([rng.normal(c, 0.12, 12) for c in (0.4, 0.6)])
    return x, y, [f"sample {i}" for i in range(len(x))]


def test_overlapping_text_is_separated(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    texts = [ax.text(*xy, nm, fontsize=7) for *xy, nm in zip(x, y, names)]
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) > 0

    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) == 0


def test_align_is_idempotent_across_draws(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    fig.canvas.draw()
    first = np.array([t.get_position() for t in texts])
    fig.canvas.draw()
    second = np.array([t.get_position() for t in texts])
    assert np.array_equal(first, second)


def test_align_survives_resize(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    fig.canvas.draw()
    fig.set_size_inches(12, 4)
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) == 0


def test_auto_align_text_collects_untagged_text(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    texts = [ax.text(*xy, nm, fontsize=7) for *xy, nm in zip(x, y, names)]
    assert ax.auto_align_text() == texts
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) == 0


def test_only_move_preserves_other_axis(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    ax.auto_align_text(only_move="y", avoid_points=False)
    fig.canvas.draw()
    assert np.allclose([t.get_position()[0] for t in texts], x)
    assert not np.allclose([t.get_position()[1] for t in texts], y)


def test_rc_opt_in(crowded):
    x, y, names = crowded
    with uplt.rc.context({"text.align": True}):
        fig, axs = uplt.subplots()
        ax = axs[0]
        texts = [ax.text(*xy, nm, fontsize=7) for *xy, nm in zip(x, y, names)]
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) == 0


def test_off_by_default(crowded):
    """Nothing moves unless you ask for it."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    texts = [ax.text(*xy, nm, fontsize=7) for *xy, nm in zip(x, y, names)]
    fig.canvas.draw()
    assert np.allclose([t.get_position() for t in texts], np.column_stack([x, y]))
    assert _count_overlaps(fig, texts) > 0


def test_per_label_opt_out_beats_rc(crowded):
    """avoid_overlap=False wins even when the rc setting turns alignment on."""
    x, y, names = crowded
    with uplt.rc.context({"text.align": True}):
        fig, axs = uplt.subplots()
        ax = axs[0]
        kept = ax.text(x[0], y[0], names[0], fontsize=7, avoid_overlap=False)
        moved = [
            ax.text(*xy, nm, fontsize=7) for *xy, nm in zip(x[1:], y[1:], names[1:])
        ]
    fig.canvas.draw()
    assert kept not in ax._align_texts
    assert kept.get_position() == (x[0], y[0])
    assert any(t.get_position() != xy for t, xy in zip(moved, zip(x[1:], y[1:])))


def test_opting_out_restores_position(crowded):
    """Releasing a label puts it back where the user asked for it."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    text = ax.text(x[0], y[0], names[0], fontsize=7, avoid_overlap=True)
    for xi, yi, nm in zip(x[1:], y[1:], names[1:]):
        ax.text(xi, yi, nm, fontsize=7, avoid_overlap=True)
    fig.canvas.draw()
    assert text.get_position() != (x[0], y[0])  # the solver moved it
    ax._register_align_text(text, False)
    assert text.get_position() == (x[0], y[0])


def test_annotations_are_aligned(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    anns = [
        ax.annotate(
            nm,
            xy=(xi, yi),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            arrowprops=dict(arrowstyle="-"),
            avoid_overlap=True,
        )
        for xi, yi, nm in zip(x, y, names)
    ]
    fig.canvas.draw()
    assert _count_overlaps(fig, anns) == 0
    # The arrow still points at the annotated data point
    assert np.allclose([a.xy for a in anns], np.column_stack([x, y]))


def test_arrows_connect_displaced_labels(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    for xi, yi, nm in zip(x, y, names):
        ax.text(xi, yi, nm, fontsize=7, avoid_overlap=True)
    ax.auto_align_text(arrows=True, min_arrow_dist=0)
    fig.canvas.draw()
    assert len(ax._align_arrows) > 0
    # Redrawing replaces the connectors rather than piling up new ones
    count = len(ax._align_arrows)
    fig.canvas.draw()
    assert len(ax._align_arrows) == count


def test_arrows_do_not_disturb_data_limits(crowded):
    """Connectors are decoration; they must not widen the axes."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    fig.canvas.draw()
    before = (ax.get_xlim(), ax.get_ylim())
    for xi, yi, nm in zip(x, y, names):
        ax.text(xi, yi, nm, fontsize=7, avoid_overlap=True)
    ax.auto_align_text(arrows=True, min_arrow_dist=0)
    fig.canvas.draw()
    assert (ax.get_xlim(), ax.get_ylim()) == before


def test_labels_stay_inside_axes(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    for xi, yi, nm in zip(x, y, names):
        ax.text(xi, yi, nm, fontsize=7, avoid_overlap=True)
    fig.canvas.draw()
    renderer = fig._get_renderer()
    axes_bbox = ax.get_window_extent(renderer=renderer)
    for text in ax._align_texts:
        bbox = text.get_window_extent(renderer=renderer)
        assert axes_bbox.x0 - 1 <= bbox.x0 and bbox.x1 <= axes_bbox.x1 + 1
        assert axes_bbox.y0 - 1 <= bbox.y0 and bbox.y1 <= axes_bbox.y1 + 1


def test_invalid_only_move_raises():
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.text(0.5, 0.5, "a", avoid_overlap=True)
    ax.text(0.5, 0.5, "b", avoid_overlap=True)
    with pytest.raises(ValueError, match="only_move"):
        uplt.align_text(ax, only_move="z")


def test_log_scale_labels(crowded):
    """Movement is computed in pixels, so nonlinear transforms are fine."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.format(yscale="log")
    texts = [
        ax.text(xi, 10**yi, nm, fontsize=7, avoid_overlap=True)
        for xi, yi, nm in zip(x, y, names)
    ]
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) == 0


# --------------------------------------------------------------------------
# Obstacle types: labels repel the data, whichever artist drew it
# --------------------------------------------------------------------------


def _labels_clear_of(fig, texts, points):
    """No label box contains any of the given display-space points."""
    renderer = fig._get_renderer()
    for text in texts:
        bbox = _label_bbox(text, renderer, 0, 0)
        for px, py in points:
            if bbox.x0 < px < bbox.x1 and bbox.y0 < py < bbox.y1:
                return False
    return True


def test_labels_avoid_line_markers():
    """A Line2D contributes its vertices as obstacles, not just scatter."""
    x = np.linspace(0, 1, 12)
    y = np.full_like(x, 0.5)
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.plot(x, y, marker="o")
    texts = [
        ax.text(xi, yi, f"p{i}", fontsize=7, avoid_overlap=True)
        for i, (xi, yi) in enumerate(zip(x, y))
    ]
    fig.canvas.draw()
    pts = ax.transData.transform(np.column_stack([x, y]))
    assert _labels_clear_of(fig, texts, pts)


def test_labels_avoid_line_collection():
    import matplotlib.collections as mcollections

    segs = [[(0.1, 0.5), (0.9, 0.5)], [(0.1, 0.6), (0.9, 0.6)]]
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.add_collection(mcollections.LineCollection(segs))
    texts = [
        ax.text(0.5, 0.5, "a", fontsize=7, avoid_overlap=True),
        ax.text(0.5, 0.6, "b", fontsize=7, avoid_overlap=True),
    ]
    fig.canvas.draw()
    pts = ax.transData.transform(np.array([p for s in segs for p in s]))
    assert _labels_clear_of(fig, texts, pts)


def test_hidden_artists_are_not_obstacles():
    """An invisible line should not push labels around."""
    x = np.linspace(0.2, 0.8, 8)
    y = np.full_like(x, 0.5)
    fig, axs = uplt.subplots()
    ax = axs[0]
    line = ax.plot(x, y, marker="o")[0]
    line.set_visible(False)
    text = ax.text(0.5, 0.5, "solo", fontsize=7, avoid_overlap=True)
    fig.canvas.draw()
    assert text.get_position() == (0.5, 0.5)  # nothing to avoid, nothing moved


def test_avoid_points_false_ignores_data(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    text = ax.text(x[0], y[0], names[0], fontsize=7, avoid_overlap=True)
    ax.auto_align_text(text, avoid_points=False)
    fig.canvas.draw()
    # The only label has nothing to collide with once the markers are ignored
    assert text.get_position() == (x[0], y[0])


# --------------------------------------------------------------------------
# Solver options
# --------------------------------------------------------------------------


def test_avoid_keeps_labels_off_a_given_artist():
    """The `avoid` argument treats an arbitrary artist as immovable."""
    fig, axs = uplt.subplots()
    ax = axs[0]
    blocker = ax.text(0.5, 0.5, "BLOCKER", fontsize=20)
    text = ax.text(0.5, 0.5, "moved", fontsize=7, avoid_overlap=True)
    ax.auto_align_text(text, avoid=[blocker], avoid_points=False)
    fig.canvas.draw()
    renderer = fig._get_renderer()
    assert not _label_bbox(text, renderer, 0, 0).overlaps(
        blocker.get_window_extent(renderer=renderer)
    )


def test_clip_false_changes_the_layout(crowded):
    """Without clipping the solver is free to push labels past the axes edge."""
    x, y, names = crowded

    def solve(clip):
        fig, axs = uplt.subplots()
        ax = axs[0]
        ax.scatter(x, y)
        texts = [
            ax.text(*xy, nm, fontsize=7, avoid_overlap=True)
            for *xy, nm in zip(x, y, names)
        ]
        ax.auto_align_text(clip=clip)
        fig.canvas.draw()
        return np.array([t.get_position() for t in texts])

    clipped, free = solve(True), solve(False)
    assert not np.allclose(clipped, free)


def test_only_move_x_preserves_y(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    ax.auto_align_text(only_move="x", avoid_points=False)
    fig.canvas.draw()
    assert np.allclose([t.get_position()[1] for t in texts], y)
    assert not np.allclose([t.get_position()[0] for t in texts], x)


def test_many_labels_use_the_reduced_schedule(crowded):
    """Past the restart limit the solver still runs and still separates labels."""
    from ultraplot.textalign import _RESTART_LIMIT

    n = _RESTART_LIMIT + 10
    rng = np.random.default_rng(3)
    x, y = rng.random(n), rng.random(n)
    fig, axs = uplt.subplots(refwidth=8)
    ax = axs[0]
    texts = [
        ax.text(xi, yi, f"p{i}", fontsize=5, avoid_overlap=True)
        for i, (xi, yi) in enumerate(zip(x, y))
    ]
    before = _count_overlaps(fig, texts)
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) < before


# --------------------------------------------------------------------------
# Connectors
# --------------------------------------------------------------------------


def test_arrow_style_dict_is_forwarded(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    for xi, yi, nm in zip(x, y, names):
        ax.text(xi, yi, nm, fontsize=7, avoid_overlap=True)
    ax.auto_align_text(arrows=dict(color="red", linewidth=2.0), min_arrow_dist=0)
    fig.canvas.draw()
    assert ax._align_arrows
    patch = ax._align_arrows[0]
    assert patch.get_linewidth() == 2.0
    assert uplt.colors.to_hex(patch.get_edgecolor()) == uplt.colors.to_hex("red")


def test_no_connector_for_annotations_with_their_own_arrow(crowded):
    """matplotlib already draws that arrow; we must not double it."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    for xi, yi, nm in zip(x, y, names):
        ax.annotate(
            nm,
            xy=(xi, yi),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            arrowprops=dict(arrowstyle="-"),
            avoid_overlap=True,
        )
    ax.auto_align_text(arrows=True, min_arrow_dist=0)
    fig.canvas.draw()
    assert ax._align_arrows == []


def test_connector_points_at_the_annotated_point(crowded):
    """An annotation without arrowprops still gets a connector to its xy."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    for xi, yi, nm in zip(x, y, names):
        ax.annotate(
            nm,
            xy=(xi, yi),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            avoid_overlap=True,
        )
    ax.auto_align_text(arrows=True, min_arrow_dist=0)
    fig.canvas.draw()
    assert ax._align_arrows
    targets = {tuple(np.round(p.get_path().vertices[-1], 6)) for p in ax._align_arrows}
    assert targets & {tuple(np.round(xy, 6)) for xy in zip(x, y)}


def test_min_arrow_dist_suppresses_short_connectors(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    for xi, yi, nm in zip(x, y, names):
        ax.text(xi, yi, nm, fontsize=7, avoid_overlap=True)
    ax.auto_align_text(arrows=True, min_arrow_dist=10_000)
    fig.canvas.draw()
    assert ax._align_arrows == []


# --------------------------------------------------------------------------
# Edge cases
# --------------------------------------------------------------------------


def test_no_labels_is_a_noop():
    fig, axs = uplt.subplots()
    ax = axs[0]
    assert uplt.align_text(ax) == []


def test_blank_and_hidden_labels_are_skipped():
    fig, axs = uplt.subplots()
    ax = axs[0]
    blank = ax.text(0.5, 0.5, "   ", avoid_overlap=True)
    hidden = ax.text(0.5, 0.5, "hidden", avoid_overlap=True)
    hidden.set_visible(False)
    fig.canvas.draw()
    assert blank.get_position() == (0.5, 0.5)
    assert hidden.get_position() == (0.5, 0.5)


def test_single_label_never_moves():
    fig, axs = uplt.subplots()
    ax = axs[0]
    text = ax.text(0.5, 0.5, "alone", avoid_overlap=True)
    fig.canvas.draw()
    assert text.get_position() == (0.5, 0.5)


def test_align_text_without_a_renderer(crowded):
    """Called directly, the solver fetches its own renderer."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    uplt.align_text(ax)  # no renderer= passed
    assert _count_overlaps(fig, texts) == 0


def test_solver_failure_warns_but_still_draws(crowded, monkeypatch):
    """A broken solve must never take the whole figure down with it."""
    import ultraplot.textalign as textalign
    from ultraplot.internals.warnings import UltraPlotWarning

    def boom(*args, **kwargs):
        raise RuntimeError("solver exploded")

    monkeypatch.setattr(textalign, "align_text", boom)
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.text(x[0], y[0], names[0], avoid_overlap=True)
    with pytest.warns(UltraPlotWarning, match="auto-align"):
        fig.canvas.draw()
    assert ax.texts  # the label is still there, just unaligned


def test_auto_align_text_accepts_an_iterable(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    texts = [ax.text(*xy, nm, fontsize=7) for *xy, nm in zip(x, y, names)]
    assert ax.auto_align_text(texts) == texts  # a list, not *args
    fig.canvas.draw()
    assert _count_overlaps(fig, texts) == 0


def test_moving_a_label_by_hand_re_anchors_it(crowded):
    """set_position() after a draw must not be undone by the next one."""
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    fig.canvas.draw()
    text = texts[0]
    solved = np.array(text.get_position())  # where the solver had parked it
    text.set_position((0.05, 0.95))
    fig.canvas.draw()

    assert text._uplt_align_anchor == (0.05, 0.95)
    # The solver may still nudge it, but it now relaxes away from where the user
    # put it rather than from the anchor the user has abandoned
    now = np.array(text.get_position())
    assert np.hypot(*(now - [0.05, 0.95])) < np.hypot(*(now - solved))
    assert _count_overlaps(fig, texts) == 0


def test_three_axes_text_is_left_alone():
    """A Text3D is placed by the projection, so a display-space nudge is meaningless."""
    fig = uplt.figure()
    ax = fig.subplot(proj="3d")
    text = ax.text(0.5, 0.5, 0.5, "label", avoid_overlap=True)
    other = ax.text(0.5, 0.5, 0.5, "overlapping", avoid_overlap=True)
    fig.canvas.draw()
    assert ax._align_texts == []
    assert text.get_position() == (0.5, 0.5)
    assert other.get_position() == (0.5, 0.5)


def test_unchanged_redraw_reuses_the_solve(crowded, monkeypatch):
    """A redraw that changes nothing must not pay for the relaxation again."""
    import ultraplot.textalign as textalign

    calls = []
    seed = textalign._crowd_seed  # only reached on a full solve, never on a cache hit
    monkeypatch.setattr(
        textalign,
        "_crowd_seed",
        lambda *args, **kwargs: (calls.append(1), seed(*args, **kwargs))[1],
    )
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    fig.canvas.draw()
    assert calls  # solved at least once
    before = np.array([t.get_position() for t in texts])

    calls.clear()
    fig.canvas.draw()
    assert not calls  # ... and reused it, rather than solving again
    assert np.array_equal([t.get_position() for t in texts], before)

    # A resize changes every box in display space, so the cache must not survive it
    fig.set_size_inches(12, 4)
    fig.canvas.draw()
    assert calls
    assert _count_overlaps(fig, texts) == 0


def test_releasing_every_label_removes_the_connectors(crowded):
    x, y, names = crowded
    fig, axs = uplt.subplots()
    ax = axs[0]
    ax.scatter(x, y)
    texts = [
        ax.text(*xy, nm, fontsize=7, avoid_overlap=True) for *xy, nm in zip(x, y, names)
    ]
    ax.auto_align_text(arrows=True, min_arrow_dist=0)
    fig.canvas.draw()
    patches = list(ax._align_arrows)
    assert patches
    for text in texts:
        ax._register_align_text(text, False)
    fig.canvas.draw()
    assert ax._align_arrows == []
    assert not any(p in ax.artists for p in patches)
