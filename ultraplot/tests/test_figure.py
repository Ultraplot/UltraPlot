import multiprocessing as mp
import os
import warnings
from datetime import datetime, timedelta

import numpy as np
import pytest
import ultraplot as uplt


def test_unsharing_after_creation(rng):
    """
    By default UltraPlot shares the axes. We test here if
    we can unshare them after we create the figure. This
    is used on the GeoAxes when the plot contains both
    rectilinear and non-rectilinear axes.
    """
    fig, ax = uplt.subplots(ncols=3, nrows=3, share="all")
    fig._unshare_axes()
    # This should be reset
    assert fig._sharey == False
    assert fig._sharex == False
    for axi in ax:
        # This should be reset
        assert axi._sharey is None
        assert axi._sharex is None
        # Also check the actual grouper
        for which, grouper in axi._shared_axes.items():
            siblings = list(grouper.get_siblings(axi))
            assert len(siblings) == 1

    # Test that the lims are different after unsharing
    base_data = rng.random((2, 100))
    ax[0].scatter(*base_data)
    xlim1 = np.array(ax[0].get_xlim())
    for idx in range(1, 4):
        data = base_data + idx * 100
        ax[idx].scatter(*data)
        xlim2 = np.array(ax[idx].get_xlim())
        l2_norm = np.linalg.norm(xlim1 - xlim2)
        assert not np.allclose(l2_norm, 0)


def test_unsharing_on_creation():
    """
    Test that figure sharing is disabled by default.
    """
    fig, ax = uplt.subplots(ncols=3, nrows=3, share=0)
    assert fig._sharey == False
    assert fig._sharex == False
    for axi in ax:
        # This should be reset
        assert axi._sharey is None
        assert axi._sharex is None
        # Also check the actual grouper
        for which, grouper in axi._shared_axes.items():
            siblings = list(grouper.get_siblings(axi))
            assert len(siblings) == 1
            assert axi in siblings


def test_unsharing_different_rectilinear():
    """
    Even if the projections are rectilinear, the coordinates systems may be different, as such we only allow sharing for the same kind of projections.
    """
    with pytest.warns(uplt.internals.warnings.UltraPlotWarning):
        fig, ax = uplt.subplots(ncols=2, proj=("cyl", "merc"), share="all")


def test_get_renderer_basic():
    """
    Test that _get_renderer returns a renderer object.
    """
    fig, ax = uplt.subplots()
    renderer = fig._get_renderer()
    # Renderer should not be None and should have draw_path method
    assert renderer is not None
    assert hasattr(renderer, "draw_path")


def test_draw_without_rendering_preserves_dpi():
    """
    draw_without_rendering should not mutate figure dpi/bbox.
    """
    fig, ax = uplt.subplots(figsize=(4, 3), dpi=101)
    dpi_before = fig.dpi
    bbox_before = np.array([fig.bbox.width, fig.bbox.height])

    fig.draw_without_rendering()

    assert np.isclose(fig.dpi, dpi_before)
    assert np.allclose([fig.bbox.width, fig.bbox.height], bbox_before)
    uplt.close(fig)


def test_figure_sharing_toggle():
    """
    Check if axis sharing and unsharing works
    """

    def compare_with_reference(layout):
        # Create reference
        ref_data = np.array([[0, 100], [0, 200]])
        ref_fig, ref_ax = uplt.subplots(layout.copy(), share=1)
        ref_ax.plot(*ref_data)
        ref_fig.suptitle("Reference")

        # Create "toggled" figure
        fig, ax = uplt.subplots(layout.copy(), share=1)
        fig.suptitle("Toggler")
        # We create a figure with sharing, then toggle it
        # to see if we can update the axis
        fig._toggle_axis_sharing(which="x", share=False)
        fig._toggle_axis_sharing(which="y", share=False)
        for axi in ax:
            assert axi._sharex is None
            assert axi._sharey is None
            for which in "xy":
                siblings = axi._shared_axes[which].get_siblings(axi)
                assert len(list(siblings)) == 1
                assert axi in siblings

        fig._toggle_axis_sharing(which="x", share=True)
        fig._toggle_axis_sharing(which="y", share=True)
        ax.plot(*ref_data)

        for ref, axi in zip(ref_ax, ax):
            for which in "xy":
                ref_axi = getattr(ref, f"_share{which}")
                axi = getattr(ref, f"_share{which}")
                if ref_axi is None:
                    assert ref_axi == axi
                else:
                    assert ref_axi.number == axi.number
                    ref_lim = getattr(ref_axi, f"{which}axis").get_view_interval()
                    lim = getattr(axi, f"{which}axis").get_view_interval()
                    l1 = np.linalg.norm(np.asarray(ref_lim) - np.asarray(lim))
                    assert np.allclose(l1, 0)

        for f in [fig, ref_fig]:
            uplt.close(f)

    # Create a reference
    gs = uplt.gridspec.GridSpec(ncols=3, nrows=3)
    compare_with_reference(gs)

    layout = [
        [1, 2, 0],
        [1, 2, 5],
        [3, 4, 5],
        [3, 4, 0],
    ]
    compare_with_reference(layout)

    layout = [
        [1, 0, 2],
        [0, 3, 0],
        [5, 0, 6],
    ]
    compare_with_reference(layout)

    return None


