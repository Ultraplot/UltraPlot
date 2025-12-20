#!/usr/bin/env python3
"""
Container class for external axes (e.g., mpltern, cartopy custom axes).

This module provides the ExternalAxesContainer class which acts as a wrapper
around external axes classes, allowing them to be used within ultraplot's
figure system while maintaining their native functionality.
"""
import matplotlib.axes as maxes
import matplotlib.transforms as mtransforms
from matplotlib import cbook, container

from ..internals import _pop_rc, warnings
from .cartesian import CartesianAxes

__all__ = ["ExternalAxesContainer"]


class ExternalAxesContainer(CartesianAxes):
    """
    Container axes that wraps an external axes instance.

    This class inherits from ultraplot's CartesianAxes and creates/manages an external
    axes as a child. It provides ultraplot's interface while delegating
    drawing and interaction to the wrapped external axes.

    Parameters
    ----------
    *args
        Positional arguments passed to Axes.__init__
    external_axes_class : type
        The external axes class to instantiate (e.g., mpltern.TernaryAxes)
    external_axes_kwargs : dict, optional
        Keyword arguments to pass to the external axes constructor
    external_shrink_factor : float, optional, default: 0.75
        The factor by which to shrink the external axes within the container
        to leave room for labels. For ternary plots, labels extend significantly
        beyond the plot area, so a value of 0.75 (25% padding) helps prevent
        overlap with adjacent subplots.
    external_padding : float, optional, default: 5.0
        Padding in points to add around the external axes tight bbox. This creates
        space between the external axes and adjacent subplots, preventing overlap
        with tick labels or other elements. Set to 0 to disable padding.
    **kwargs
        Keyword arguments passed to Axes.__init__

    Notes
    -----
    When using external axes containers with multiple subplots, the external axes
    (e.g., ternary plots) are automatically shrunk to prevent label overlap with
    adjacent subplots. If you still experience overlap, you can:

    1. Increase spacing with ``wspace`` or ``hspace`` in subplots()
    2. Decrease ``external_shrink_factor`` (more aggressive shrinking)
    3. Use tight_layout or constrained_layout for automatic spacing

    Example: ``uplt.subplots(ncols=2, projection=('ternary', None), wspace=5)``

    To reduce padding between external axes and adjacent subplots, use:
    ``external_padding=2`` or ``external_padding=0`` to disable padding entirely.
    """

    def __init__(
        self, *args, external_axes_class=None, external_axes_kwargs=None, **kwargs
    ):
        """Initialize the container and create the external axes child."""
        # Initialize instance variables
        self._syncing_position = False
        self._external_axes = None
        self._last_external_position = None
        self._position_synced = False
        self._external_stale = True  # Track if external axes needs redrawing

        # Store external axes class and kwargs
        self._external_axes_class = external_axes_class
        self._external_axes_kwargs = external_axes_kwargs or {}

        # Store shrink factor for external axes (to fit labels)
        # Can be customized per-axes or set globally
        # Default 0.95 for ternary plots to prevent label overlap with adjacent subplots
        self._external_shrink_factor = kwargs.pop("external_shrink_factor", 0.95)

        # Store padding for tight bbox (prevents overlap with adjacent subplot elements)
        # Default 5 points (~7 pixels at 96 dpi)
        self._external_padding = kwargs.pop("external_padding", 5.0)

        # Pop the projection kwarg if it exists (matplotlib will add it)
        # We don't want to pass it to parent since we're using cartesian for container
        kwargs.pop("projection", None)

        # Pop format kwargs before passing to parent
        rc_kw, rc_mode = _pop_rc(kwargs)
        format_kwargs = {}

        # Extract common format parameters
        # Include both general format params and GeoAxes-specific params
        # to handle cases where GeoAxes might be incorrectly wrapped
        format_params = [
            "title",
            "ltitle",
            "ctitle",
            "rtitle",
            "ultitle",
            "uctitle",
            "urtitle",
            "lltitle",
            "lctitle",
            "lrtitle",
            "abc",
            "abcloc",
            "abcstyle",
            "abcformat",
            "xlabel",
            "ylabel",
            "xlim",
            "ylim",
            "aspect",
            "grid",
            "gridminor",
            # GeoAxes-specific parameters
            "extent",
            "map_projection",
            "lonlim",
            "latlim",
            "land",
            "ocean",
            "coast",
            "rivers",
            "borders",
            "innerborders",
            "lakes",
            "labels",
            "latlines",
            "lonlines",
            "latlabels",
            "lonlabels",
            "lonlocator",
            "latlocator",
            "lonformatter",
            "latformatter",
            "lonticklen",
            "latticklen",
            "gridminor",
            "round",
            "boundinglat",
        ]
        for param in format_params:
            if param in kwargs:
                format_kwargs[param] = kwargs.pop(param)

        # Initialize parent ultraplot Axes
        # Don't set projection here - the class itself is already the right projection
        # and matplotlib has already resolved it before instantiation
        # Note: _subplot_spec is handled by parent Axes.__init__, no need to pop/restore it

        # Disable autoshare for external axes containers since they manage
        # external axes that don't participate in ultraplot's sharing system
        kwargs.setdefault("autoshare", False)

        super().__init__(*args, **kwargs)

        # Make the container axes invisible (it's just a holder)
        # But keep it functional for layout purposes
        self.patch.set_visible(False)
        self.patch.set_facecolor("none")

        # Hide spines
        for spine in self.spines.values():
            spine.set_visible(False)

        # Hide axes
        self.xaxis.set_visible(False)
        self.yaxis.set_visible(False)

        # Hide axis labels explicitly
        self.set_xlabel("")
        self.set_ylabel("")
        self.xaxis.label.set_visible(False)
        self.yaxis.label.set_visible(False)

        # Hide tick labels
        self.tick_params(
            axis="both",
            which="both",
            labelbottom=False,
            labeltop=False,
            labelleft=False,
            labelright=False,
            bottom=False,
            top=False,
            left=False,
            right=False,
        )

        # Ensure container participates in layout
        self.set_frame_on(False)

        # Create the external axes as a child
        if external_axes_class is not None:
            self._create_external_axes()

            # Debug: verify external axes was created
            if self._external_axes is None:
                warnings._warn_ultraplot(
                    f"Failed to create external axes of type {external_axes_class.__name__}"
                )

        # Apply any format kwargs
        if format_kwargs:
            self.format(**format_kwargs)

    def _create_external_axes(self):
        """Create the external axes instance as a child of this container."""
        if self._external_axes_class is None:
            return

        # Get the figure
        fig = self.get_figure()
        if fig is None:
            warnings._warn_ultraplot("Cannot create external axes without a figure")
            return

        # Prepare kwargs for external axes
        external_kwargs = self._external_axes_kwargs.copy()

        # Get projection name
        projection_name = external_kwargs.pop("projection", None)

        # Get the subplot spec from the container
        subplotspec = self.get_subplotspec()

        # Direct instantiation of the external axes class
        try:
            # Most external axes expect (fig, *args, projection=name, **kwargs)
            # or use SubplotBase initialization with subplotspec
            if subplotspec is not None:
                # Try with subplotspec (standard matplotlib way)
                try:
                    # Don't pass projection= since the class is already the right projection
                    self._external_axes = self._external_axes_class(
                        fig, subplotspec, **external_kwargs
                    )
                except TypeError as e:
                    # Some axes might not accept subplotspec this way
                    # Try with rect instead
                    rect = self.get_position()
                    # Don't pass projection= since the class is already the right projection
                    self._external_axes = self._external_axes_class(
                        fig,
                        [rect.x0, rect.y0, rect.width, rect.height],
                        **external_kwargs,
                    )
            else:
                # No subplotspec, use position rect
                rect = self.get_position()
                # Don't pass projection= since the class is already the right projection
                self._external_axes = self._external_axes_class(
                    fig,
                    [rect.x0, rect.y0, rect.width, rect.height],
                    **external_kwargs,
                )

            # Note: Most axes classes automatically register themselves with the figure
            # during __init__. We need to REMOVE them from fig.axes so that ultraplot
            # doesn't try to call ultraplot-specific methods on them.
            # The container will handle all the rendering.
            if self._external_axes in fig.axes:
                fig.axes.remove(self._external_axes)

            # Ensure external axes is visible and has higher zorder than container
            if hasattr(self._external_axes, "set_visible"):
                self._external_axes.set_visible(True)
            if hasattr(self._external_axes, "set_zorder"):
                # Set higher zorder so external axes draws on top of container
                container_zorder = self.get_zorder()
                self._external_axes.set_zorder(container_zorder + 1)
            if hasattr(self._external_axes.patch, "set_visible"):
                self._external_axes.patch.set_visible(True)

            # Ensure the external axes patch has white background by default
            if hasattr(self._external_axes.patch, "set_facecolor"):
                self._external_axes.patch.set_facecolor("white")

            # Ensure all spines are visible
            if hasattr(self._external_axes, "spines"):
                for spine in self._external_axes.spines.values():
                    if hasattr(spine, "set_visible"):
                        spine.set_visible(True)

            # Ensure axes frame is on
            if hasattr(self._external_axes, "set_frame_on"):
                self._external_axes.set_frame_on(True)

            # Set subplotspec on the external axes if it has the method
            if subplotspec is not None and hasattr(
                self._external_axes, "set_subplotspec"
            ):
                self._external_axes.set_subplotspec(subplotspec)

            # Shrink external axes slightly to leave room for labels
            # This prevents labels from being cut off at figure edges
            self._shrink_external_for_labels()

            # Set up position synchronization
            self._sync_position_to_external()

            # Mark external axes as stale (needs drawing)
            self._external_stale = True

            # Note: Do NOT add external axes as a child artist to the container.
            # The container's draw() method explicitly handles drawing the external axes
            # (line ~514), and adding it as a child would cause matplotlib to draw it
            # twice - once via our explicit call and once via the parent's child iteration.
            # This double-draw is especially visible in REPL environments where figures
            # are displayed multiple times.

            # After creation, ensure external axes fits within container by measuring
            # This is done lazily on first draw to ensure renderer is available

        except Exception as e:
            warnings._warn_ultraplot(
                f"Failed to create external axes {self._external_axes_class.__name__}: {e}"
            )
            self._external_axes = None

    def _shrink_external_for_labels(self):
        """
        Shrink the external axes to leave room for labels that extend beyond the plot area.

        This is particularly important for ternary plots where axis labels can extend
        significantly beyond the triangular plot region.
        """
        if self._external_axes is None:
            return

        # Get the current position
        pos = self._external_axes.get_position()

        # Shrink to leave room for labels that extend beyond the plot area
        # For ternary axes, labels typically need about 5% padding (0.95 shrink factor)
        # This prevents label overlap with adjacent subplots
        # Use the configured shrink factor
        shrink_factor = getattr(self, "_external_shrink_factor", 0.95)

        # Calculate new dimensions
        new_width = pos.width * shrink_factor
        new_height = pos.height * shrink_factor

        # Align external axes to top of container (for alignment with adjacent subplots)
        # Offset slightly to the left to use available space better
        center_x = pos.x0 + pos.width / 2
        # Move 5% to the left from center
        new_x0 = center_x - new_width / 2 - pos.width * 0.05
        new_y0 = pos.y0 + pos.height - new_height

        # Set the new position
        from matplotlib.transforms import Bbox

        new_pos = Bbox.from_bounds(new_x0, new_y0, new_width, new_height)

        if hasattr(self._external_axes, "set_position"):
            self._external_axes.set_position(new_pos)

        # Also adjust aspect if the external axes has aspect control
        # This helps ternary axes maintain their triangular shape
        if hasattr(self._external_axes, "set_aspect"):
            try:
                self._external_axes.set_aspect("equal", adjustable="box")
            except Exception:
                pass  # Some axes types don't support aspect adjustment

    def _ensure_external_fits_within_container(self, renderer):
        """
        Iteratively shrink external axes until it fits completely within container bounds.

        This ensures that external axes labels don't extend beyond the container's
        allocated space and overlap with adjacent subplots.
        """
        if self._external_axes is None:
            return

        if not hasattr(self._external_axes, "get_tightbbox"):
            return

        # Get container bounds in display coordinates
        container_pos = self.get_position()
        container_bbox = container_pos.transformed(self.figure.transFigure)

        # Try up to 10 iterations to fit the external axes within container
        max_iterations = 10
        tolerance = 1.0  # 1 pixel tolerance

        for iteration in range(max_iterations):
            # Get external axes tight bbox (includes labels)
            ext_tight = self._external_axes.get_tightbbox(renderer)

            if ext_tight is None:
                break

            # Check if external axes extends beyond container
            extends_left = ext_tight.x0 < container_bbox.x0 - tolerance
            extends_right = ext_tight.x1 > container_bbox.x1 + tolerance
            extends_bottom = ext_tight.y0 < container_bbox.y0 - tolerance
            extends_top = ext_tight.y1 > container_bbox.y1 + tolerance

            if not (extends_left or extends_right or extends_bottom or extends_top):
                # Fits within container, we're done
                break

            # Calculate how much we need to shrink
            current_pos = self._external_axes.get_position()

            # Calculate shrink factors needed in each direction
            shrink_x = 1.0
            shrink_y = 1.0

            if extends_left or extends_right:
                # Need to shrink horizontally
                available_width = container_bbox.width
                needed_width = ext_tight.width
                if needed_width > 0:
                    shrink_x = min(0.95, available_width / needed_width * 0.95)

            if extends_bottom or extends_top:
                # Need to shrink vertically
                available_height = container_bbox.height
                needed_height = ext_tight.height
                if needed_height > 0:
                    shrink_y = min(0.95, available_height / needed_height * 0.95)

            # Use the more aggressive shrink factor
            shrink_factor = min(shrink_x, shrink_y)

            # Apply shrinking with top-aligned, left-offset positioning
            center_x = current_pos.x0 + current_pos.width / 2
            new_width = current_pos.width * shrink_factor
            new_height = current_pos.height * shrink_factor
            # Move 5% to the left from center
            new_x0 = center_x - new_width / 2 - current_pos.width * 0.05
            new_y0 = current_pos.y0 + current_pos.height - new_height

            from matplotlib.transforms import Bbox
            new_pos = Bbox.from_bounds(new_x0, new_y0, new_width, new_height)
            self._external_axes.set_position(new_pos)

            # Mark as stale to ensure it redraws with new position
            if hasattr(self._external_axes, "stale"):
                self._external_axes.stale = True

    def _sync_position_to_external(self):
        """Synchronize the container position to the external axes."""
        if self._external_axes is None:
            return

        # Copy position from container to external axes
        pos = self.get_position()
        if hasattr(self._external_axes, "set_position"):
            self._external_axes.set_position(pos)

    def set_position(self, pos, which="both"):
        """Override to sync position changes to external axes."""
        super().set_position(pos, which=which)
        # Only sync to external if not already syncing from external
        if not getattr(self, "_syncing_position", False):
            self._sync_position_to_external()
            # Invalidate position cache when manually setting position
            self._last_external_position = None
            self._position_synced = False
            self._external_stale = True  # Position change may affect drawing

    def _iter_axes(self, hidden=True, children=True, panels=True):
        """
        Override to only yield the container itself, not the external axes.

        The external axes is a rendering child, not a logical ultraplot child,
        so we don't want ultraplot's iteration to find it and call ultraplot
        methods on it.
        """
        # Only yield self (the container), never the external axes
        yield self

    # Plotting method delegation
    # Override common plotting methods to delegate to external axes
    def plot(self, *args, **kwargs):
        """Delegate plot to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.plot(*args, **kwargs)
        return super().plot(*args, **kwargs)

    def scatter(self, *args, **kwargs):
        """Delegate scatter to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.scatter(*args, **kwargs)
        return super().scatter(*args, **kwargs)

    def fill(self, *args, **kwargs):
        """Delegate fill to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.fill(*args, **kwargs)
        return super().fill(*args, **kwargs)

    def contour(self, *args, **kwargs):
        """Delegate contour to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.contour(*args, **kwargs)
        return super().contour(*args, **kwargs)

    def contourf(self, *args, **kwargs):
        """Delegate contourf to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.contourf(*args, **kwargs)
        return super().contourf(*args, **kwargs)

    def pcolormesh(self, *args, **kwargs):
        """Delegate pcolormesh to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.pcolormesh(*args, **kwargs)
        return super().pcolormesh(*args, **kwargs)

    def imshow(self, *args, **kwargs):
        """Delegate imshow to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.imshow(*args, **kwargs)
        return super().imshow(*args, **kwargs)

    def hexbin(self, *args, **kwargs):
        """Delegate hexbin to external axes."""
        if self._external_axes is not None:
            self._external_stale = True  # Mark for redraw
            return self._external_axes.hexbin(*args, **kwargs)
        return super().hexbin(*args, **kwargs)

    def get_external_axes(self):
        """
        Get the wrapped external axes instance.

        Returns
        -------
        axes
            The external axes instance, or None if not created
        """
        return self._external_axes

    def has_external_child(self):
        """
        Check if this container has an external axes child.

        Returns
        -------
        bool
            True if an external axes instance exists, False otherwise
        """
        return self._external_axes is not None

    def get_external_child(self):
        """
        Get the external axes child (alias for get_external_axes).

        Returns
        -------
        axes
            The external axes instance, or None if not created
        """
        return self.get_external_axes()

    def clear(self):
        """Clear the container and mark external axes as stale."""
        # Mark external axes as stale before clearing
        self._external_stale = True
        # Clear the container
        super().clear()
        # If we have external axes, clear it too
        if self._external_axes is not None:
            self._external_axes.clear()

    def format(self, **kwargs):
        """
        Format the container and delegate to external axes where appropriate.

        This method handles ultraplot-specific formatting on the container
        and attempts to delegate common parameters to the external axes.

        Parameters
        ----------
        **kwargs
            Formatting parameters. Common matplotlib parameters (title, xlabel,
            ylabel, xlim, ylim) are delegated to the external axes if supported.
        """
        # Separate kwargs into container and external
        external_kwargs = {}
        container_kwargs = {}

        # Parameters that can be delegated to external axes
        delegatable = ["title", "xlabel", "ylabel", "xlim", "ylim"]

        for key, value in kwargs.items():
            if key in delegatable and self._external_axes is not None:
                # Check if external axes has the method
                method_name = f"set_{key}"
                if hasattr(self._external_axes, method_name):
                    external_kwargs[key] = value
                else:
                    container_kwargs[key] = value
            else:
                container_kwargs[key] = value

        # Apply container formatting (for ultraplot-specific features)
        if container_kwargs:
            super().format(**container_kwargs)

        # Apply external axes formatting
        if external_kwargs and self._external_axes is not None:
            self._external_axes.set(**external_kwargs)

    def draw(self, renderer):
        """Override draw to render container (with abc/titles) and external axes."""
        # Draw external axes first - it may adjust its own position for labels
        if self._external_axes is not None:
            # Check if external axes is stale (needs redrawing)
            # This avoids redundant draws on external axes that haven't changed
            external_stale = getattr(self._external_axes, "stale", True)

            # Only draw if external axes is stale or we haven't synced positions yet
            if external_stale or not self._position_synced or self._external_stale:
                # First, ensure external axes fits within container bounds
                # This prevents labels from overlapping with adjacent subplots
                self._ensure_external_fits_within_container(renderer)

                self._external_axes.draw(renderer)
                self._external_stale = False

                # Sync container position to external axes if needed
                # This ensures abc labels and titles are positioned correctly
                ext_pos = self._external_axes.get_position()

                # Quick check if position changed since last draw
                position_changed = False
                if self._last_external_position is None:
                    position_changed = True
                else:
                    last_pos = self._last_external_position
                    # Use a slightly larger tolerance to avoid excessive sync calls
                    if (
                        abs(ext_pos.x0 - last_pos.x0) > 0.001
                        or abs(ext_pos.y0 - last_pos.y0) > 0.001
                        or abs(ext_pos.width - last_pos.width) > 0.001
                        or abs(ext_pos.height - last_pos.height) > 0.001
                    ):
                        position_changed = True

                # Only update if position actually changed
                if position_changed:
                    container_pos = self.get_position()

                    # Check if container needs updating
                    if (
                        abs(container_pos.x0 - ext_pos.x0) > 0.001
                        or abs(container_pos.y0 - ext_pos.y0) > 0.001
                        or abs(container_pos.width - ext_pos.width) > 0.001
                        or abs(container_pos.height - ext_pos.height) > 0.001
                    ):
                        # Temporarily disable position sync to avoid recursion
                        self._syncing_position = True
                        self.set_position(ext_pos)
                        self._syncing_position = False

                    # Cache the current external position
                    self._last_external_position = ext_pos
                    self._position_synced = True

        # Draw the container (with abc labels, titles, etc.)
        super().draw(renderer)

    def stale_callback(self, *args, **kwargs):
        """Mark external axes as stale when container is marked stale."""
        # When container is marked stale, mark external axes as stale too
        if self._external_axes is not None:
            self._external_stale = True
        # Call parent stale callback if it exists
        if hasattr(super(), "stale_callback"):
            super().stale_callback(*args, **kwargs)

    def get_tightbbox(self, renderer, *args, **kwargs):
        """
        Override to return the container bbox for consistent layout positioning.

        By returning the container's bbox, we ensure the layout engine positions
        the container properly within the subplot grid, and we rely on our
        iterative shrinking to ensure the external axes fits within the container.
        """
        # Simply return the container's position bbox
        # This gives the layout engine a symmetric, predictable bbox to work with
        container_pos = self.get_position()
        container_bbox = container_pos.transformed(self.figure.transFigure)
        return container_bbox

    def __getattr__(self, name):
        """
        Delegate attribute access to the external axes when not found on container.

        This allows the container to act as a transparent wrapper, forwarding
        plotting methods and other attributes to the external axes.
        """
        # Avoid infinite recursion for private attributes
        # But allow parent class lookups during initialization
        if name.startswith("_"):
            # During initialization, let parent class handle private attributes
            # This prevents interfering with parent class setup
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Try to get from external axes if it exists
        if hasattr(self, "_external_axes") and self._external_axes is not None:
            try:
                return getattr(self._external_axes, name)
            except AttributeError:
                pass

        # Not found anywhere
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __dir__(self):
        """Include external axes attributes in dir() output."""
        attrs = set(super().__dir__())
        if self._external_axes is not None:
            attrs.update(dir(self._external_axes))
        return sorted(attrs)


def create_external_axes_container(external_axes_class, projection_name=None):
    """
    Factory function to create a container class for a specific external axes type.

    Parameters
    ----------
    external_axes_class : type
        The external axes class to wrap
    projection_name : str, optional
        The projection name to register with matplotlib

    Returns
    -------
    type
        A subclass of ExternalAxesContainer configured for the external axes class
    """

    class SpecificContainer(ExternalAxesContainer):
        """Container for {external_axes_class.__name__}"""

        def __init__(self, *args, **kwargs):
            # Pop external_axes_class and external_axes_kwargs if passed in kwargs
            # (they're passed from Figure._add_subplot)
            ext_class = kwargs.pop("external_axes_class", None)
            ext_kwargs = kwargs.pop("external_axes_kwargs", None)

            # Pop projection - it's already been handled and shouldn't be passed to parent
            kwargs.pop("projection", None)

            # Use the provided class or fall back to the factory default
            if ext_class is None:
                ext_class = external_axes_class
            if ext_kwargs is None:
                ext_kwargs = {}

            # Inject the external axes class
            kwargs["external_axes_class"] = ext_class
            kwargs["external_axes_kwargs"] = ext_kwargs
            super().__init__(*args, **kwargs)

    # Set proper name and module
    SpecificContainer.__name__ = f"{external_axes_class.__name__}Container"
    SpecificContainer.__qualname__ = f"{external_axes_class.__name__}Container"
    if projection_name:
        SpecificContainer.name = projection_name

    return SpecificContainer
