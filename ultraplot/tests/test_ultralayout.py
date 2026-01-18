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