def test_toggle_input_axis_sharing():
    fig = uplt.figure()
    with pytest.warns(uplt.internals.warnings.UltraPlotWarning):
        fig._toggle_axis_sharing(which="does not exist")


def _layout_signature() -> tuple:
    fig, ax = uplt.subplots(ncols=2, nrows=2)
    for axi in ax:
        axi.plot([0, 1], [0, 1], label="line")
        axi.set_xlabel("X label")
        axi.set_ylabel("Y label")
    fig.suptitle("Title")
    fig.legend()
    fig.canvas.draw()
    signature = tuple(
        tuple(np.round(axi.get_position().bounds, 6))
        for axi in fig.axes
        if axi.get_visible()
    )
    uplt.close(fig)
    return signature


def _layout_worker(queue):
    queue.put(_layout_signature())


def test_layout_deterministic_across_runs():
    """
    Layout should be deterministic for identical inputs.
    """
    positions = [_layout_signature() for _ in range(3)]
    assert all(p == positions[0] for p in positions)

    # Probe mode: exercise multiple processes to catch nondeterminism.
    if os.environ.get("ULTRAPLOT_LAYOUT_PROBE") == "1":
        ctx = mp.get_context("spawn")
        queue = ctx.Queue()
        workers = [ctx.Process(target=_layout_worker, args=(queue,)) for _ in range(4)]
        for proc in workers:
            proc.start()
        proc_positions = [queue.get() for _ in workers]
        for proc in workers:
            proc.join()
        assert all(p == proc_positions[0] for p in proc_positions)


def test_suptitle_alignment():
    """
    Test that suptitle uses the original centering behavior with includepanels parameter.
    """
    # Test 1: Default behavior uses original centering algorithm
    fig1, ax1 = uplt.subplots(ncols=3)
    for ax in ax1:
        ax.panel("top", width="1em")  # Add panels
    fig1.suptitle("Default")
    fig1.canvas.draw()  # Trigger alignment
    pos1 = fig1._suptitle.get_position()

    # Test 2: includepanels=False should use original centering behavior
    fig2, ax2 = uplt.subplots(ncols=3, includepanels=False)
    for ax in ax2:
        ax.panel("top", width="1em")  # Add panels
    fig2.suptitle("includepanels=False")
    fig2.canvas.draw()  # Trigger alignment
    pos2 = fig2._suptitle.get_position()

    # Test 3: includepanels=True should use original centering behavior
    fig3, ax3 = uplt.subplots(ncols=3, includepanels=True)
    for ax in ax3:
        ax.panel("top", width="1em")  # Add panels
    fig3.suptitle("includepanels=True")
    fig3.canvas.draw()  # Trigger alignment
    pos3 = fig3._suptitle.get_position()

    # With reverted behavior, all use the same original centering algorithm
    # Note: In the original code, includepanels didn't actually affect suptitle positioning
    assert (
        abs(pos1[0] - pos2[0]) < 0.001
    ), f"Default and includepanels=False should be same: {pos1[0]} vs {pos2[0]}"

    assert (
        abs(pos2[0] - pos3[0]) < 0.001
    ), f"includepanels=False and True should be same with reverted behavior: {pos2[0]} vs {pos3[0]}"

    uplt.close("all")


import pytest


@pytest.mark.parametrize(
    "suptitle, suptitle_kw, expected_ha, expected_va",
    [
        ("Default alignment", {}, "center", "bottom"),  # Test 1: Default alignment
        (
            "Left aligned",
            {"ha": "left"},
            "left",
            "bottom",
        ),  # Test 2: Custom horizontal alignment
        (
            "Top aligned",
            {"va": "top"},
            "center",
            "top",
        ),  # Test 3: Custom vertical alignment
        (
            "Custom aligned",
            {"ha": "right", "va": "top"},
            "right",
            "top",
        ),  # Test 4: Both custom alignments
    ],
)
def test_suptitle_kw_alignment(suptitle, suptitle_kw, expected_ha, expected_va):
    """
    Test that suptitle_kw alignment parameters work correctly and are not overridden.
    """
    fig, ax = uplt.subplots()
    fig.format(suptitle=suptitle, suptitle_kw=suptitle_kw)
    fig.canvas.draw()
    assert (
        fig._suptitle.get_ha() == expected_ha
    ), f"Expected ha={expected_ha}, got {fig._suptitle.get_ha()}"
    assert (
        fig._suptitle.get_va() == expected_va
    ), f"Expected va={expected_va}, got {fig._suptitle.get_va()}"


