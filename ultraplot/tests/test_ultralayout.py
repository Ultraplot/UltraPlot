import numpy as np
import pytest

import ultraplot as uplt
from ultraplot import ultralayout
from ultraplot.gridspec import GridSpec
from ultraplot.internals.warnings import UltraPlotWarning


def test_is_orthogonal_layout_simple_grid():
    """Test orthogonal layout detection for simple grids."""
    # Simple 2x2 grid should be orthogonal
    array = np.array([[1, 2], [3, 4]])
    assert ultralayout.is_orthogonal_layout(array) is True


def test_is_orthogonal_layout_non_orthogonal():
    """Test orthogonal layout detection for non-orthogonal layouts."""
    # Centered subplot with empty cells should be non-orthogonal
    array = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    assert ultralayout.is_orthogonal_layout(array) is False


def test_is_orthogonal_layout_spanning():
    """Test orthogonal layout with spanning subplots that is still orthogonal."""
    # L-shape that maintains grid alignment
    array = np.array([[1, 1], [1, 2]])
    assert ultralayout.is_orthogonal_layout(array) is True


def test_is_orthogonal_layout_with_gaps():
    """Test non-orthogonal layout with gaps."""
    array = np.array([[1, 1, 1], [2, 0, 3]])
    assert ultralayout.is_orthogonal_layout(array) is False


def test_is_orthogonal_layout_empty():
    """Test empty layout."""
    array = np.array([[0, 0], [0, 0]])
    assert ultralayout.is_orthogonal_layout(array) is True


def test_gridspec_with_orthogonal_layout():
    """Test that GridSpec activates UltraLayout for orthogonal layouts."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 2], [3, 4]])
    gs = GridSpec(2, 2, layout_array=layout)
    assert gs._layout_array is not None
    # Should use UltraLayout for orthogonal layouts
    assert gs._use_ultra_layout is True


def test_gridspec_with_non_orthogonal_layout():
    """Test that GridSpec activates UltraLayout for non-orthogonal layouts."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    gs = GridSpec(2, 4, layout_array=layout)
    assert gs._layout_array is not None
    # Should use UltraLayout for non-orthogonal layouts
    assert gs._use_ultra_layout is True


def test_gridspec_without_kiwisolver(monkeypatch):
    """Test graceful fallback when kiwisolver is not available."""
    # Mock the ULTRA_AVAILABLE flag
    import ultraplot.gridspec as gs_module

    monkeypatch.setattr(gs_module, "ULTRA_AVAILABLE", False)

    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    gs = GridSpec(2, 4, layout_array=layout)
    # Should not activate UltraLayout if kiwisolver not available
    assert gs._use_ultra_layout is False


def test_gridspec_ultralayout_opt_out():
    """Test that UltraLayout can be disabled explicitly."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 2], [3, 4]])
    gs = GridSpec(2, 2, layout_array=layout, ultra_layout=False)
    assert gs._use_ultra_layout is False


def test_gridspec_default_layout_array_with_ultralayout():
    """Test that UltraLayout initializes a default layout array."""
    pytest.importorskip("kiwisolver")
    gs = GridSpec(2, 3)
    assert gs._layout_array is not None
    assert gs._layout_array.shape == (2, 3)
    assert gs._use_ultra_layout is True


def test_ultralayout_layout_array_shape_mismatch_warns():
    """Test that mismatched layout arrays fall back to the original array."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 2, 3]])
    with pytest.warns(UltraPlotWarning):
        gs = GridSpec(2, 2, layout_array=layout)
        resolved = gs._get_ultra_layout_array()
    assert resolved.shape == layout.shape
    assert np.array_equal(resolved, layout)


def test_subplots_pass_layout_array_into_gridspec():
    """Test that subplots pass the layout array to GridSpec."""
    layout = [[1, 1, 2], [3, 4, 5]]
    fig, axs = uplt.subplots(array=layout, figsize=(6, 4))
    assert np.array_equal(fig.gridspec._layout_array, np.array(layout))
    uplt.close(fig)


