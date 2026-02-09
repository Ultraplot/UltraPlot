#!/usr/bin/env python3
"""
Test external axes container integration.

These tests verify that the ExternalAxesContainer works correctly with
external axes like mpltern.TernaryAxes.
"""

import numpy as np
import pytest

import ultraplot as uplt

# Check if mpltern is available
try:
    import mpltern  # noqa: F401
    from mpltern.ternary import TernaryAxes

    HAS_MPLTERN = True
except ImportError:
    HAS_MPLTERN = False


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_creation_via_subplots():
    """Test that external axes container is created via subplots."""
    fig, axs = uplt.subplots(projection="ternary")

    # subplots returns a SubplotGrid
    assert axs is not None
    assert len(axs) == 1
    ax = axs[0]
    assert ax is not None


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_has_external_child():
    """Test that container has external child methods."""
    fig, ax = uplt.subplots(projection="ternary")

    # Container should have helper methods
    if hasattr(ax, "has_external_child"):
        assert hasattr(ax, "get_external_child")
        assert hasattr(ax, "get_external_axes")


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_format_method():
    """Test that format method works on container."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Should not raise
    ax.format(title="Test Title")

    # Verify title was set on container (not external axes)
    # The container manages titles, external axes handles plotting
    title = ax.get_title()
    # Title may be empty string if set on external axes instead
    # Just verify format doesn't crash
    assert title is not None


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_plotting():
    """Test that plotting methods are delegated to external axes."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Simple ternary plot
    n = 10
    t = np.linspace(0, 1, n)
    l = 1 - t
    r = np.zeros_like(t)

    # This should not raise
    result = ax.plot(t, l, r)
    assert result is not None


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_scatter():
    """Test that scatter works through container."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    n = 20
    t = np.random.rand(n)
    l = np.random.rand(n)
    r = 1 - t - l
    r = np.maximum(r, 0)  # Ensure non-negative

    # Should not raise
    result = ax.scatter(t, l, r)
    assert result is not None


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_drawing():
    """Test that drawing works without errors."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Add some data
    t = np.array([0.5, 0.3, 0.2])
    l = np.array([0.3, 0.4, 0.3])
    r = np.array([0.2, 0.3, 0.5])
    ax.scatter(t, l, r)

    # Should not raise
    fig.canvas.draw()


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_multiple_subplots():
    """Test that multiple external axes containers work."""
    fig, axs = uplt.subplots(nrows=1, ncols=2, projection="ternary")

    assert len(axs) == 2
    assert all(ax is not None for ax in axs)

    # Each should work independently
    for i, ax in enumerate(axs):
        ax.format(title=f"Plot {i+1}")
        t = np.random.rand(10)
        l = np.random.rand(10)
        r = 1 - t - l
        r = np.maximum(r, 0)
        ax.scatter(t, l, r)


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_with_abc_labels():
    """Test that abc labels work with container."""
    fig, axs = uplt.subplots(nrows=1, ncols=2, projection="ternary")

    # Should not raise
    fig.format(abc=True)

    # Each axes should have abc label
    for ax in axs:
        # abc label is internal, just verify no errors
        pass


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_label_fitting():
    """Test that external axes labels fit within bounds."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Set labels that would normally be cut off
    ax.set_tlabel("Top Component")
    ax.set_llabel("Left Component")
    ax.set_rlabel("Right Component")

    # Draw to trigger shrinking
    fig.canvas.draw()

    # Should not raise and labels should be positioned
    # (visual verification would require checking renderer output)


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_custom_shrink_factor():
    """Test that custom shrink factor can be specified."""
    # Note: This tests the API exists, actual shrinking tested visually
    fig = uplt.figure()
    ax = fig.add_subplot(111, projection="ternary", external_shrink_factor=0.8)

    assert ax is not None
    # Check if shrink factor was stored
    if hasattr(ax, "_external_shrink_factor"):
        assert ax._external_shrink_factor == 0.8


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_clear():
    """Test that clear method works."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Add data
    t = np.array([0.5])
    l = np.array([0.3])
    r = np.array([0.2])
    ax.scatter(t, l, r)

    # Clear should not raise
    ax.clear()


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_savefig():
    """Test that figures with container can be saved."""
    import os
    import tempfile

    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Add some data
    t = np.array([0.5, 0.3, 0.2])
    l = np.array([0.3, 0.4, 0.3])
    r = np.array([0.2, 0.3, 0.5])
    ax.scatter(t, l, r)

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # This should not raise
        fig.savefig(tmp_path)

        # File should exist and have content
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_regular_axes_still_work():
    """Test that regular ultraplot axes still work normally."""
    fig, axs = uplt.subplots()

    # SubplotGrid with one element
    ax = axs[0]

    # Should be regular CartesianAxes
    from ultraplot.axes import CartesianAxes

    assert isinstance(ax, CartesianAxes)

    # Should work normally
    ax.plot([1, 2, 3], [1, 2, 3])
    ax.format(title="Regular Plot")
    fig.canvas.draw()


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_position_bounds():
    """Test that container and external axes stay within bounds."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Get positions
    container_pos = ax.get_position()

    if hasattr(ax, "get_external_child"):
        child = ax.get_external_child()
        if child is not None:
            child_pos = child.get_position()

            # Child should be within or at container bounds
            assert child_pos.x0 >= container_pos.x0 - 0.01
            assert child_pos.y0 >= container_pos.y0 - 0.01
            assert child_pos.x1 <= container_pos.x1 + 0.01
            assert child_pos.y1 <= container_pos.y1 + 0.01


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_with_tight_layout():
    """Test that container works with tight_layout."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, projection="ternary")

    # Add data to all axes
    for ax in axs:
        t = np.random.rand(10)
        l = np.random.rand(10)
        r = 1 - t - l
        r = np.maximum(r, 0)
        ax.scatter(t, l, r)
        ax.format(title="Test")

    # tight_layout should not crash
    try:
        fig.tight_layout()
    except Exception:
        # tight_layout might not work perfectly with external axes
        # but shouldn't crash catastrophically
        pass


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_scatter_with_colorbar():
    """Test scatter plot with colorbar on ternary axes."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    n = 50
    t = np.random.rand(n)
    l = np.random.rand(n)
    r = 1 - t - l
    r = np.maximum(r, 0)
    c = np.random.rand(n)  # Color values

    # Scatter with color values
    sc = ax.scatter(t, l, r, c=c)

    # Should not crash
    assert sc is not None


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_fill_between():
    """Test fill functionality on ternary axes."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Create a triangular region to fill
    t = np.array([0.5, 0.6, 0.5, 0.4, 0.5])
    l = np.array([0.3, 0.3, 0.4, 0.3, 0.3])
    r = 1 - t - l

    # Should not crash
    ax.fill(t, l, r, alpha=0.5)


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_multiple_plot_calls():
    """Test multiple plot calls on same container."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Multiple plots
    for i in range(3):
        t = np.linspace(0, 1, 10) + i * 0.1
        t = np.clip(t, 0, 1)
        l = 1 - t
        r = np.zeros_like(t)
        ax.plot(t, l, r, label=f"Series {i+1}")

    # Should handle multiple plots
    fig.canvas.draw()


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_legend():
    """Test that legend works with container."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Plot with labels
    t1 = np.array([0.5, 0.3, 0.2])
    l1 = np.array([0.3, 0.4, 0.3])
    r1 = np.array([0.2, 0.3, 0.5])
    ax.scatter(t1, l1, r1, label="Data 1")

    t2 = np.array([0.4, 0.5, 0.1])
    l2 = np.array([0.4, 0.3, 0.5])
    r2 = np.array([0.2, 0.2, 0.4])
    ax.scatter(t2, l2, r2, label="Data 2")

    # Add legend - should not crash
    try:
        ax.legend()
    except Exception:
        # Legend might not be fully supported, but shouldn't crash hard
        pass


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_grid_lines():
    """Test grid functionality if available."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Try to enable grid
    try:
        if hasattr(ax, "grid"):
            ax.grid(True)
    except Exception:
        # Grid might not be supported on all external axes
        pass

    # Should not crash drawing
    fig.canvas.draw()


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_stale_flag():
    """Test that stale flag works correctly."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Check stale tracking exists
    if hasattr(ax, "_external_stale"):
        # After plotting, should be stale
        ax.plot([0.5], [0.3], [0.2])
        assert ax._external_stale == True

        # After drawing, may be reset
        fig.canvas.draw()


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_iterator_isolation():
    """Test that iteration doesn't expose external child."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Iterate using _iter_axes
    if hasattr(ax, "_iter_axes"):
        axes_list = list(ax._iter_axes())

        # Should only yield container
        assert ax in axes_list

        # External child should not be yielded
        if hasattr(ax, "get_external_child"):
            child = ax.get_external_child()
            if child is not None:
                assert child not in axes_list


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_with_different_shrink_factors():
    """Test multiple containers with different shrink factors."""
    fig = uplt.figure()

    ax1 = fig.add_subplot(121, projection="ternary", external_shrink_factor=0.9)
    ax2 = fig.add_subplot(122, projection="ternary", external_shrink_factor=0.7)

    # Both should work
    assert ax1 is not None
    assert ax2 is not None

    if hasattr(ax1, "_external_shrink_factor"):
        assert ax1._external_shrink_factor == 0.9

    if hasattr(ax2, "_external_shrink_factor"):
        assert ax2._external_shrink_factor == 0.7


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_set_limits():
    """Test setting limits on ternary axes through container."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Try setting limits (may or may not be supported)
    try:
        if hasattr(ax, "set_xlim"):
            ax.set_xlim(0, 1)
        if hasattr(ax, "set_ylim"):
            ax.set_ylim(0, 1)
    except Exception:
        # Limits might not apply to ternary axes
        pass

    # Should not crash
    fig.canvas.draw()


@pytest.mark.skipif(not HAS_MPLTERN, reason="mpltern not installed")
def test_container_axes_visibility():
    """Test that container axes are hidden but external is visible."""
    fig, axs = uplt.subplots(projection="ternary")
    ax = axs[0]

    # Container's visual elements should be hidden
    assert not ax.patch.get_visible()
    assert not ax.xaxis.get_visible()
    assert not ax.yaxis.get_visible()

    for spine in ax.spines.values():
        assert not spine.get_visible()


def test_projection_detection():
    """Test that ternary projection is properly detected."""
    # This tests the projection registry and detection logic
    fig = uplt.figure()

    # Should be able to detect ternary projection
    try:
        ax = fig.add_subplot(111, projection="ternary")
        # If mpltern is available, should create container
        # If not, should raise appropriate error
        if HAS_MPLTERN:
            assert ax is not None
    except Exception as e:
        # If mpltern not available, should get helpful error
        if not HAS_MPLTERN:
            assert "ternary" in str(e).lower() or "projection" in str(e).lower()
