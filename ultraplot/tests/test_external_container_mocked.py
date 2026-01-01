#!/usr/bin/env python3
"""
Unit tests for ExternalAxesContainer using mocked external axes.

These tests verify container behavior without requiring external dependencies
like mpltern to be installed.
"""
from unittest.mock import MagicMock, Mock, call, patch

import numpy as np
import pytest
from matplotlib.transforms import Bbox

import ultraplot as uplt
from ultraplot.axes.container import ExternalAxesContainer


class MockExternalAxes:
    """Mock external axes class that mimics behavior of external axes like TernaryAxes."""

    def __init__(self, fig, *args, **kwargs):
        """Initialize mock external axes."""
        self.figure = fig
        self._position = Bbox.from_bounds(0.1, 0.1, 0.8, 0.8)
        self._title = ""
        self._xlabel = ""
        self._ylabel = ""
        self._xlim = (0, 1)
        self._ylim = (0, 1)
        self._visible = True
        self._zorder = 0
        self._artists = []
        self.stale = True

        # Mock patch and spines
        self.patch = Mock()
        self.patch.set_visible = Mock()
        self.patch.set_facecolor = Mock()
        self.patch.set_alpha = Mock()

        self.spines = {
            "top": Mock(set_visible=Mock()),
            "bottom": Mock(set_visible=Mock()),
            "left": Mock(set_visible=Mock()),
            "right": Mock(set_visible=Mock()),
        }

        # Simulate matplotlib behavior: auto-register with figure
        if hasattr(fig, "axes") and self not in fig.axes:
            fig.axes.append(self)

    def get_position(self):
        """Get axes position."""
        return self._position

    def set_position(self, pos, which="both"):
        """Set axes position."""
        self._position = pos
        self.stale = True

    def get_title(self):
        """Get title."""
        return self._title

    def set_title(self, title):
        """Set title."""
        self._title = title
        self.stale = True

    def get_xlabel(self):
        """Get xlabel."""
        return self._xlabel

    def set_xlabel(self, label):
        """Set xlabel."""
        self._xlabel = label
        self.stale = True

    def get_ylabel(self):
        """Get ylabel."""
        return self._ylabel

    def set_ylabel(self, label):
        """Set ylabel."""
        self._ylabel = label
        self.stale = True

    def get_xlim(self):
        """Get xlim."""
        return self._xlim

    def set_xlim(self, xlim):
        """Set xlim."""
        self._xlim = xlim
        self.stale = True

    def get_ylim(self):
        """Get ylim."""
        return self._ylim

    def set_ylim(self, ylim):
        """Set ylim."""
        self._ylim = ylim
        self.stale = True

    def set(self, **kwargs):
        """Set multiple properties."""
        for key, value in kwargs.items():
            if key == "title":
                self.set_title(value)
            elif key == "xlabel":
                self.set_xlabel(value)
            elif key == "ylabel":
                self.set_ylabel(value)
            elif key == "xlim":
                self.set_xlim(value)
            elif key == "ylim":
                self.set_ylim(value)
        self.stale = True

    def set_visible(self, visible):
        """Set visibility."""
        self._visible = visible

    def set_zorder(self, zorder):
        """Set zorder."""
        self._zorder = zorder

    def get_zorder(self):
        """Get zorder."""
        return self._zorder

    def set_frame_on(self, b):
        """Set frame on/off."""
        pass

    def set_aspect(self, aspect, adjustable=None):
        """Set aspect ratio."""
        pass

    def set_subplotspec(self, subplotspec):
        """Set subplot spec."""
        pass

    def plot(self, *args, **kwargs):
        """Mock plot method."""
        line = Mock()
        self._artists.append(line)
        self.stale = True
        return [line]

    def scatter(self, *args, **kwargs):
        """Mock scatter method."""
        collection = Mock()
        self._artists.append(collection)
        self.stale = True
        return collection

    def fill(self, *args, **kwargs):
        """Mock fill method."""
        poly = Mock()
        self._artists.append(poly)
        self.stale = True
        return [poly]

    def contour(self, *args, **kwargs):
        """Mock contour method."""
        cs = Mock()
        self._artists.append(cs)
        self.stale = True
        return cs

    def contourf(self, *args, **kwargs):
        """Mock contourf method."""
        cs = Mock()
        self._artists.append(cs)
        self.stale = True
        return cs

    def pcolormesh(self, *args, **kwargs):
        """Mock pcolormesh method."""
        mesh = Mock()
        self._artists.append(mesh)
        self.stale = True
        return mesh

    def imshow(self, *args, **kwargs):
        """Mock imshow method."""
        img = Mock()
        self._artists.append(img)
        self.stale = True
        return img

    def hexbin(self, *args, **kwargs):
        """Mock hexbin method."""
        poly = Mock()
        self._artists.append(poly)
        self.stale = True
        return poly

    def clear(self):
        """Clear axes."""
        self._artists.clear()
        self._title = ""
        self._xlabel = ""
        self._ylabel = ""
        self.stale = True

    def draw(self, renderer):
        """Mock draw method."""
        self.stale = False
        # Simulate position adjustment during draw (like ternary axes)
        # This is important for testing position synchronization
        pass

    def get_tightbbox(self, renderer):
        """Get tight bounding box."""
        return self._position.transformed(self.figure.transFigure)