def test_ultralayout_solver_initialization():
    """Test UltraLayoutSolver can be initialized."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    solver = ultralayout.UltraLayoutSolver(layout, figwidth=10.0, figheight=6.0)
    assert solver.array is not None
    assert solver.nrows == 2
    assert solver.ncols == 4


def test_compute_ultra_positions():
    """Test computing positions with UltraLayout."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    positions = ultralayout.compute_ultra_positions(
        layout,
        figwidth=10.0,
        figheight=6.0,
        wspace=[0.2, 0.2, 0.2],
        hspace=[0.2],
    )

    # Should return positions for 3 subplots
    assert len(positions) == 3
    assert 1 in positions
    assert 2 in positions
    assert 3 in positions

    # Each position should be (left, bottom, width, height)
    for num, pos in positions.items():
        assert len(pos) == 4
        left, bottom, width, height = pos
        assert 0 <= left <= 1
        assert 0 <= bottom <= 1
        assert width > 0
        assert height > 0
        assert left + width <= 1.01  # Allow small numerical error
        assert bottom + height <= 1.01


def test_subplots_with_non_orthogonal_layout():
    """Test creating subplots with non-orthogonal layout."""
    pytest.importorskip("kiwisolver")
    layout = [[1, 1, 2, 2], [0, 3, 3, 0]]
    fig, axs = uplt.subplots(array=layout, figsize=(10, 6))

    # Should create 3 subplots
    assert len(axs) == 3

    # Check that positions are valid
    for ax in axs:
        pos = ax.get_position()
        assert pos.width > 0
        assert pos.height > 0
        assert 0 <= pos.x0 <= 1
        assert 0 <= pos.y0 <= 1


def test_ultralayout_panel_alignment_matches_parent():
    """Test panel axes stay aligned with parent axes under UltraLayout."""
    pytest.importorskip("kiwisolver")
    layout = [[1, 1, 2, 2], [0, 3, 3, 0]]
    fig, axs = uplt.subplots(array=layout, figsize=(8, 5))
    parent = axs[0]
    panel = parent.panel_axes("right", width=0.4)
    fig.auto_layout()

    parent_pos = parent.get_position()
    panel_pos = panel.get_position()
    assert np.isclose(panel_pos.y0, parent_pos.y0)
    assert np.isclose(panel_pos.height, parent_pos.height)
    assert panel_pos.x0 >= parent_pos.x1
    uplt.close(fig)


@pytest.mark.parametrize("ultra_layout", [False, True])
def test_fixed_aspect_spanning_axes_keeps_adjacent_stack_aligned(ultra_layout):
    """Fixed-aspect spanning axes should keep adjacent subplot stacks aligned."""
    if ultra_layout:
        pytest.importorskip("kiwisolver")

    fig, axs = uplt.subplots(array=[[1, 2], [1, 3]], ultra_layout=ultra_layout)
    axs[0].plot([0, 1], [0, 1])
    axs[0].format(aspect="equal")
    fig.canvas.draw()

    left = axs[0].get_position()
    top_right = axs[1].get_position()
    bottom_right = axs[2].get_position()

    assert np.isclose(top_right.y1, left.y1)
    assert np.isclose(bottom_right.y0, left.y0)
    uplt.close(fig)


def test_subplots_with_orthogonal_layout():
    """Test creating subplots with orthogonal layout (should work as before)."""
    layout = [[1, 2], [3, 4]]
    fig, axs = uplt.subplots(array=layout, figsize=(8, 6))

    # Should create 4 subplots
    assert len(axs) == 4

    # Check that positions are valid
    for ax in axs:
        pos = ax.get_position()
        assert pos.width > 0
        assert pos.height > 0


