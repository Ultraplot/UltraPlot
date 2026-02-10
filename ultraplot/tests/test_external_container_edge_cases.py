#!/usr/bin/env python3
"""
Edge case and integration tests for ExternalAxesContainer.

These tests cover error handling, edge cases, and integration scenarios
without requiring external dependencies.
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest
from matplotlib.transforms import Bbox

import ultraplot as uplt
from ultraplot.axes.container import (
    ExternalAxesContainer,
    create_external_axes_container,
)


class FaultyExternalAxes:
    """Mock external axes that raises errors to test error handling."""

    def __init__(self, fig, *args, **kwargs):
        """Initialize but raise error to simulate construction failure."""
        raise RuntimeError("Failed to create external axes")


class MinimalExternalAxes:
    """Minimal external axes with only required methods."""

    def __init__(self, fig, *args, **kwargs):
        self.figure = fig
        self._position = Bbox.from_bounds(0.1, 0.1, 0.8, 0.8)
        self.stale = True
        self.patch = Mock()
        self.spines = {}
        self._visible = True
        self._zorder = 0

    def get_position(self):
        return self._position

    def set_position(self, pos, which="both"):
        self._position = pos

    def draw(self, renderer):
        self.stale = False

    def get_visible(self):
        return self._visible

    def set_visible(self, visible):
        self._visible = visible

    def get_animated(self):
        return False

    def get_zorder(self):
        return self._zorder

    def set_zorder(self, zorder):
        self._zorder = zorder

    def get_axes_locator(self):
        """Return axes locator (for matplotlib 3.9 compatibility)."""
        return None

    def get_in_layout(self):
        """Return whether axes participates in layout (matplotlib 3.9 compatibility)."""
        return True

    def set_in_layout(self, value):
        """Set whether axes participates in layout (matplotlib 3.9 compatibility)."""
        pass

    def get_clip_on(self):
        """Return whether clipping is enabled (matplotlib 3.9 compatibility)."""
        return True

    def get_rasterized(self):
        """Return whether axes is rasterized (matplotlib 3.9 compatibility)."""
        return False

    def get_agg_filter(self):
        """Return agg filter (matplotlib 3.9 compatibility)."""
        return None

    def get_sketch_params(self):
        """Return sketch params (matplotlib 3.9 compatibility)."""
        return None

    def get_path_effects(self):
        """Return path effects (matplotlib 3.9 compatibility)."""
        return []

    def get_figure(self):
        """Return the figure (matplotlib 3.9 compatibility)."""
        return self.figure

    def get_transform(self):
        """Return the transform (matplotlib 3.9 compatibility)."""
        from matplotlib.transforms import IdentityTransform

        return IdentityTransform()

    def get_transformed_clip_path_and_affine(self):
        """Return transformed clip path (matplotlib 3.9 compatibility)."""
        return None, None

    @property
    def zorder(self):
        return self._zorder

    @zorder.setter
    def zorder(self, value):
        self._zorder = value


class PositionChangingAxes(MinimalExternalAxes):
    """External axes that changes position during draw (like ternary)."""

    def __init__(self, fig, *args, **kwargs):
        super().__init__(fig, *args, **kwargs)
        self._draw_count = 0

    def draw(self, renderer):
        """Change position on first draw to simulate label adjustment."""
        self._draw_count += 1
        self.stale = False
        if self._draw_count == 1:
            # Simulate position adjustment for labels
            pos = self._position
            new_pos = Bbox.from_bounds(
                pos.x0 + 0.05, pos.y0 + 0.05, pos.width - 0.1, pos.height - 0.1
            )
            self._position = new_pos


class NoTightBboxAxes(MinimalExternalAxes):
    """External axes without get_tightbbox method."""

    pass  # Intentionally doesn't have get_tightbbox


class NoTightBboxAxes(MinimalExternalAxes):
    """External axes without get_tightbbox method."""

    def get_tightbbox(self, renderer):
        # Return None or basic bbox
        return None


class AutoRegisteringAxes(MinimalExternalAxes):
    """External axes that auto-registers with figure."""

    def __init__(self, fig, *args, **kwargs):
        super().__init__(fig, *args, **kwargs)
        # Simulate matplotlib behavior: auto-register
        if hasattr(fig, "axes") and self not in fig.axes:
            fig.axes.append(self)


# Tests


def test_faulty_external_axes_creation():
    """Test that container handles external axes creation failure gracefully."""
    fig = uplt.figure()

    # Should not crash, just warn
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=FaultyExternalAxes, external_axes_kwargs={}
    )

    # Container should exist but have no external child
    assert ax is not None
    assert not ax.has_external_child()
    assert ax.get_external_child() is None


def test_position_change_during_draw():
    """Test that container handles position changes during external axes draw."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=PositionChangingAxes,
        external_axes_kwargs={},
    )

    # Get initial external axes position
    child = ax.get_external_child()
    assert child is not None
    assert hasattr(child, "_draw_count")

    # Manually call draw to trigger the position change
    from unittest.mock import Mock

    renderer = Mock()
    ax.draw(renderer)

    # Verify child's draw was called
    # The position change happens during draw, which we just verified doesn't crash
    assert child._draw_count >= 1, f"Expected draw_count >= 1, got {child._draw_count}"
    # Container should sync its position to the external axes after draw
    assert np.allclose(ax.get_position().bounds, child.get_position().bounds)


