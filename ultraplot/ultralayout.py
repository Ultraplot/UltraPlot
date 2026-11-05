#!/usr/bin/env python3
"""
UltraLayout: Advanced constraint-based layout system for non-orthogonal subplot arrangements.

This module provides UltraPlot's constraint-based layout computation for subplot grids
that don't follow simple orthogonal patterns, such as [[1, 1, 2, 2], [0, 3, 3, 0]]
where subplot 3 should be nicely centered between subplots 1 and 2.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from .internals import _alias_kwargs

try:
    from kiwisolver import Solver, Variable

    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False
    Variable = None
    Solver = None


__all__ = [
    "ColorbarLayoutSolver",
    "UltraLayoutSolver",
    "compute_ultra_positions",
    "get_grid_positions_ultra",
    "is_orthogonal_layout",
]


def is_orthogonal_layout(array: np.ndarray) -> bool:
    """
    Check if a subplot array follows an orthogonal (grid-aligned) layout.

    An orthogonal layout is one where every subplot's edges align with
    other subplots' edges, forming a simple grid.

    Parameters
    ----------
    array : np.ndarray
        2D array of subplot numbers (with 0 for empty cells)

    Returns
    -------
    bool
        True if layout is orthogonal, False otherwise
    """
    if array.size == 0:
        return True

    # Get unique subplot numbers (excluding 0)
    subplot_nums = np.unique(array[array != 0])

    if len(subplot_nums) == 0:
        return True

    # Reject layouts with interior gaps (zeros surrounded by non-zero rows/cols).
    row_has = np.any(array != 0, axis=1)
    col_has = np.any(array != 0, axis=0)
    if np.any((array == 0) & row_has[:, None] & col_has[None, :]):
        return False

    # For each subplot, get its bounding box
    bboxes = {}
    for num in subplot_nums:
        rows, cols = np.where(array == num)
        bboxes[num] = {
            "row_min": rows.min(),
            "row_max": rows.max(),
            "col_min": cols.min(),
            "col_max": cols.max(),
        }

    # Check if layout is orthogonal by verifying that all vertical and
    # horizontal edges align with cell boundaries
    # A more sophisticated check: for each row/col boundary, check if
    # all subplots either cross it or are completely on one side

    # Collect all unique row and column boundaries
    row_boundaries = set()
    col_boundaries = set()

    for bbox in bboxes.values():
        row_boundaries.add(bbox["row_min"])
        row_boundaries.add(bbox["row_max"] + 1)
        col_boundaries.add(bbox["col_min"])
        col_boundaries.add(bbox["col_max"] + 1)

    # Check if these boundaries create a consistent grid
    # For orthogonal layout, we should be able to split the grid
    # using these boundaries such that each subplot is a union of cells

    row_boundaries = sorted(row_boundaries)
    col_boundaries = sorted(col_boundaries)

    # Create a refined grid
    refined_rows = len(row_boundaries) - 1
    refined_cols = len(col_boundaries) - 1

    if refined_rows == 0 or refined_cols == 0:
        return True

    # Map each subplot to refined grid cells
    for num in subplot_nums:
        rows, cols = np.where(array == num)

        # Check if this subplot occupies a rectangular region in the refined grid
        refined_row_indices = set()
        refined_col_indices = set()

        for r in rows:
            for i, (r_start, r_end) in enumerate(
                zip(row_boundaries[:-1], row_boundaries[1:])
            ):
                if r_start <= r < r_end:
                    refined_row_indices.add(i)

        for c in cols:
            for i, (c_start, c_end) in enumerate(
                zip(col_boundaries[:-1], col_boundaries[1:])
            ):
                if c_start <= c < c_end:
                    refined_col_indices.add(i)

        # Check if indices form a rectangle
        if refined_row_indices and refined_col_indices:
            r_min, r_max = min(refined_row_indices), max(refined_row_indices)
            c_min, c_max = min(refined_col_indices), max(refined_col_indices)

            expected_cells = (r_max - r_min + 1) * (c_max - c_min + 1)
            actual_cells = len(refined_row_indices) * len(refined_col_indices)

            if expected_cells != actual_cells:
                return False

    return True


def _solve_axis_sizes(
    array,
    axis,
    ratios,
    panels,
    spaces,
    *,
    total=None,
    reference=None,
    reference_size=None,
):
    """Size grid tracks by their visible subplot spans, in physical units.

    Panel tracks and gaps have fixed sizes. Ordinary tracks are subdivisions
    of axes, not necessarily axes themselves: constraining their ratios would
    let a gap or a panel inside a span change the size of that subplot.

    Constrain the smallest subplot intervals to a common scale instead. A
    larger interval containing these intervals inherits their sizes and the
    intervening gaps, as in a conventional spanning subplot. The reference
    span or the total extent fixes the scale. Any remaining freedom is resolved
    by a least-squares preference for the original track ratios; this treats
    equivalent left/right (or top/bottom) subdivisions symmetrically.
    """
    ratios = np.asarray(ratios, dtype=float)
    panels = np.asarray(panels, dtype=bool)
    spaces = np.asarray(spaces, dtype=float)
    ordinary = np.flatnonzero(~panels)
    fixed = np.where(panels, ratios, 0.0)
    intervals = set()
    for num in np.unique(array[array != 0]):
        indices = np.where(array == num)[axis]
        intervals.add((int(indices.min()), int(indices.max())))
    minimal = [
        (lo, hi)
        for lo, hi in sorted(intervals)
        if not any(lo <= a <= b <= hi and (a, b) != (lo, hi) for a, b in intervals)
    ]
    # Empty tracks still participate in the layout and retain their ratios.
    if not minimal:
        minimal = [(int(i), int(i)) for i in ordinary]

    # Regular grids (including larger axes spanning a stack of smaller ones)
    # have a scalar solution. Avoid a matrix decomposition on the common path.
    if minimal == [(int(i), int(i)) for i in ordinary]:
        if reference_size is None:
            scale = (total - fixed.sum() - spaces.sum()) / ratios[ordinary].sum()
        else:
            lo, hi = reference
            mask = (ordinary >= lo) & (ordinary <= hi)
            offset = fixed[lo : hi + 1].sum() + spaces[lo:hi].sum()
            scale = (reference_size - offset) / ratios[ordinary[mask]].sum()
        fixed[ordinary] = ratios[ordinary] * scale
        return fixed

    def span(lo, hi):
        mask = (ordinary >= lo) & (ordinary <= hi)
        row = np.zeros(len(ordinary) + 1)
        row[:-1] = mask
        offset = fixed[lo : hi + 1].sum() + spaces[lo:hi].sum()
        return row, offset, ratios[ordinary[mask]].sum()

    rows, values = [], []
    for lo, hi in minimal:
        row, offset, weight = span(lo, hi)
        if not weight:
            continue
        row[-1] = -weight
        rows.append(row)
        values.append(-offset)
    if reference_size is None:
        row, offset, _ = span(0, len(ratios) - 1)
        value = total - offset
    else:
        row, offset, _ = span(*reference)
        value = reference_size - offset
    rows.append(row)
    values.append(value)
    matrix = np.asarray(rows)
    values = np.asarray(values)
    solution, _, rank, _ = np.linalg.lstsq(matrix, values, rcond=None)
    # Minimize track-ratio error within the null space of the span constraints,
    # rather than weakening the physical reference-size or spacing constraints.
    if rank < matrix.shape[1]:
        _, _, vectors = np.linalg.svd(matrix, full_matrices=True)
        null = vectors[rank:].T
        preference = np.column_stack((np.eye(len(ordinary)), -ratios[ordinary]))
        correction = np.linalg.lstsq(
            preference @ null, -preference @ solution, rcond=None
        )[0]
        solution += null @ correction
    if not np.allclose(matrix @ solution, values, rtol=1e-9, atol=1e-9):
        raise ValueError("Inconsistent subplot span sizes.")
    fixed[ordinary] = solution[:-1]
    return fixed


class UltraLayoutSolver:
    """
    UltraLayout: Constraint-based layout solver using kiwisolver for subplot positioning.

    This solver computes aesthetically pleasing positions for subplots in
    non-orthogonal arrangements by using constraint satisfaction, providing
    a superior layout experience for complex subplot arrangements.
    """

    @_alias_kwargs("gridspec")
    def __init__(
        self,
        array: np.ndarray,
        figwidth: float = 10.0,
        figheight: float = 8.0,
        wspace: Optional[List[float]] = None,
        hspace: Optional[List[float]] = None,
        left: float = 0.125,
        right: float = 0.125,
        top: float = 0.125,
        bottom: float = 0.125,
        width_ratios: Optional[List[float]] = None,
        height_ratios: Optional[List[float]] = None,
        wpanels: Optional[List[bool]] = None,
        hpanels: Optional[List[bool]] = None,
    ):
        """
        Initialize the UltraLayout solver.

        Parameters
        ----------
        array : np.ndarray
            2D array of subplot numbers (with 0 for empty cells)
        figwidth, figheight : float
            Figure dimensions in inches
        wspace, hspace : list of float, optional
            Spacing between columns and rows in inches
        left, right, top, bottom : float
            Margins in inches
        width_ratios, height_ratios : list of float, optional
            Width and height ratios for columns and rows
        wpanels, hpanels : list of bool, optional
            Flags indicating panel columns or rows with fixed widths/heights.
        """
        if not KIWI_AVAILABLE:
            raise ImportError(
                "kiwisolver is required for non-orthogonal layouts. "
                "Install it with: pip install kiwisolver"
            )

        self.array = array
        self.nrows, self.ncols = array.shape
        self.figwidth = figwidth
        self.figheight = figheight
        self.left_margin = left
        self.right_margin = right
        self.top_margin = top
        self.bottom_margin = bottom

        # Get subplot numbers
        self.subplot_nums = sorted(np.unique(array[array != 0]))

        # Set up spacing
        if wspace is None:
            self.wspace = [0.2] * (self.ncols - 1) if self.ncols > 1 else []
        else:
            self.wspace = list(wspace)

        if hspace is None:
            self.hspace = [0.2] * (self.nrows - 1) if self.nrows > 1 else []
        else:
            self.hspace = list(hspace)

        # Set up ratios
        if width_ratios is None:
            self.wratios = [1.0] * self.ncols
        else:
            self.wratios = list(width_ratios)

        if height_ratios is None:
            self.hratios = [1.0] * self.nrows
        else:
            self.hratios = list(height_ratios)

        # Set up panel flags (True for fixed-width panel slots).
        if wpanels is None:
            self.wpanels = [False] * self.ncols
        else:
            if len(wpanels) != self.ncols:
                raise ValueError("wpanels length must match number of columns.")
            self.wpanels = [bool(val) for val in wpanels]
        if hpanels is None:
            self.hpanels = [False] * self.nrows
        else:
            if len(hpanels) != self.nrows:
                raise ValueError("hpanels length must match number of rows.")
            self.hpanels = [bool(val) for val in hpanels]

        # Initialize solver
        self.solver = Solver()
        self._setup_variables()
        self._setup_constraints()

    def _setup_variables(self):
        """Create kiwisolver variables for all grid lines."""
        # Vertical lines (left edges of columns + right edge of last column)
        self.col_lefts = [Variable(f"col_{i}_left") for i in range(self.ncols)]
        self.col_rights = [Variable(f"col_{i}_right") for i in range(self.ncols)]

        # Horizontal lines (top edges of rows + bottom edge of last row)
        # Note: in figure coordinates, top is higher value
        self.row_tops = [Variable(f"row_{i}_top") for i in range(self.nrows)]
        self.row_bottoms = [Variable(f"row_{i}_bottom") for i in range(self.nrows)]

    def _setup_constraints(self):
        """Set up all constraints for the layout."""
        # 1. Figure boundary constraints
        self.solver.addConstraint(self.col_lefts[0] == self.left_margin / self.figwidth)
        self.solver.addConstraint(
            self.col_rights[-1] == 1.0 - self.right_margin / self.figwidth
        )
        self.solver.addConstraint(
            self.row_bottoms[-1] == self.bottom_margin / self.figheight
        )
        self.solver.addConstraint(
            self.row_tops[0] == 1.0 - self.top_margin / self.figheight
        )

        # 2. Column continuity and spacing constraints
        for i in range(self.ncols - 1):
            # Right edge of column i connects to left edge of column i+1 with spacing
            spacing = self.wspace[i] / self.figwidth if i < len(self.wspace) else 0
            self.solver.addConstraint(
                self.col_rights[i] + spacing == self.col_lefts[i + 1]
            )

        # 3. Row continuity and spacing constraints
        for i in range(self.nrows - 1):
            # Bottom edge of row i connects to top edge of row i+1 with spacing
            spacing = self.hspace[i] / self.figheight if i < len(self.hspace) else 0
            self.solver.addConstraint(
                self.row_bottoms[i] == self.row_tops[i + 1] + spacing
            )

        # Size visible subplot spans, including any fixed slots inside them.
        widths = _solve_axis_sizes(
            self.array,
            1,
            self.wratios,
            self.wpanels,
            self.wspace,
            total=self.figwidth - self.left_margin - self.right_margin,
        )
        heights = _solve_axis_sizes(
            self.array,
            0,
            self.hratios,
            self.hpanels,
            self.hspace,
            total=self.figheight - self.top_margin - self.bottom_margin,
        )
        for i, width in enumerate(widths / self.figwidth):
            self.solver.addConstraint(self.col_rights[i] == self.col_lefts[i] + width)
        for i, height in enumerate(heights / self.figheight):
            self.solver.addConstraint(self.row_tops[i] == self.row_bottoms[i] + height)

    def solve(self) -> Dict[int, Tuple[float, float, float, float]]:
        """
        Solve the constraint system and return subplot positions.

        Returns
        -------
        dict
            Dictionary mapping subplot numbers to (left, bottom, width, height)
            in figure-relative coordinates [0, 1]
        """
        # Solve the constraint system
        self.solver.updateVariables()

        # Extract positions for each subplot
        positions = {}
        col_lefts = [v.value() for v in self.col_lefts]
        col_rights = [v.value() for v in self.col_rights]
        row_tops = [v.value() for v in self.row_tops]
        row_bottoms = [v.value() for v in self.row_bottoms]

        for num in self.subplot_nums:
            rows, cols = np.where(self.array == num)
            row_min, row_max = rows.min(), rows.max()
            col_min, col_max = cols.min(), cols.max()

            # Get the bounding box from the grid lines
            left = col_lefts[col_min]
            right = max(left, col_rights[col_max])
            bottom = row_bottoms[row_max]
            top = max(bottom, row_tops[row_min])

            # Tight margins can exhaust a fixed-size figure (e.g. a title
            # wider than the canvas). Match SubplotSpec's legacy behavior:
            # collapse the visible axes instead of reversing its transform.
            # Do not clamp individual tracks: these are virtual subdivisions
            # and can be negative while their containing subplot stays valid.

            width = right - left
            height = top - bottom

            positions[num] = (left, bottom, width, height)

        return positions


class ColorbarLayoutSolver:
    """
    Constraint-based solver for inset colorbar frame alignment.
    """

    def __init__(
        self,
        loc: str,
        cb_width: float,
        cb_height: float,
        pad_left: float,
        pad_right: float,
        pad_bottom: float,
        pad_top: float,
    ):
        if not KIWI_AVAILABLE:
            raise ImportError(
                "kiwisolver is required for constraint-based colorbar layout. "
                "Install it with: pip install kiwisolver"
            )
        self.loc = loc
        self.cb_width = cb_width
        self.cb_height = cb_height
        self.pad_left = pad_left
        self.pad_right = pad_right
        self.pad_bottom = pad_bottom
        self.pad_top = pad_top
        self.frame_width = pad_left + cb_width + pad_right
        self.frame_height = pad_bottom + cb_height + pad_top

        self.solver = Solver()
        self.xframe = Variable("cb_frame_x")
        self.yframe = Variable("cb_frame_y")
        self.cb_x = Variable("cb_x")
        self.cb_y = Variable("cb_y")
        self._setup_constraints()

    def _setup_constraints(self):
        self.solver.addConstraint(self.cb_x == self.xframe + self.pad_left)
        self.solver.addConstraint(self.cb_y == self.yframe + self.pad_bottom)
        self.solver.addConstraint(self.xframe >= 0)
        self.solver.addConstraint(self.yframe >= 0)
        self.solver.addConstraint(self.xframe + self.frame_width <= 1)
        self.solver.addConstraint(self.yframe + self.frame_height <= 1)

        loc = self.loc or "lower right"
        if loc not in ("upper right", "upper left", "lower left", "lower right"):
            loc = "lower right"
        if "left" in loc:
            self.solver.addConstraint(self.xframe == 0)
        elif "right" in loc:
            self.solver.addConstraint(self.xframe + self.frame_width == 1)
        if "upper" in loc:
            self.solver.addConstraint(self.yframe + self.frame_height == 1)
        elif "lower" in loc:
            self.solver.addConstraint(self.yframe == 0)

    def solve(self) -> Dict[str, Tuple[float, float, float, float]]:
        """
        Solve the constraint system and return inset and frame bounds.
        """
        self.solver.updateVariables()
        xframe = self.xframe.value()
        yframe = self.yframe.value()
        cb_x = self.cb_x.value()
        cb_y = self.cb_y.value()
        return {
            "frame": (xframe, yframe, self.frame_width, self.frame_height),
            "inset": (cb_x, cb_y, self.cb_width, self.cb_height),
        }


@_alias_kwargs("gridspec")
def compute_ultra_positions(
    array: np.ndarray,
    figwidth: float = 10.0,
    figheight: float = 8.0,
    wspace: Optional[List[float]] = None,
    hspace: Optional[List[float]] = None,
    left: float = 0.125,
    right: float = 0.125,
    top: float = 0.125,
    bottom: float = 0.125,
    width_ratios: Optional[List[float]] = None,
    height_ratios: Optional[List[float]] = None,
    wpanels: Optional[List[bool]] = None,
    hpanels: Optional[List[bool]] = None,
) -> Dict[int, Tuple[float, float, float, float]]:
    """
    Compute subplot positions using UltraLayout for non-orthogonal layouts.

    Parameters
    ----------
    array : np.ndarray
        2D array of subplot numbers (with 0 for empty cells)
    figwidth, figheight : float
        Figure dimensions in inches
    wspace, hspace : list of float, optional
        Spacing between columns and rows in inches
    left, right, top, bottom : float
        Margins in inches
    width_ratios, height_ratios : list of float, optional
        Width and height ratios for columns and rows
    wpanels, hpanels : list of bool, optional
        Flags indicating panel columns or rows with fixed widths/heights.

    Returns
    -------
    dict
        Dictionary mapping subplot numbers to (left, bottom, width, height)
        in figure-relative coordinates [0, 1]

    Examples
    --------
    >>> array = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    >>> positions = compute_ultra_positions(array)
    >>> positions[3]  # Position of subplot 3
    (0.25, 0.125, 0.5, 0.35)
    """
    solver = UltraLayoutSolver(
        array,
        figwidth,
        figheight,
        wspace,
        hspace,
        left,
        right,
        top,
        bottom,
        width_ratios,
        height_ratios,
        wpanels,
        hpanels,
    )
    return solver.solve()


@_alias_kwargs("gridspec")
def get_grid_positions_ultra(
    array: np.ndarray,
    figwidth: float,
    figheight: float,
    wspace: Optional[List[float]] = None,
    hspace: Optional[List[float]] = None,
    left: float = 0.125,
    right: float = 0.125,
    top: float = 0.125,
    bottom: float = 0.125,
    width_ratios: Optional[List[float]] = None,
    height_ratios: Optional[List[float]] = None,
    wpanels: Optional[List[bool]] = None,
    hpanels: Optional[List[bool]] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Get grid line positions using UltraLayout.

    This returns arrays of grid line positions similar to GridSpec.get_grid_positions(),
    but computed using UltraLayout's constraint satisfaction for better handling of non-orthogonal layouts.

    Parameters
    ----------
    array : np.ndarray
        2D array of subplot numbers
    figwidth, figheight : float
        Figure dimensions in inches
    wspace, hspace : list of float, optional
        Spacing between columns and rows in inches
    left, right, top, bottom : float
        Margins in inches
    width_ratios, height_ratios : list of float, optional
        Width and height ratios for columns and rows
    wpanels, hpanels : list of bool, optional
        Flags indicating panel columns or rows with fixed widths/heights.

    Returns
    -------
    bottoms, tops, lefts, rights : np.ndarray
        Arrays of grid line positions for each cell
    """
    solver = UltraLayoutSolver(
        array,
        figwidth,
        figheight,
        wspace,
        hspace,
        left,
        right,
        top,
        bottom,
        width_ratios,
        height_ratios,
        wpanels,
        hpanels,
    )
    solver.solver.updateVariables()

    # Extract grid line positions
    lefts = np.array([v.value() for v in solver.col_lefts])
    rights = np.array([v.value() for v in solver.col_rights])
    tops = np.array([v.value() for v in solver.row_tops])
    bottoms = np.array([v.value() for v in solver.row_bottoms])

    return bottoms, tops, lefts, rights