@pytest.mark.parametrize(
    "ha, expectation",
    [
        ("left", 0),
        ("center", 0.5),
        ("right", 1),
    ],
)
def test_suptitle_kw_position_reverted(ha, expectation):
    """
    Test that position remains the same while alignment properties differ.
    """
    fig, ax = uplt.subplots(ncols=3)
    fig.format(suptitle=ha, suptitle_kw=dict(ha=ha))
    fig.canvas.draw()  # trigger alignment
    x, y = fig._suptitle.get_position()

    # Note values are dynamic so atol is a bit wide here
    assert np.isclose(x, expectation, atol=0.1), f"Expected x={expectation}, got {x=}"

    uplt.close("all")


def _share_sibling_count(ax, which: str) -> int:
    return len(list(ax._shared_axes[which].get_siblings(ax)))


def test_default_share_mode_is_auto():
    fig, axs = uplt.subplots(ncols=2)
    assert fig._sharex_auto is True
    assert fig._sharey_auto is True


def test_auto_share_skips_mixed_cartesian_polar_without_warning(recwarn):
    fig, axs = uplt.subplots(ncols=2, proj=("cart", "polar"), share="auto")

    ultra_warnings = [
        w
        for w in recwarn
        if issubclass(w.category, uplt.internals.warnings.UltraPlotWarning)
    ]
    assert len(ultra_warnings) == 0

    for which in ("x", "y"):
        assert _share_sibling_count(axs[0], which) == 1
        assert _share_sibling_count(axs[1], which) == 1


def test_explicit_share_warns_for_mixed_cartesian_polar():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", uplt.internals.warnings.UltraPlotWarning)
        fig, axs = uplt.subplots(ncols=2, proj=("cart", "polar"), share="all")
    incompatible = [
        w
        for w in record
        if issubclass(w.category, uplt.internals.warnings.UltraPlotWarning)
        and "Skipping incompatible" in str(w.message)
    ]
    assert len(incompatible) == 1


def test_share_zero_polar_emits_no_warnings(recwarn):
    fig, axs = uplt.subplots(proj="polar", ncols=2, nrows=3, share=0)
    fig.canvas.draw()

    ultra = [
        w
        for w in recwarn
        if issubclass(w.category, uplt.internals.warnings.UltraPlotWarning)
    ]
    assert ultra == [], [str(w.message) for w in ultra]


def test_share_zero_mixed_cartesian_polar_emits_no_warnings(recwarn):
    fig, axs = uplt.subplots(ncols=2, proj=("cart", "polar"), share=0)
    fig.canvas.draw()

    ultra = [
        w
        for w in recwarn
        if issubclass(w.category, uplt.internals.warnings.UltraPlotWarning)
    ]
    assert ultra == [], [str(w.message) for w in ultra]


def test_share_default_single_polar_emits_no_warnings(recwarn):
    """A single polar axis has nothing to share — must not warn at default share."""
    fig, ax = uplt.subplots(proj="polar")
    fig.canvas.draw()

    ultra = [
        w
        for w in recwarn
        if issubclass(w.category, uplt.internals.warnings.UltraPlotWarning)
    ]
    assert ultra == [], [str(w.message) for w in ultra]


def test_share_default_single_polar_subplot_singular_emits_no_warnings(recwarn):
    """``uplt.subplot(proj='polar')`` (singular) has nothing to share either."""
    fig, ax = uplt.subplot(proj="polar")
    fig.canvas.draw()

    ultra = [
        w
        for w in recwarn
        if issubclass(w.category, uplt.internals.warnings.UltraPlotWarning)
    ]
    assert ultra == [], [str(w.message) for w in ultra]


def test_auto_share_local_yscale_change_splits_group():
    fig, axs = uplt.subplots(ncols=2, share="auto")
    fig.canvas.draw()

    assert _share_sibling_count(axs[0], "y") == 2
    assert _share_sibling_count(axs[1], "y") == 2

    axs[0].format(yscale="log")
    fig.canvas.draw()

    assert axs[0].get_yscale() == "log"
    assert axs[1].get_yscale() == "linear"
    assert _share_sibling_count(axs[0], "y") == 1
    assert _share_sibling_count(axs[1], "y") == 1