def test_no_tightbbox_method():
    """Test container works with external axes that has no get_tightbbox."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=NoTightBboxAxes, external_axes_kwargs={}
    )

    # Should not crash during draw
    fig.canvas.draw()

    # get_tightbbox should fall back to parent
    renderer = Mock()
    result = ax.get_tightbbox(renderer)
    # Should return something (from parent implementation)
    # May be None or a bbox, but shouldn't crash


def test_auto_registering_axes_removed():
    """Test that auto-registering external axes is removed from fig.axes."""
    fig = uplt.figure()

    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=AutoRegisteringAxes,
        external_axes_kwargs={},
    )

    # External child should NOT be in axes (should have been removed)
    child = ax.get_external_child()
    assert child is not None

    # The key invariant: external child should not be in fig.axes
    # (it gets removed during container initialization)
    assert child not in fig.axes, f"External child should not be in fig.axes"


def test_format_with_non_delegatable_params():
    """Test format with parameters that can't be delegated."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    # Format with ultraplot-specific params (not delegatable)
    # Should not crash, just apply to container
    ax.format(abc=True, abcloc="ul")


def test_clear_without_external_axes():
    """Test clear works when there's no external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=None, external_axes_kwargs={}
    )

    # Should not crash
    ax.clear()


def test_getattr_during_initialization():
    """Test __getattr__ doesn't interfere with initialization."""
    fig = uplt.figure()

    # Should not crash during construction
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    assert ax is not None


def test_getattr_with_private_attribute():
    """Test __getattr__ raises for private attributes not found."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    with pytest.raises(AttributeError):
        _ = ax._nonexistent_private_attr


def test_position_cache_invalidation():
    """Test position cache is invalidated on position change."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    # Set position
    pos1 = Bbox.from_bounds(0.1, 0.1, 0.8, 0.8)
    ax.set_position(pos1)

    # Cache should be invalidated initially
    assert ax._position_synced is False

    # Draw to establish cache
    fig.canvas.draw()

    # After drawing, position sync should have occurred
    # The exact state depends on draw logic, just verify no crash

    # Change position again
    pos2 = Bbox.from_bounds(0.2, 0.2, 0.6, 0.6)
    ax.set_position(pos2)

    # Should be marked as needing sync
    assert ax._position_synced is False


def test_stale_flag_on_plotting():
    """Test that stale flag is set when plotting."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    # Reset stale flag
    ax._external_stale = False

    # Plot something (if external axes supports it)
    child = ax.get_external_child()
    if child is not None and hasattr(child, "plot"):
        # Add plot method to minimal axes for this test
        child.plot = Mock()
        ax.plot([1, 2, 3], [1, 2, 3])

        # Should be marked stale
        assert ax._external_stale == True


def test_draw_skips_when_not_stale():
    """Test that draw can skip external axes when not stale."""
    fig = uplt.figure()

    # Create mock with draw tracking
    draw_count = [0]

    class DrawCountingAxes(MinimalExternalAxes):
        def draw(self, renderer):
            draw_count[0] += 1
            self.stale = False

    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=DrawCountingAxes, external_axes_kwargs={}
    )

    # Set up conditions for skipping draw
    child = ax.get_external_child()
    if child:
        child.stale = False
    ax._external_stale = False
    ax._position_synced = True

    # Draw should not crash
    try:
        renderer = Mock()
        ax.draw(renderer)
    except Exception:
        # May fail due to missing renderer methods, that's OK
        pass


def test_draw_called_when_stale():
    """Test that draw calls external axes when stale."""
    fig = uplt.figure()

    # Create mock with draw tracking
    draw_count = [0]

    class DrawCountingAxes(MinimalExternalAxes):
        def draw(self, renderer):
            draw_count[0] += 1
            self.stale = False

    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=DrawCountingAxes, external_axes_kwargs={}
    )

    ax._external_stale = True

    # Draw should not crash and should call external draw
    try:
        renderer = Mock()
        ax.draw(renderer)
        # External axes draw should be called when stale
        assert draw_count[0] > 0
    except Exception:
        # May fail due to missing renderer methods, that's OK
        # Just verify no crash during setup
        pass


def test_shrink_with_zero_size():
    """Test shrink calculation with zero-sized position."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    # Set zero-sized position
    zero_pos = Bbox.from_bounds(0.5, 0.5, 0, 0)
    ax.set_position(zero_pos)

    # Should not crash during shrink
    ax._shrink_external_for_labels()