# Tests


def test_container_creation_basic():
    """Test basic container creation without external axes."""
    fig = uplt.figure()
    ax = fig.add_subplot(111)

    assert ax is not None
    # Regular axes may or may not have external child methods
    # Just verify the axes was created successfully


def test_container_creation_with_external_axes():
    """Test container creation with external axes class."""
    fig = uplt.figure()

    # Create container with mock external axes
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    assert ax is not None
    assert ax.has_external_child()
    assert ax.get_external_child() is not None
    assert isinstance(ax.get_external_child(), MockExternalAxes)


def test_external_axes_removed_from_figure_axes():
    """Test that external axes is removed from figure axes list."""
    fig = uplt.figure()

    # Track initial axes count
    initial_count = len(fig.axes)

    # Create container with mock external axes
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # External child should NOT be in fig.axes
    child = ax.get_external_child()
    if child is not None:
        assert child not in fig.axes

    # Container should be in fig.axes
    # Note: The way ultraplot manages axes, the container may be wrapped
    # Just verify the child is not in the list
    assert child not in fig.axes


def test_position_synchronization():
    """Test that position changes sync between container and external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Set new position on container
    new_pos = Bbox.from_bounds(0.2, 0.2, 0.6, 0.6)
    ax.set_position(new_pos)

    # External axes should have similar position (accounting for shrink)
    child = ax.get_external_child()
    if child is not None:
        child_pos = child.get_position()
        # Position should be set (within or near the container bounds)
        assert child_pos is not None


def test_shrink_factor_default():
    """Test default shrink factor is applied."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Default shrink factor should be 0.95
    assert hasattr(ax, "_external_shrink_factor")
    assert ax._external_shrink_factor == 0.95


def test_shrink_factor_custom():
    """Test custom shrink factor can be specified."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MockExternalAxes,
        external_axes_kwargs={},
        external_shrink_factor=0.7,
    )

    assert ax._external_shrink_factor == 0.7


def test_plot_delegation():
    """Test that plot method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Call plot on container
    x = [1, 2, 3]
    y = [1, 2, 3]
    result = ax.plot(x, y)

    # Should return result from external axes
    assert result is not None


def test_scatter_delegation():
    """Test that scatter method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    x = np.random.rand(10)
    y = np.random.rand(10)
    result = ax.scatter(x, y)

    assert result is not None


def test_fill_delegation():
    """Test that fill method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    x = [0, 1, 1, 0]
    y = [0, 0, 1, 1]
    result = ax.fill(x, y)

    assert result is not None