def test_auto_share_grid_yscale_change_keeps_shared_limits():
    fig, axs = uplt.subplots(ncols=2, share="auto")
    x = np.linspace(1, 10, 100)
    axs[0].plot(x, x)
    axs[1].plot(x, 100 * x)

    axs.format(yscale="log")
    fig.canvas.draw()

    assert _share_sibling_count(axs[0], "y") == 2
    assert _share_sibling_count(axs[1], "y") == 2

    ymin, ymax = axs[0].get_ylim()
    assert ymax > 500
    assert ymin > 0


def test_auto_share_splits_mixed_x_unit_domains_after_refresh():
    fig, axs = uplt.subplots(ncols=2, share="auto")
    fig.canvas.draw()

    # Start from independent x groups so each axis can establish units separately.
    for axi in axs:
        axi._unshare(which="x")
    assert _share_sibling_count(axs[0], "x") == 1
    assert _share_sibling_count(axs[1], "x") == 1

    t0 = datetime(2020, 1, 1)
    axs[0].plot([t0, t0 + timedelta(days=1)], [0, 1])
    axs[1].plot([0.0, 1.0], [0, 1])

    fig._refresh_auto_share("x")
    fig.canvas.draw()

    sig0 = fig._axis_unit_signature(axs[0], "x")
    sig1 = fig._axis_unit_signature(axs[1], "x")
    assert sig0 != sig1
    assert _share_sibling_count(axs[0], "x") == 1
    assert _share_sibling_count(axs[1], "x") == 1


def test_explicit_sharey_propagates_scale_changes():
    fig, axs = uplt.subplots(ncols=2, sharey=True)
    axs[0].format(yscale="log")
    fig.canvas.draw()

    assert axs[0].get_yscale() == "log"
    assert axs[1].get_yscale() == "log"