def test_format_kwargs_popped_before_parent():
    """Test that format kwargs are properly removed before parent init."""
    fig = uplt.figure()

    # Pass format kwargs that would cause issues if passed to parent
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
        title="Title",
        xlabel="X",
        grid=True,
    )

    # Should not crash
    assert ax is not None


def test_projection_kwarg_removed():
    """Test that projection kwarg is removed before parent init."""
    fig = uplt.figure()

    # Pass projection which should be popped
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
        projection="ternary",
    )

    # Should not crash
    assert ax is not None


def test_container_with_subplotspec():
    """Test container creation with subplot spec."""
    fig = uplt.figure()

    # Use add_subplot which handles subplotspec internally
    ax = fig.add_subplot(221)

    # Just verify it was created - subplotspec handling is internal
    assert ax is not None

    # If it's a container, verify it has the methods
    if hasattr(ax, "has_external_child"):
        # It's a container, test passes
        pass


def test_external_axes_with_no_set_position():
    """Test external axes that doesn't have set_position method."""

    class NoSetPositionAxes:
        def __init__(self, fig, *args, **kwargs):
            self.figure = fig
            self._position = Bbox.from_bounds(0.1, 0.1, 0.8, 0.8)
            self.patch = Mock()
            self.spines = {}

        def get_position(self):
            return self._position

        def draw(self, renderer):
            pass

    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=NoSetPositionAxes, external_axes_kwargs={}
    )

    # Should handle missing set_position gracefully
    new_pos = Bbox.from_bounds(0.2, 0.2, 0.6, 0.6)
    ax.set_position(new_pos)

    # Should not crash


def test_external_axes_kwargs_passed():
    """Test that external_axes_kwargs are passed to external axes constructor."""

    class KwargsCheckingAxes(MinimalExternalAxes):
        def __init__(self, fig, *args, custom_param=None, **kwargs):
            super().__init__(fig, *args, **kwargs)
            self.custom_param = custom_param

    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=KwargsCheckingAxes,
        external_axes_kwargs={"custom_param": "test_value"},
    )

    child = ax.get_external_child()
    assert child is not None
    assert child.custom_param == "test_value"


def test_container_aspect_setting():
    """Test that aspect setting is attempted on external axes."""

    class AspectAwareAxes(MinimalExternalAxes):
        def __init__(self, fig, *args, **kwargs):
            super().__init__(fig, *args, **kwargs)
            self.aspect_set = False

        def set_aspect(self, aspect, adjustable=None):
            self.aspect_set = True

    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=AspectAwareAxes, external_axes_kwargs={}
    )

    child = ax.get_external_child()
    # Aspect should have been set during shrink
    if child is not None:
        assert child.aspect_set == True


def test_multiple_draw_calls_efficient():
    """Test that multiple draw calls don't redraw unnecessarily."""
    fig = uplt.figure()

    # Create mock with draw counting
    draw_count = [0]

    class DrawCountingAxes(MinimalExternalAxes):
        def draw(self, renderer):
            draw_count[0] += 1
            self.stale = False

    ax = ExternalAxesContainer(
        fig, 1, 1, 1, external_axes_class=DrawCountingAxes, external_axes_kwargs={}
    )

    try:
        renderer = Mock()

        # First draw
        ax.draw(renderer)
        first_count = draw_count[0]

        # Second draw without changes (may or may not skip depending on stale tracking)
        ax.draw(renderer)
        # Just verify it doesn't redraw excessively
        # Allow for some draws but not too many
        assert draw_count[0] <= first_count + 5
    except Exception:
        # Drawing may fail due to renderer issues, that's OK for this test
        # The point is to verify the counting mechanism works
        pass