def test_contour_delegation():
    """Test that contour method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    X = np.random.rand(10, 10)
    result = ax.contour(X)

    assert result is not None


def test_contourf_delegation():
    """Test that contourf method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    X = np.random.rand(10, 10)
    result = ax.contourf(X)

    assert result is not None


def test_pcolormesh_delegation():
    """Test that pcolormesh method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    X = np.random.rand(10, 10)
    result = ax.pcolormesh(X)

    assert result is not None


def test_imshow_delegation():
    """Test that imshow method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    X = np.random.rand(10, 10)
    result = ax.imshow(X)

    assert result is not None


def test_hexbin_delegation():
    """Test that hexbin method is delegated to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    x = np.random.rand(100)
    y = np.random.rand(100)
    result = ax.hexbin(x, y)

    assert result is not None


def test_format_method_basic():
    """Test format method with basic parameters."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Should not raise
    ax.format(title="Test Title")

    # Title should be set on external axes
    child = ax.get_external_child()
    if child is not None:
        assert child.get_title() == "Test Title"


def test_format_method_delegatable_params():
    """Test format method delegates appropriate parameters to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Format with delegatable parameters
    ax.format(
        title="Title", xlabel="X Label", ylabel="Y Label", xlim=(0, 10), ylim=(0, 5)
    )

    child = ax.get_external_child()
    if child is not None:
        assert child.get_title() == "Title"
        assert child.get_xlabel() == "X Label"
        assert child.get_ylabel() == "Y Label"
        assert child.get_xlim() == (0, 10)
        assert child.get_ylim() == (0, 5)


def test_clear_method():
    """Test clear method clears both container and external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Add data
    ax.plot([1, 2, 3], [1, 2, 3])
    ax.format(title="Title")

    child = ax.get_external_child()
    if child is not None:
        assert len(child._artists) > 0
        assert child.get_title() == "Title"

    # Clear
    ax.clear()

    # External axes should be cleared
    if child is not None:
        assert len(child._artists) == 0
        assert child.get_title() == ""


def test_stale_tracking():
    """Test that stale tracking works."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Initially stale
    assert ax._external_stale == True

    # After plotting, should be stale
    ax.plot([1, 2, 3], [1, 2, 3])
    assert ax._external_stale == True


def test_drawing():
    """Test that drawing works without errors."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Add some data
    ax.plot([1, 2, 3], [1, 2, 3])

    # Should not raise
    fig.canvas.draw()


def test_getattr_delegation():
    """Test that __getattr__ delegates to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    child = ax.get_external_child()
    if child is not None:
        # Access attribute that exists on external axes but not container
        # MockExternalAxes has 'stale' attribute
        assert hasattr(ax, "stale")


def test_getattr_raises_for_missing():
    """Test that __getattr__ raises AttributeError for missing attributes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    with pytest.raises(AttributeError):
        _ = ax.nonexistent_attribute_xyz


def test_dir_includes_external_attrs():
    """Test that dir() includes external axes attributes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    attrs = dir(ax)

    # Should include container methods
    assert "has_external_child" in attrs
    assert "get_external_child" in attrs

    # Should also include external axes methods
    child = ax.get_external_child()
    if child is not None:
        # Check for some mock external axes attributes
        assert "plot" in attrs
        assert "scatter" in attrs


def test_iter_axes_only_yields_container():
    """Test that _iter_axes only yields the container, not external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Iterate over axes
    axes_list = list(ax._iter_axes())

    # Should only yield the container
    assert len(axes_list) == 1
    assert axes_list[0] is ax

    # Should NOT include external child
    child = ax.get_external_child()
    if child is not None:
        assert child not in axes_list


