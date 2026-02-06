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