def test_ultralayout_respects_spacing():
    """Test that UltraLayout respects spacing parameters."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])

    # Compute with different spacing
    positions1 = ultralayout.compute_ultra_positions(
        layout, figwidth=10.0, figheight=6.0, wspace=[0.1, 0.1, 0.1], hspace=[0.1]
    )
    positions2 = ultralayout.compute_ultra_positions(
        layout, figwidth=10.0, figheight=6.0, wspace=[0.5, 0.5, 0.5], hspace=[0.5]
    )

    # Subplots should be smaller with more spacing
    for num in [1, 2, 3]:
        _, _, width1, height1 = positions1[num]
        _, _, width2, height2 = positions2[num]
        # With more spacing, subplots should be smaller
        assert width2 < width1 or height2 < height1


def test_ultralayout_preserves_gap_between_spanning_axes():
    """Test UltraLayout preserves inter-axes gaps for spanning subplots."""
    pytest.importorskip("kiwisolver")
    layout = [[1, 1, 2, 2], [0, 3, 3, 0]]

    fig_ultra, axs_ultra = uplt.subplots(
        array=layout, ref=3, refwidth=2.3, wspace="1em", ultra_layout=True
    )
    fig_ultra.auto_layout()
    pos_left_ultra = axs_ultra[0].get_position()
    pos_right_ultra = axs_ultra[1].get_position()
    gap_ultra = pos_right_ultra.x0 - pos_left_ultra.x1
    uplt.close(fig_ultra)

    fig_legacy, axs_legacy = uplt.subplots(
        array=layout, ref=3, refwidth=2.3, wspace="1em", ultra_layout=False
    )
    fig_legacy.auto_layout()
    pos_left_legacy = axs_legacy[0].get_position()
    pos_right_legacy = axs_legacy[1].get_position()
    gap_legacy = pos_right_legacy.x0 - pos_left_legacy.x1
    uplt.close(fig_legacy)

    assert gap_ultra > 0
    assert np.isclose(gap_ultra, gap_legacy, rtol=0.1, atol=1e-3)


def test_ultralayout_respects_ratios():
    """Test that UltraLayout respects width/height ratios."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 2], [3, 4]])

    # Equal ratios
    positions1 = ultralayout.compute_ultra_positions(
        layout, figwidth=10.0, figheight=6.0, wratios=[1, 1], hratios=[1, 1]
    )

    # Unequal ratios
    positions2 = ultralayout.compute_ultra_positions(
        layout, figwidth=10.0, figheight=6.0, wratios=[1, 2], hratios=[1, 1]
    )

    # Subplot 2 should be wider than subplot 1 with unequal ratios
    _, _, width1_1, _ = positions1[1]
    _, _, width1_2, _ = positions1[2]
    _, _, width2_1, _ = positions2[1]
    _, _, width2_2, _ = positions2[2]

    # With equal ratios, widths should be similar
    assert abs(width1_1 - width1_2) < 0.01
    # With 1:2 ratio, second should be roughly twice as wide
    assert width2_2 > width2_1


def test_ultralayout_with_panels_uses_total_geometry():
    """Test UltraLayout accounts for panel slots in total geometry."""
    pytest.importorskip("kiwisolver")
    layout = [[1, 1, 2, 2], [0, 3, 3, 0]]
    fig, axs = uplt.subplots(array=layout, figsize=(8, 6))

    # Add a colorbar to introduce panel slots
    mappable = axs[0].imshow([[0, 1], [2, 3]])
    fig.colorbar(mappable, loc="r")

    gs = fig.gridspec
    gs._compute_ultra_positions()
    assert gs._ultra_layout_array.shape == gs.get_total_geometry()

    row_idxs = gs._get_indices("h", panel=False)
    col_idxs = gs._get_indices("w", panel=False)
    for i, row_idx in enumerate(row_idxs):
        for j, col_idx in enumerate(col_idxs):
            assert gs._ultra_layout_array[row_idx, col_idx] == gs._layout_array[i, j]

    ss = axs[0].get_subplotspec()
    assert gs._get_ultra_position(ss.num1, fig) is not None