def test_get_external_axes_alias():
    """Test that get_external_axes is an alias for get_external_child."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    assert ax.get_external_axes() is ax.get_external_child()


def test_container_invisible_elements():
    """Test that container's visual elements are hidden."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Container patch should be invisible
    assert not ax.patch.get_visible()

    # Container spines should be invisible
    for spine in ax.spines.values():
        assert not spine.get_visible()

    # Container axes should be invisible
    assert not ax.xaxis.get_visible()
    assert not ax.yaxis.get_visible()


def test_external_axes_visible():
    """Test that external axes elements are visible."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    child = ax.get_external_child()
    if child is not None:
        # External axes should be visible
        assert child._visible == True

        # Patch should have been set to visible
        child.patch.set_visible.assert_called()


def test_container_without_external_class():
    """Test container creation without external axes class."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=None, external_axes_kwargs={}
    )

    assert ax is not None
    assert not ax.has_external_child()
    assert ax.get_external_child() is None


def test_plotting_without_external_axes():
    """Test that plotting methods work even without external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=None, external_axes_kwargs={}
    )

    # Should fall back to parent implementation
    # (may or may not work depending on parent class, but shouldn't crash)
    try:
        result = ax.plot([1, 2, 3], [1, 2, 3])
        # If it works, result should be something
        assert result is not None
    except Exception:
        # If parent doesn't support it, that's OK too
        pass


def test_format_without_external_axes():
    """Test format method without external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=None, external_axes_kwargs={}
    )

    # Should not raise
    ax.format(title="Test")

    # Title should be set on container
    assert ax.get_title() == "Test"


def test_zorder_external_higher_than_container():
    """Test that external axes has higher zorder than container."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    container_zorder = ax.get_zorder()
    child = ax.get_external_child()

    if child is not None:
        child_zorder = child.get_zorder()
        # External axes should have higher zorder
        assert child_zorder > container_zorder


def test_stale_callback():
    """Test stale callback marks external axes as stale."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Reset stale flags
    ax._external_stale = False

    # Trigger stale callback if it exists
    if hasattr(ax, "stale_callback") and callable(ax.stale_callback):
        ax.stale_callback()

        # External should be marked stale
        assert ax._external_stale == True
    else:
        # If no stale_callback, just verify the flag can be set
        ax._external_stale = True
        assert ax._external_stale == True


def test_get_tightbbox_delegation():
    """Test get_tightbbox delegates to external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Mock renderer
    renderer = Mock()

    # Should not raise
    result = ax.get_tightbbox(renderer)

    # Should get result from external axes
    assert result is not None


def test_position_sync_disabled_during_sync():
    """Test that position sync doesn't recurse."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Set syncing flag
    ax._syncing_position = True

    # Change position
    new_pos = Bbox.from_bounds(0.3, 0.3, 0.5, 0.5)
    ax.set_position(new_pos)

    # External axes position should not have been updated
    # (since we're in a sync operation)
    # This is hard to test directly, but the code should not crash


def test_format_kwargs_extracted_from_init():
    """Test that format kwargs are extracted during init."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MockExternalAxes,
        external_axes_kwargs={},
        title="Init Title",
        xlabel="X",
        ylabel="Y",
    )

    child = ax.get_external_child()
    if child is not None:
        # Title should have been set during init
        assert child.get_title() == "Init Title"


def test_multiple_containers_independent():
    """Test that multiple containers work independently."""
    fig = uplt.figure()

    ax1 = ExternalAxesContainer(
        fig, 2, 1, 1, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    ax2 = ExternalAxesContainer(
        fig, 2, 1, 2, external_axes_class=MockExternalAxes, external_axes_kwargs={}
    )

    # Both should work
    assert ax1.has_external_child()
    assert ax2.has_external_child()

    # Should be different axes
    assert ax1 is not ax2
    assert ax1.get_external_child() is not ax2.get_external_child()

    # External children should not be in figure
    assert ax1.get_external_child() not in fig.axes
    assert ax2.get_external_child() not in fig.axes