@pytest.mark.parametrize("va", ["bottom", "center", "top"])
def test_suptitle_vertical_alignment_preserves_top_spacing(va):
    """
    Suptitle vertical alignment should not reduce the spacing above top content.
    """
    fig, axs = uplt.subplots(ncols=2)
    fig.format(
        suptitle="Long figure title\nsecond line",
        suptitle_kw={"va": va},
        toplabels=("left", "right"),
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    axs_top = fig._get_align_axes("top")
    labs = tuple(t for t in fig._suplabel_dict["top"].values() if t.get_text())
    pad = (fig._suptitle_pad / 72) / fig.get_size_inches()[1]
    y_expected = fig._get_offset_coord("top", axs_top, renderer, pad=pad, extra=labs)

    bbox = fig._suptitle.get_window_extent(renderer)
    y_actual = fig.transFigure.inverted().transform((0, bbox.ymin))[1]
    y_tol = 1.5 / (fig.dpi * fig.get_size_inches()[1])  # ~1.5 px tolerance
    assert y_actual >= y_expected - y_tol

    uplt.close("all")


def test_suptitle_clears_shared_subset_titles():
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    axs[0, :].format(title="Row title")
    fig.format(suptitle="Figure title")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    subset_title = next(iter(fig._subset_title_dict.values()))["artist"]
    subset_bbox = subset_title.get_window_extent(renderer)
    suptitle_bbox = fig._suptitle.get_window_extent(renderer)

    assert subset_bbox.y1 <= suptitle_bbox.y0

    uplt.close("all")


def test_subplots_pixelsnap_aligns_axes_bounds():
    with uplt.rc.context({"subplots.pixelsnap": True}):
        fig, axs = uplt.subplots(ncols=2, nrows=2)
        axs.plot([0, 1], [0, 1])
        fig.canvas.draw()

        renderer = fig._get_renderer()
        width = float(renderer.width)
        height = float(renderer.height)

        for ax in axs:
            bbox = ax.get_position(original=False)
            coords = np.array(
                [bbox.x0 * width, bbox.y0 * height, bbox.x1 * width, bbox.y1 * height]
            )
            assert np.allclose(coords, np.round(coords), atol=1e-8)


def test_figure_repr():
    fig, axs = uplt.subplots(ncols=2, nrows=3)
    r = repr(fig)
    assert "Figure(" in r
    assert "nrows=3" in r
    assert "ncols=2" in r
    uplt.close(fig)


def test_register_share_label_group_basic():
    fig, axs = uplt.subplots(ncols=3)
    axs[0].set_xlabel("shared x")
    axs[1].set_xlabel("also x")
    fig._register_share_label_group([axs[0], axs[1]], target="x", source=axs[0])
    assert fig._has_share_label_groups("x")
    assert fig._is_share_label_group_member(axs[0], "x")
    assert fig._is_share_label_group_member(axs[1], "x")
    assert not fig._is_share_label_group_member(axs[2], "x")
    uplt.close(fig)


def test_register_share_label_group_y():
    fig, axs = uplt.subplots(nrows=3)
    axs[0].set_ylabel("shared y")
    axs[1].set_ylabel("also y")
    fig._register_share_label_group([axs[0], axs[1]], target="y", source=axs[0])
    assert fig._has_share_label_groups("y")
    assert fig._is_share_label_group_member(axs[0], "y")
    uplt.close(fig)


def test_register_share_label_group_empty_and_single():
    fig, axs = uplt.subplots(ncols=2)
    fig._register_share_label_group([], target="x")
    assert not fig._has_share_label_groups("x")
    fig._register_share_label_group([axs[0]], target="x")
    assert not fig._has_share_label_groups("x")
    uplt.close(fig)


def test_register_share_label_group_deduplicates():
    fig, axs = uplt.subplots(ncols=2)
    axs[0].set_xlabel("x")
    fig._register_share_label_group([axs[0], axs[0], axs[1]], target="x")
    assert fig._has_share_label_groups("x")
    uplt.close(fig)


def test_clear_share_label_groups_all():
    fig, axs = uplt.subplots(ncols=3)
    axs[0].set_xlabel("x")
    fig._register_share_label_group([axs[0], axs[1]], target="x")
    fig._register_share_label_group([axs[0], axs[1]], target="y")
    assert fig._has_share_label_groups("x")
    fig._clear_share_label_groups()
    assert not fig._has_share_label_groups("x")
    assert not fig._has_share_label_groups("y")
    uplt.close(fig)


def test_clear_share_label_groups_by_axes():
    fig, axs = uplt.subplots(ncols=3)
    axs[0].set_xlabel("x0")
    axs[2].set_xlabel("x2")
    fig._register_share_label_group([axs[0], axs[1]], target="x")
    fig._clear_share_label_groups(axes=[axs[0]], target="x")
    assert not fig._has_share_label_groups("x")
    uplt.close(fig)


def test_clear_share_label_groups_with_spanning_labels():
    fig, axs = uplt.subplots(ncols=3)
    axs[0].set_xlabel("shared x")
    axs[1].set_xlabel("shared x")
    fig._register_share_label_group([axs[0], axs[1]], target="x", source=axs[0])
    fig.canvas.draw()
    fig._clear_share_label_groups(axes=[axs[0], axs[1]], target="x")
    assert not fig._has_share_label_groups("x")
    uplt.close(fig)


def test_apply_share_label_groups():
    fig, axs = uplt.subplots(ncols=3, share=False)
    axs[0].set_xlabel("shared label")
    axs[1].set_xlabel("")
    fig._register_share_label_group([axs[0], axs[1]], target="x", source=axs[0])
    fig.canvas.draw()
    uplt.close(fig)


def test_apply_share_label_groups_y():
    fig, axs = uplt.subplots(nrows=3, share=False)
    axs[0].set_ylabel("shared label")
    axs[1].set_ylabel("")
    fig._register_share_label_group([axs[0], axs[1]], target="y", source=axs[0])
    fig.canvas.draw()
    uplt.close(fig)


def test_register_share_label_group_updates_existing():
    fig, axs = uplt.subplots(ncols=3)
    axs[0].set_xlabel("original")
    fig._register_share_label_group([axs[0], axs[1]], target="x", source=axs[0])
    axs[0].set_xlabel("updated")
    fig._register_share_label_group([axs[0], axs[1]], target="x", source=axs[0])
    fig.canvas.draw()
    uplt.close(fig)


def test_share_label_group_mixed_label_position_splits():
    fig, axs = uplt.subplots(ncols=3, share=False)
    axs[0].set_xlabel("bottom")
    axs[1].xaxis.set_label_position("top")
    axs[1].set_xlabel("top")
    axs[2].set_xlabel("bottom")
    fig._register_share_label_group([axs[0], axs[1], axs[2]], target="x")
    fig.canvas.draw()
    uplt.close(fig)


def test_deduplicate_axes():
    fig, axs = uplt.subplots(ncols=3)
    result = fig._deduplicate_axes([axs[0], axs[0], axs[1]])
    assert len(result) == 2
    uplt.close(fig)


def test_normalize_title_alignment_left():
    from ultraplot.figure import Figure

    assert Figure._normalize_title_alignment("left") == "left"


def test_normalize_title_alignment_center():
    from ultraplot.figure import Figure

    assert Figure._normalize_title_alignment("center") == "center"


def test_normalize_title_alignment_right():
    from ultraplot.figure import Figure

    assert Figure._normalize_title_alignment("right") == "right"


def test_normalize_title_alignment_invalid():
    from ultraplot.figure import Figure

    with pytest.raises((ValueError, KeyError)):
        Figure._normalize_title_alignment("invalid_loc_xyz")


def test_resolve_title_props_defaults():
    from ultraplot.figure import Figure

    kw = Figure._resolve_title_props(None, {})
    assert isinstance(kw, dict)


def test_resolve_title_props_with_fontdict():
    from ultraplot.figure import Figure

    kw = Figure._resolve_title_props({"size": 20}, {"weight": "bold"})
    assert kw["size"] == 20
    assert kw["weight"] == "bold"


def test_visible_subset_group_axes():
    fig, axs = uplt.subplots(ncols=3)
    group = {"axes": list(axs), "artist": None}
    result = fig._visible_subset_group_axes(group)
    assert len(result) == 3
    uplt.close(fig)


def test_update_subset_title_single_axes_delegates():
    fig, axs = uplt.subplots(ncols=3)
    artist = fig._update_subset_title([axs[0]], "Solo title")
    assert artist.get_text() == "Solo title"
    uplt.close(fig)


def test_update_subset_title_empty_raises():
    fig, axs = uplt.subplots(ncols=2)
    with pytest.raises(ValueError, match="Need at least one"):
        fig._update_subset_title([], "No axes")
    uplt.close(fig)


def test_update_subset_title_creates_group():
    fig, axs = uplt.subplots(ncols=3)
    artist = fig._update_subset_title([axs[0], axs[1]], "Two-panel title")
    assert artist.get_text() == "Two-panel title"
    assert len(fig._subset_title_dict) == 1
    uplt.close(fig)


def test_update_subset_title_update_existing():
    fig, axs = uplt.subplots(ncols=3)
    fig._update_subset_title([axs[0], axs[1]], "First")
    fig._update_subset_title([axs[0], axs[1]], "Updated")
    assert len(fig._subset_title_dict) == 1
    group = next(iter(fig._subset_title_dict.values()))
    assert group["artist"].get_text() == "Updated"
    uplt.close(fig)


def test_get_subset_title_bbox_returns_none_when_empty():
    fig, axs = uplt.subplots(ncols=2)
    renderer = fig._get_renderer()
    assert fig._get_subset_title_bbox(axs[0], renderer) is None
    uplt.close(fig)


def test_get_subset_title_bbox_for_top_row_only():
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    fig._update_subset_title([axs[0], axs[1]], "Top row title")
    fig.canvas.draw()
    renderer = fig._get_renderer()
    bbox_top = fig._get_subset_title_bbox(axs[0], renderer)
    bbox_bottom = fig._get_subset_title_bbox(axs[2], renderer)
    assert bbox_top is not None
    assert bbox_bottom is None
    uplt.close(fig)


def test_align_subset_titles_removes_orphaned():
    fig, axs = uplt.subplots(ncols=3)
    fig._update_subset_title([axs[0], axs[1]], "Will be orphaned")
    key = next(iter(fig._subset_title_dict))
    fig._subset_title_dict[key]["axes"] = []
    renderer = fig._get_renderer()
    fig._align_subset_titles(renderer)
    assert len(fig._subset_title_dict) == 0
    uplt.close(fig)


def test_align_subset_titles_with_manual_y():
    fig, axs = uplt.subplots(ncols=3)
    fig._update_subset_title([axs[0], axs[1]], "Manual Y", y=0.95)
    fig.canvas.draw()
    key = next(iter(fig._subset_title_dict))
    artist = fig._subset_title_dict[key]["artist"]
    assert np.isclose(artist.get_position()[1], 0.95)
    uplt.close(fig)


def test_subset_title_left_alignment():
    fig, axs = uplt.subplots(ncols=3)
    fig._update_subset_title([axs[0], axs[1]], "Left title", loc="left")
    key = next(iter(fig._subset_title_dict))
    artist = fig._subset_title_dict[key]["artist"]
    assert artist.get_ha() == "left"
    uplt.close(fig)


def test_subset_title_right_alignment():
    fig, axs = uplt.subplots(ncols=3)
    fig._update_subset_title([axs[0], axs[1]], "Right title", loc="right")
    key = next(iter(fig._subset_title_dict))
    artist = fig._subset_title_dict[key]["artist"]
    assert artist.get_ha() == "right"
    uplt.close(fig)


def test_find_aspect_spans_empty():
    fig, axs = uplt.subplots(ncols=2)
    spans = fig._find_misaligned_spans([])
    assert spans == []
    uplt.close(fig)


def test_find_aspect_spans_no_aspect():
    fig, axs = uplt.subplots(ncols=2)
    axes = list(fig._iter_axes(hidden=False, children=False, panels=False))
    spans = fig._find_misaligned_spans(axes)
    assert spans == []
    uplt.close(fig)


def test_remap_axes_with_empty_spans():
    fig, axs = uplt.subplots(ncols=2)
    axes = list(fig._iter_axes(hidden=False, children=False, panels=False))
    fig._remap_axes_to_span(axes, [])
    uplt.close(fig)


def test_align_spanning_axes_no_axes():
    fig = uplt.figure()
    fig._align_spanning_axes()
    uplt.close(fig)


def test_aspect_row_spanning_layout():
    fig, axs = uplt.subplots([[1, 2], [1, 3]])
    axs[0].set_aspect("equal")
    axs[0].plot([0, 1], [0, 1])
    axs[1].plot([0, 1], [0, 1])
    axs[2].plot([0, 1], [0, 1])
    fig.canvas.draw()
    axes = list(fig._iter_axes(hidden=False, children=False, panels=False))
    spans = fig._find_misaligned_spans(axes)
    assert len(spans) >= 1
    assert any(s[0] == "y" for s in spans)
    uplt.close(fig)


def test_aspect_col_spanning_layout():
    fig, axs = uplt.subplots([[1, 1], [2, 3]])
    axs[0].set_aspect("equal")
    axs[0].plot([0, 1], [0, 1])
    axs[1].plot([0, 1], [0, 1])
    axs[2].plot([0, 1], [0, 1])
    fig.canvas.draw()
    axes = list(fig._iter_axes(hidden=False, children=False, panels=False))
    spans = fig._find_misaligned_spans(axes)
    assert len(spans) >= 1
    assert any(s[0] == "x" for s in spans)
    uplt.close(fig)


def test_full_align_aspect_row_spanning():
    fig, axs = uplt.subplots([[1, 2], [1, 3]])
    axs[0].set_aspect("equal")
    axs[0].plot([0, 1], [0, 1])
    axs[1].plot([0, 1], [0, 1])
    axs[2].plot([0, 1], [0, 1])
    fig.canvas.draw()
    pos0 = axs[0].get_position()
    pos1 = axs[1].get_position()
    pos2 = axs[2].get_position()
    assert pos1.y0 + pos1.height <= pos0.y0 + pos0.height + 0.01
    uplt.close(fig)


def test_add_subplot_three_integer_args():
    fig = uplt.figure()
    ax = fig.add_subplot(2, 2, 1)
    assert ax is not None
    ax2 = fig.add_subplot(2, 2, (3, 4))
    assert ax2 is not None
    uplt.close(fig)


def test_explicit_figwidth_figheight():
    fig, axs = uplt.subplots(figwidth=6, figheight=4)
    w, h = fig.get_size_inches()
    assert np.isclose(w, 6, atol=0.1)
    assert np.isclose(h, 4, atol=0.1)
    uplt.close(fig)


def test_figwidth_overrides_refwidth():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        fig, axs = uplt.subplots(figwidth=6, refwidth=3)
    conflict_warnings = [w for w in record if "conflicting" in str(w.message).lower()]
    assert len(conflict_warnings) >= 1
    uplt.close(fig)


def test_figheight_overrides_refheight():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        fig, axs = uplt.subplots(figheight=4, refheight=2)
    conflict_warnings = [w for w in record if "conflicting" in str(w.message).lower()]
    assert len(conflict_warnings) >= 1
    uplt.close(fig)


def test_journal_size():
    fig, axs = uplt.subplots(journal="ams1")
    fig.canvas.draw()
    uplt.close(fig)


def test_subplots_with_gridspec_kw_warns():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        fig, axs = uplt.subplots([[1, 2], [3, 4]], gridspec_kw={"hspace": 0.5})
    kw_warnings = [w for w in record if "not necessary" in str(w.message).lower()]
    assert len(kw_warnings) >= 1
    uplt.close(fig)


def test_refaspect_as_tuple():
    fig, axs = uplt.subplots(refaspect=(16, 9))
    fig.canvas.draw()
    uplt.close(fig)


def test_figure_keyword_aliases() -> None:
    """Figure.__init__ aliases are folded by the @_alias_kwargs decorator."""
    # ref -> refnum, with the canonical default (1) preserved.
    assert uplt.figure(ref=3)._refnum == 3
    assert uplt.figure(refnum=2)._refnum == 2
    assert uplt.figure()._refnum == 1

    # width/height -> figwidth/figheight.
    np.testing.assert_allclose(uplt.figure(width=6, height=3).get_size_inches(), (6, 3))
    np.testing.assert_allclose(
        uplt.figure(figwidth=6, figheight=3).get_size_inches(), (6, 3)
    )

    # axwidth -> refwidth still builds a laid-out figure.
    fig, ax = uplt.subplots(axwidth=2)
    fig.canvas.draw()
    uplt.close("all")


def test_figure_alias_conflict_warns() -> None:
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        fig = uplt.figure(refnum=1, ref=5)
    assert fig._refnum == 1  # canonical wins
    assert any("conflicting" in str(w.message).lower() for w in record)
    uplt.close(fig)


def test_clear_drops_subplot_state():
    """
    clear() must forget the subplots it destroyed. Otherwise the figure keeps
    handing out axes that matplotlib already detached from it.
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    fig.clear()
    assert fig.axes == []
    assert len(fig.subplotgrid) == 0
    assert fig._get_subplot(1) is None
    assert list(fig._iter_subplots()) == []
    assert fig.gridspec is None
    uplt.close(fig)


def test_clear_drops_panel_state():
    """clear() also forgets figure-level panels created by e.g. fig.colorbar."""
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    m = axs[0].pcolormesh(np.arange(16).reshape(4, 4))
    fig.colorbar(m, loc="r")
    assert fig._panel_dict["right"]
    fig.clear()
    assert not any(fig._panel_dict.values())
    assert list(fig._iter_axes(panels=True)) == []
    uplt.close(fig)


def test_clear_resets_subplot_numbering():
    """
    The label counter restarts after clear(), so a reused figure numbers its
    subplots from 1 rather than continuing from the destroyed ones.
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    fig.clear()
    ax = fig.add_subplot(111)
    assert ax.number == 1
    assert list(fig._iter_subplots()) == [ax]
    uplt.close(fig)


def test_clear_allows_suptitle():
    """
    Matplotlib's clear() sets _suptitle to None, so ultraplot must rebuild its
    label artists or the next format(suptitle=...) raises AttributeError.
    """
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    fig.clear()
    fig.add_subplot(111)
    fig.format(suptitle="after clear")
    fig.canvas.draw()
    assert fig._suptitle.get_text() == "after clear"
    assert fig._suptitle in fig.texts  # detached artists never render
    uplt.close(fig)


def test_clf_alias_clears_subplot_state():
    """clf() is matplotlib's alias for clear() and must reset the same state."""
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    fig.clf()
    assert len(fig.subplotgrid) == 0
    assert fig.gridspec is None
    uplt.close(fig)


def test_figure_is_reusable_after_clear():
    """A cleared figure can be drawn again from scratch."""
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    fig.canvas.draw()
    fig.clear()
    axs = fig.add_subplots(nrows=1, ncols=3)
    axs[0].plot([1, 2, 3])
    fig.canvas.draw()
    assert len(fig.subplotgrid) == 3
    assert fig.gridspec.get_geometry() == (1, 3)
    uplt.close(fig)


def test_spanning_ylabel_is_outside_leftlabels():
    """Row labels take precedence over the shared y label in side layout."""
    fig, axs = uplt.subplots(nrows=2, share=True, refwidth=2)
    axs.format(ylabel="Shared y")
    fig.format(leftlabels=("Row 1", "Row 2"), leftlabelsharedpad="20pt")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    shared = next(iter(fig._supylabel_dict.values())).get_window_extent(renderer)
    rows = [
        label.get_window_extent(renderer)
        for label in fig._suplabel_dict["left"].values()
    ]
    gap = min(row.xmin for row in rows) - shared.xmax
    assert gap >= fig._suplabel_shared_pad["left"] - 1e-6
    uplt.close(fig)


def test_spanning_ylabel_scales_with_output_dpi(tmp_path):
    """Spanning labels remain inside the figure when the output DPI changes."""
    fig, axs = uplt.subplots(nrows=2, share=True, figsize=(3, 3))
    axs.format(ylabel="Shared y")
    fig.format(leftlabels=("Row 1", "Row 2"), leftlabelsharedpad="5em")
    path = tmp_path / "spanning-label.png"
    fig.savefig(path, dpi=300)
    from matplotlib import image

    pixels = image.imread(path)
    dark = pixels[..., :3].min(axis=2) < 0.1
    # At high output DPI, the spanning y label must occupy the outer label lane.
    # Previously its raw-pixel transform placed it outside the saved image.
    assert dark[:, : pixels.shape[1] * 8 // 100].any()
    uplt.close(fig)