def test_ultralayout_cached_positions():
    """Test that UltraLayout positions are cached in GridSpec."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    gs = GridSpec(2, 4, layout_array=layout)

    # Positions should not be computed yet
    assert gs._ultra_positions is None

    # Create a figure to trigger position computation
    fig = uplt.figure()
    gs._figure = fig

    # Access a position (this should trigger computation)
    ss = gs[0, 0]
    pos = ss.get_position(fig)

    # Positions should now be cached
    assert gs._ultra_positions is not None
    assert len(gs._ultra_positions) == 3


def test_ultralayout_with_margins():
    """Test that UltraLayout respects margin parameters."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 2]])

    # Small margins
    positions1 = ultralayout.compute_ultra_positions(
        layout, figwidth=10.0, figheight=6.0, left=0.1, right=0.1, top=0.1, bottom=0.1
    )

    # Large margins
    positions2 = ultralayout.compute_ultra_positions(
        layout, figwidth=10.0, figheight=6.0, left=1.0, right=1.0, top=1.0, bottom=1.0
    )

    # With larger margins, subplots should be smaller
    for num in [1, 2]:
        _, _, width1, height1 = positions1[num]
        _, _, width2, height2 = positions2[num]
        assert width2 < width1
        assert height2 < height1


def test_complex_non_orthogonal_layout():
    """Test a more complex non-orthogonal layout."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 1, 1, 2], [3, 3, 0, 2], [4, 5, 5, 5]])

    positions = ultralayout.compute_ultra_positions(
        layout, figwidth=12.0, figheight=9.0
    )

    # Should have 5 subplots
    assert len(positions) == 5

    # All positions should be valid
    for num in range(1, 6):
        assert num in positions
        left, bottom, width, height = positions[num]
        assert 0 <= left <= 1
        assert 0 <= bottom <= 1
        assert width > 0
        assert height > 0


def test_ultralayout_module_exports():
    """Test that ultralayout module exports expected symbols."""
    assert hasattr(ultralayout, "UltraLayoutSolver")
    assert hasattr(ultralayout, "compute_ultra_positions")
    assert hasattr(ultralayout, "is_orthogonal_layout")
    assert hasattr(ultralayout, "get_grid_positions_ultra")


def test_gridspec_copy_preserves_layout_array():
    """Test that copying a GridSpec preserves the layout array."""
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    gs1 = GridSpec(2, 4, layout_array=layout)
    gs2 = gs1.copy()

    assert gs2._layout_array is not None
    assert np.array_equal(gs1._layout_array, gs2._layout_array)
    assert gs1._use_ultra_layout == gs2._use_ultra_layout


@pytest.mark.parametrize("transpose", [False, True])
@pytest.mark.parametrize("tight", [False, True])
@pytest.mark.parametrize("bars", [(), (0,), (0, 2, 3, 4), (0, 1, 2, 3, 4)])
def test_staggered_spans_preserve_sizes_and_local_guide_gaps(transpose, tight, bars):
    """A guide changes its own interface, not axes sizes or other row gaps."""
    pytest.importorskip("kiwisolver")
    layout = np.array([[1, 1, 2, 2, 3, 3], [0, 4, 4, 5, 5, 0]])
    if transpose:
        layout = layout.T
    side = "bottom" if transpose else "right"
    space_key = "hspace" if transpose else "wspace"
    x = np.array([-10, -5, 0, 5, 10])
    data = np.random.RandomState(51423).rand(5, 5)
    for space in (0.1, 0.5):
        fig, axs = uplt.subplots(
            layout,
            refwidth=2.2,
            refaspect=1,
            tight=tight,
            **{space_key: f"{space}in"},
        )
        for i, ax in enumerate(axs):
            kw = {}
            if i in bars:
                kw = dict(colorbar=side, colorbar_kw=dict(space="0.1in", width="0.2in"))
            ax.contourf(x, x, data, **kw)
        fig.canvas.draw()
        size = fig.get_size_inches()
        boxes = np.array([ax.get_position().bounds for ax in axs]) * np.tile(size, 2)
        # Figure sizes are rounded up to pixels; allow at most one pixel.
        np.testing.assert_allclose(boxes[:, 2:], 2.2, atol=1 / fig.dpi, rtol=0)
        for first, second in ((0, 1), (1, 2), (3, 4)):
            if transpose:
                gap = boxes[first, 1] - boxes[second, 1] - boxes[second, 3]
            else:
                gap = boxes[second, 0] - boxes[first, 0] - boxes[first, 2]
            assert gap == pytest.approx(space + (0.3 if first in bars else 0))
        if not bars:
            # Equal empty half-slots keep the shorter row/column centred.
            dim = 1 if transpose else 0
            outer_center = (boxes[0, dim] + boxes[2, dim] + boxes[0, dim + 2]) / 2
            inner_center = (boxes[3, dim] + boxes[4, dim] + boxes[3, dim + 2]) / 2
            assert inner_center == pytest.approx(outer_center)
        for i in bars:
            parent = axs[i].get_position()
            panel = axs[i]._panel_dict[side][0].get_position()
            if transpose:
                assert panel.x0 == pytest.approx(parent.x0)
                assert panel.width == pytest.approx(parent.width)
            else:
                assert panel.y0 == pytest.approx(parent.y0)
                assert panel.height == pytest.approx(parent.height)
        # Drawing again must not feed size changes back into tight layout.
        fig.canvas.draw()
        again = np.array([ax.get_position().bounds for ax in axs]) * np.tile(
            fig.get_size_inches(), 2
        )
        np.testing.assert_allclose(again[:, 2:], boxes[:, 2:], atol=1 / fig.dpi, rtol=0)
        uplt.close(fig)


@pytest.mark.parametrize("transpose", [False, True])
def test_staggered_spans_respect_nonuniform_spacing(transpose):
    layout = np.array([[1, 1, 2, 2, 3, 3], [0, 4, 4, 5, 5, 0]])
    if transpose:
        layout = layout.T
    fig, axs = uplt.subplots(
        layout,
        refwidth=2.2,
        tight=False,
        **{
            ("hspace" if transpose else "wspace"): [
                "0.05in",
                "0.3in",
                "0.2in",
                "0.7in",
                "0.1in",
            ]
        },
    )
    fig.canvas.draw()
    boxes = np.array([ax.get_position().bounds for ax in axs]) * np.tile(
        fig.get_size_inches(), 2
    )
    np.testing.assert_allclose(boxes[:, 2:], 2.2, atol=1 / fig.dpi, rtol=0)
    for (a, b), expected in zip(((0, 1), (1, 2), (3, 4)), (0.3, 0.7, 0.2)):
        gap = (
            boxes[a, 1] - boxes[b, 1] - boxes[b, 3]
            if transpose
            else boxes[b, 0] - boxes[a, 0] - boxes[a, 2]
        )
        assert gap == pytest.approx(expected)


@pytest.mark.parametrize("ultra_layout", [False, True])
@pytest.mark.parametrize("sizing", ["refwidth", "refheight", "figwidth", "figheight"])
def test_spanning_reference_aspect_with_internal_spacing(ultra_layout, sizing):
    """Reference and figure sizing agree with the actual reference axes box."""
    fig, axs = uplt.subplots(
        [[1, 1, 2], [3, 3, 2]],
        refaspect=1.5,
        ultra_layout=ultra_layout,
        tight=False,
        wspace="0.4in",
        hspace="0.3in",
        **{sizing: 2.2 if sizing.startswith("ref") else 7},
    )
    fig.canvas.draw()
    size = fig.get_size_inches()
    box = axs[0].get_position()
    width, height = box.width * size[0], box.height * size[1]
    assert width / height == pytest.approx(1.5, abs=0.01)
    if sizing == "refwidth":
        assert width == pytest.approx(2.2, abs=1 / fig.dpi)
    elif sizing == "refheight":
        assert height == pytest.approx(2.2, abs=1 / fig.dpi)
    else:
        assert size[0 if sizing == "figwidth" else 1] == pytest.approx(7)


@pytest.mark.parametrize("transpose", [False, True])
def test_spanning_axes_cover_adjacent_stack_with_panels(transpose):
    """A larger span still covers smaller axes and the panel/gap between them."""
    layout = np.array([[1, 2], [1, 3]])
    if transpose:
        layout = layout.T
    fig, axs = uplt.subplots(layout, refwidth=2.2, tight=False, space="0.3in")
    axs[1].panel_axes("right" if transpose else "bottom", width="0.2in", space="0.1in")
    fig.canvas.draw()
    span, first, last = [ax.get_position() for ax in axs]
    if transpose:
        assert span.x0 == pytest.approx(first.x0)
        assert span.x1 == pytest.approx(last.x1)
    else:
        assert span.y1 == pytest.approx(first.y1)
        assert span.y0 == pytest.approx(last.y0)


def test_staggered_spans_with_panels_and_fixed_figure_size():
    widths = []
    for space in ("0.2in", "0.5in"):
        fig, axs = uplt.subplots(
            [[1, 1, 2, 2, 3, 3], [0, 4, 4, 5, 5, 0]],
            figsize=(9, 6),
            tight=False,
            wspace=space,
        )
        for i in (0, 2, 3, 4):
            axs[i].panel_axes("right", width="0.2in", space="0.1in")
        fig.canvas.draw()
        np.testing.assert_allclose(fig.get_size_inches(), (9, 6))
        sizes = [ax.get_position().width * 9 for ax in axs]
        np.testing.assert_allclose(sizes, sizes[0])
        widths.append(sizes[0])
        uplt.close(fig)
    assert widths[1] < widths[0]


@pytest.mark.parametrize("side", ["left", "right", "top", "bottom"])
def test_staggered_spans_with_stacked_panels(side):
    layout = np.array([[1, 1, 2, 2, 3, 3], [0, 4, 4, 5, 5, 0]])
    if side in ("top", "bottom"):
        layout = layout.T
    fig, axs = uplt.subplots(layout, refwidth=2.2, tight=False, space="0.3in")
    # Add guides in reverse axes order and stack two on each parent.
    for i in (4, 3, 2, 0):
        for _ in range(2):
            axs[i].panel_axes(side, width="0.2in", space="0.1in")
    fig.canvas.draw()
    sizes = np.array(
        [[ax.get_position().width, ax.get_position().height] for ax in axs]
    )
    sizes *= fig.get_size_inches()
    np.testing.assert_allclose(sizes, 2.2, atol=1 / fig.dpi, rtol=0)


@pytest.mark.parametrize("transpose", [False, True])
@pytest.mark.parametrize("spanning", [False, True])
def test_exhausted_figure_space_does_not_invert_axes(transpose, spanning):
    """Oversized margins collapse visible spans instead of mirroring axes."""
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]] if spanning else [[1, 2]])
    if transpose:
        layout = layout.T
    positions = ultralayout.compute_ultra_positions(
        layout,
        figwidth=2,
        figheight=2,
        **({"top": 1, "bottom": 2} if transpose else {"left": 1, "right": 2}),
    )
    for left, bottom, width, height in positions.values():
        assert np.isfinite((left, bottom, width, height)).all()
        assert width >= 0
        assert height >= 0
        assert (height if transpose else width) == 0


@pytest.mark.parametrize("transpose", [False, True])
def test_wide_spacing_does_not_clamp_virtual_tracks(transpose):
    """Large gaps may require negative subdivisions inside positive spans."""
    layout = np.array([[1, 1, 2, 2, 3, 3], [0, 4, 4, 5, 5, 0]])
    if transpose:
        layout = layout.T
    fig, axs = uplt.subplots(
        layout,
        refwidth=1,
        refaspect=1,
        tight=False,
        **{("hspace" if transpose else "wspace"): "2in"},
    )
    fig.canvas.draw()
    sizes = np.array(
        [[ax.get_position().width, ax.get_position().height] for ax in axs]
    )
    sizes *= fig.get_size_inches()
    np.testing.assert_allclose(sizes, 1, atol=1 / fig.dpi, rtol=0)
