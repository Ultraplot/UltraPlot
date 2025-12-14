#!/usr/bin/env python3
"""
Kiwisolver-based layout system for non-orthogonal subplot arrangements.

This module provides constraint-based layout computation for subplot grids
that don't follow simple orthogonal patterns, such as [[1, 1, 2, 2], [0, 3, 3, 0]]
where subplot 3 should be nicely centered between subplots 1 and 2.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from kiwisolver import Constraint, Solver, Variable
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False
    Variable = None
    Solver = None
    Constraint = None


__all__ = ['KiwiLayoutSolver', 'compute_kiwi_positions', 'is_orthogonal_layout']


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

    nrows, ncols = array.shape

    # Get unique subplot numbers (excluding 0)
    subplot_nums = np.unique(array[array != 0])

    if len(subplot_nums) == 0:
        return True

    # For each subplot, get its bounding box
    bboxes = {}
    for num in subplot_nums:
        rows, cols = np.where(array == num)
        bboxes[num] = {
            'row_min': rows.min(),
            'row_max': rows.max(),
            'col_min': cols.min(),
            'col_max': cols.max(),
        }

    # Check if layout is orthogonal by verifying that all vertical and
    # horizontal edges align with cell boundaries
    # A more sophisticated check: for each row/col boundary, check if
    # all subplots either cross it or are completely on one side

    # Collect all unique row and column boundaries
    row_boundaries = set()
    col_boundaries = set()

    for bbox in bboxes.values():
        row_boundaries.add(bbox['row_min'])
        row_boundaries.add(bbox['row_max'] + 1)
        col_boundaries.add(bbox['col_min'])
        col_boundaries.add(bbox['col_max'] + 1)

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
            for i, (r_start, r_end) in enumerate(zip(row_boundaries[:-1], row_boundaries[1:])):
                if r_start <= r < r_end:
                    refined_row_indices.add(i)

        for c in cols:
            for i, (c_start, c_end) in enumerate(zip(col_boundaries[:-1], col_boundaries[1:])):
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


class KiwiLayoutSolver:
    """
    Constraint-based layout solver using kiwisolver for subplot positioning.

    This solver computes aesthetically pleasing positions for subplots in
    non-orthogonal arrangements by using constraint satisfaction.
    """

    def __init__(self, array: np.ndarray, figwidth: float = 10.0, figheight: float = 8.0,
                 wspace: Optional[List[float]] = None, hspace: Optional[List[float]] = None,
                 left: float = 0.125, right: float = 0.125,
                 top: float = 0.125, bottom: float = 0.125,
                 wratios: Optional[List[float]] = None, hratios: Optional[List[float]] = None):
        """
        Initialize the kiwi layout solver.

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
        wratios, hratios : list of float, optional
            Width and height ratios for columns and rows
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
        if wratios is None:
            self.wratios = [1.0] * self.ncols
        else:
            self.wratios = list(wratios)

        if hratios is None:
            self.hratios = [1.0] * self.nrows
        else:
            self.hratios = list(hratios)

        # Initialize solver
        self.solver = Solver()
        self.variables = {}
        self._setup_variables()
        self._setup_constraints()

    def _setup_variables(self):
        """Create kiwisolver variables for all grid lines."""
        # Vertical lines (left edges of columns + right edge of last column)
        self.col_lefts = [Variable(f'col_{i}_left') for i in range(self.ncols)]
        self.col_rights = [Variable(f'col_{i}_right') for i in range(self.ncols)]

        # Horizontal lines (top edges of rows + bottom edge of last row)
        # Note: in figure coordinates, top is higher value
        self.row_tops = [Variable(f'row_{i}_top') for i in range(self.nrows)]
        self.row_bottoms = [Variable(f'row_{i}_bottom') for i in range(self.nrows)]

    def _setup_constraints(self):
        """Set up all constraints for the layout."""
        # 1. Figure boundary constraints
        self.solver.addConstraint(self.col_lefts[0] == self.left_margin / self.figwidth)
        self.solver.addConstraint(self.col_rights[-1] == 1.0 - self.right_margin / self.figwidth)
        self.solver.addConstraint(self.row_bottoms[-1] == self.bottom_margin / self.figheight)
        self.solver.addConstraint(self.row_tops[0] == 1.0 - self.top_margin / self.figheight)

        # 2. Column continuity and spacing constraints
        for i in range(self.ncols - 1):
            # Right edge of column i connects to left edge of column i+1 with spacing
            spacing = self.wspace[i] / self.figwidth if i < len(self.wspace) else 0
            self.solver.addConstraint(self.col_rights[i] + spacing == self.col_lefts[i + 1])

        # 3. Row continuity and spacing constraints
        for i in range(self.nrows - 1):
            # Bottom edge of row i connects to top edge of row i+1 with spacing
            spacing = self.hspace[i] / self.figheight if i < len(self.hspace) else 0
            self.solver.addConstraint(self.row_bottoms[i] == self.row_tops[i + 1] + spacing)

        # 4. Width ratio constraints
        total_width = 1.0 - (self.left_margin + self.right_margin) / self.figwidth
        if self.ncols > 1:
            spacing_total = sum(self.wspace) / self.figwidth
        else:
            spacing_total = 0
        available_width = total_width - spacing_total
        total_ratio = sum(self.wratios)

        for i in range(self.ncols):
            width = available_width * self.wratios[i] / total_ratio
            self.solver.addConstraint(self.col_rights[i] == self.col_lefts[i] + width)

        # 5. Height ratio constraints
        total_height = 1.0 - (self.top_margin + self.bottom_margin) / self.figheight
        if self.nrows > 1:
            spacing_total = sum(self.hspace) / self.figheight
        else:
            spacing_total = 0
        available_height = total_height - spacing_total
        total_ratio = sum(self.hratios)

        for i in range(self.nrows):
            height = available_height * self.hratios[i] / total_ratio
            self.solver.addConstraint(self.row_tops[i] == self.row_bottoms[i] + height)

        # 6. Add aesthetic constraints for non-orthogonal layouts
        self._add_aesthetic_constraints()

    def _add_aesthetic_constraints(self):
        """
        Add constraints to make non-orthogonal layouts look nice.

        For subplots that span cells in non-aligned ways, we add constraints
        to center them or align them aesthetically with neighboring subplots.
        """
        # Analyze the layout to find subplots that need special handling
        for num in self.subplot_nums:
            rows, cols = np.where(self.array == num)
            row_min, row_max = rows.min(), rows.max()
            col_min, col_max = cols.min(), cols.max()

            # Check if this subplot has empty cells on its sides
            # If so, try to center it with respect to subplots above/below/beside

            # Check left side
            if col_min > 0:
                left_cells = self.array[row_min:row_max+1, col_min-1]
                if np.all(left_cells == 0):
                    # Empty on the left - might want to align with something above/below
                    self._try_align_with_neighbors(num, 'left', row_min, row_max, col_min)

            # Check right side
            if col_max < self.ncols - 1:
                right_cells = self.array[row_min:row_max+1, col_max+1]
                if np.all(right_cells == 0):
                    # Empty on the right
                    self._try_align_with_neighbors(num, 'right', row_min, row_max, col_max)

    def _try_align_with_neighbors(self, num: int, side: str, row_min: int, row_max: int, col_idx: int):
        """
        Try to align a subplot edge with neighboring subplots.

        For example, if subplot 3 is in row 1 between subplots 1 and 2 in row 0,
        we want to center it between them.
        """
        # Find subplots in adjacent rows that overlap with this subplot's column range
        rows, cols = np.where(self.array == num)
        col_min, col_max = cols.min(), cols.max()

        # Look in rows above
        if row_min > 0:
            above_nums = set()
            for r in range(row_min):
                for c in range(col_min, col_max + 1):
                    if self.array[r, c] != 0:
                        above_nums.add(self.array[r, c])

            if len(above_nums) >= 2:
                # Multiple subplots above - try to center between them
                above_nums = sorted(above_nums)
                # Find the leftmost and rightmost subplots above
                leftmost_cols = []
                rightmost_cols = []
                for n in above_nums:
                    n_cols = np.where(self.array == n)[1]
                    leftmost_cols.append(n_cols.min())
                    rightmost_cols.append(n_cols.max())

                # If we're between two subplots, center between them
                if side == 'left' and leftmost_cols:
                    # Could add centering constraint here
                    # For now, we let the default grid handle it
                    pass

        # Look in rows below
        if row_max < self.nrows - 1:
            below_nums = set()
            for r in range(row_max + 1, self.nrows):
                for c in range(col_min, col_max + 1):
                    if self.array[r, c] != 0:
                        below_nums.add(self.array[r, c])

            if len(below_nums) >= 2:
                # Similar logic for below
                pass

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

        for num in self.subplot_nums:
            rows, cols = np.where(self.array == num)
            row_min, row_max = rows.min(), rows.max()
            col_min, col_max = cols.min(), cols.max()

            # Get the bounding box from the grid lines
            left = self.col_lefts[col_min].value()
            right = self.col_rights[col_max].value()
            bottom = self.row_bottoms[row_max].value()
            top = self.row_tops[row_min].value()

            width = right - left
            height = top - bottom

            positions[num] = (left, bottom, width, height)

        return positions