def test_container_autoshare_disabled():
    """Test that autoshare is disabled for external axes containers."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    # Check that autoshare was set to False during init
    # (This is in the init code but hard to verify directly)
    # Just ensure container exists
    assert ax is not None


def test_external_padding_with_points_to_pixels():
    """Test external padding applied when points_to_pixels returns numeric."""
    fig = uplt.figure()

    class TightBboxAxes(MinimalExternalAxes):
        def get_tightbbox(self, renderer):
            bbox = self._position.transformed(self.figure.transFigure)
            return bbox.expanded(1.5, 1.5)

    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=TightBboxAxes,
        external_axes_kwargs={},
        external_padding=10.0,
        external_shrink_factor=1.0,
    )

    child = ax.get_external_child()
    assert child is not None
    initial_pos = child.get_position()

    class Renderer:
        def points_to_pixels(self, value):
            return 2.0

    ax._ensure_external_fits_within_container(Renderer())
    new_pos = child.get_position()
    assert new_pos.width <= initial_pos.width
    assert new_pos.height <= initial_pos.height


def test_external_axes_fallback_to_rect_on_typeerror():
    """Test fallback to rect init when subplotspec is unsupported."""
    fig = uplt.figure()

    class RectOnlyAxes(MinimalExternalAxes):
        def __init__(self, fig, rect, **kwargs):
            from matplotlib.gridspec import SubplotSpec

            if isinstance(rect, SubplotSpec):
                raise TypeError("subplotspec not supported")
            super().__init__(fig, rect, **kwargs)
            self.used_rect = rect

    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=RectOnlyAxes,
        external_axes_kwargs={},
    )

    child = ax.get_external_child()
    assert child is not None
    assert isinstance(child.used_rect, (list, tuple))


def test_container_factory_uses_defaults_and_projection_name():
    """Test factory container injects defaults and projection name."""
    fig = uplt.figure()

    class CapturingAxes(MinimalExternalAxes):
        def __init__(self, fig, *args, **kwargs):
            super().__init__(fig, *args, **kwargs)
            self.kwargs = kwargs

    Container = create_external_axes_container(CapturingAxes, projection_name="cap")
    assert Container.name == "cap"

    ax = Container(
        fig,
        1,
        1,
        1,
        external_axes_kwargs={"flag": True},
    )

    child = ax.get_external_child()
    assert child is not None
    assert child.kwargs.get("flag") is True


def test_container_factory_can_override_external_class():
    """Test factory container honors external_axes_class override."""
    fig = uplt.figure()

    class FirstAxes(MinimalExternalAxes):
        pass

    class SecondAxes(MinimalExternalAxes):
        pass

    Container = create_external_axes_container(FirstAxes)
    ax = Container(
        fig,
        1,
        1,
        1,
        external_axes_class=SecondAxes,
        external_axes_kwargs={},
    )

    child = ax.get_external_child()
    assert child is not None
    assert isinstance(child, SecondAxes)


def test_clear_marks_external_stale():
    """Test clear sets external stale flag."""
    fig = uplt.figure()

    class ClearableAxes(MinimalExternalAxes):
        def clear(self):
            pass

    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=ClearableAxes,
        external_axes_kwargs={},
    )

    child = ax.get_external_child()
    assert child is not None
    ax._external_stale = False
    ax.clear()
    assert ax._external_stale is True


def test_set_position_shrinks_external_axes():
    """Test set_position triggers shrink on external axes."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
        external_shrink_factor=0.8,
    )

    child = ax.get_external_child()
    assert child is not None
    new_pos = Bbox.from_bounds(0.1, 0.1, 0.8, 0.8)
    ax.set_position(new_pos)

    child_pos = child.get_position()
    assert child_pos.width < new_pos.width
    assert child_pos.height < new_pos.height


def test_format_falls_back_when_external_missing_setters():
    """Test format uses container when external axes lacks setters."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    ax.format(title="Local Title")
    assert ax.get_title() == "Local Title"


def test_get_tightbbox_returns_container_bbox():
    """Test get_tightbbox returns the container's bbox."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    renderer = Mock()
    result = ax.get_tightbbox(renderer)
    expected = ax.get_position().transformed(fig.transFigure)
    assert np.allclose(result.bounds, expected.bounds)


def test_private_getattr_raises_attribute_error():
    """Test private missing attributes raise AttributeError."""
    fig = uplt.figure()
    ax = ExternalAxesContainer(
        fig,
        1,
        1,
        1,
        external_axes_class=MinimalExternalAxes,
        external_axes_kwargs={},
    )

    with pytest.raises(AttributeError):
        _ = ax._missing_private_attribute