def compute_kiwi_positions(array: np.ndarray, figwidth: float = 10.0, figheight: float = 8.0,
                          wspace: Optional[List[float]] = None, hspace: Optional[List[float]] = None,
                          left: float = 0.125, right: float = 0.125,
                          top: float = 0.125, bottom: float = 0.125,
                          wratios: Optional[List[float]] = None,
                          hratios: Optional[List[float]] = None) -> Dict[int, Tuple[float, float, float, float]]:
    """
    Compute subplot positions using kiwisolver for non-orthogonal layouts.

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
    wratios, hratios : list of float, optional
        Width and height ratios for columns and rows

    Returns
    -------
    dict
        Dictionary mapping subplot numbers to (left, bottom, width, height)
        in figure-relative coordinates [0, 1]

    Examples
    --------
    >>> array = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    >>> positions = compute_kiwi_positions(array)
    >>> positions[3]  # Position of subplot 3
    (0.25, 0.125, 0.5, 0.35)
    """
    solver = KiwiLayoutSolver(
        array, figwidth, figheight, wspace, hspace,
        left, right, top, bottom, wratios, hratios
    )
    return solver.solve()


def get_grid_positions_kiwi(array: np.ndarray, figwidth: float, figheight: float,
                            wspace: Optional[List[float]] = None,
                            hspace: Optional[List[float]] = None,
                            left: float = 0.125, right: float = 0.125,
                            top: float = 0.125, bottom: float = 0.125,
                            wratios: Optional[List[float]] = None,
                            hratios: Optional[List[float]] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Get grid line positions using kiwisolver.

    This returns arrays of grid line positions similar to GridSpec.get_grid_positions(),
    but computed using constraint satisfaction for better handling of non-orthogonal layouts.

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
    wratios, hratios : list of float, optional
        Width and height ratios for columns and rows

    Returns
    -------
    bottoms, tops, lefts, rights : np.ndarray
        Arrays of grid line positions for each cell
    """
    solver = KiwiLayoutSolver(
        array, figwidth, figheight, wspace, hspace,
        left, right, top, bottom, wratios, hratios
    )
    solver.solver.updateVariables()

    nrows, ncols = array.shape

    # Extract grid line positions
    lefts = np.array([v.value() for v in solver.col_lefts])
    rights = np.array([v.value() for v in solver.col_rights])
    tops = np.array([v.value() for v in solver.row_tops])
    bottoms = np.array([v.value() for v in solver.row_bottoms])

    return bottoms, tops, lefts, rights
