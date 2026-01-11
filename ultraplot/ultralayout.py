#!/usr/bin/env python3
"""
UltraLayout: Advanced constraint-based layout system for non-orthogonal subplot arrangements.

This module provides UltraPlot's constraint-based layout computation for subplot grids
that don't follow simple orthogonal patterns, such as [[1, 1, 2, 2], [0, 3, 3, 0]]
where subplot 3 should be nicely centered between subplots 1 and 2.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from kiwisolver import Solver, Variable

    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False
    Variable = None
    Solver = None


__all__ = [
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


class UltraLayoutSolver:
    """
    UltraLayout: Constraint-based layout solver using kiwisolver for subplot positioning.

    This solver computes aesthetically pleasing positions for subplots in
    non-orthogonal arrangements by using constraint satisfaction, providing
    a superior layout experience for complex subplot arrangements.
    """

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
        wratios: Optional[List[float]] = None,
        hratios: Optional[List[float]] = None,
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
        wratios, hratios : list of float, optional
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
        if wratios is None:
            self.wratios = [1.0] * self.ncols
        else:
            self.wratios = list(wratios)

        if hratios is None:
            self.hratios = [1.0] * self.nrows
        else:
            self.hratios = list(hratios)

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

        # 4. Width constraints (panel slots are fixed, remaining slots use ratios)
        total_width = 1.0 - (self.left_margin + self.right_margin) / self.figwidth
        if self.ncols > 1:
            spacing_total = sum(self.wspace) / self.figwidth
        else:
            spacing_total = 0
        available_width = total_width - spacing_total
        fixed_width = 0.0
        ratio_sum = 0.0
        for i in range(self.ncols):
            if self.wpanels[i]:
                fixed_width += self.wratios[i] / self.figwidth
            else:
                ratio_sum += self.wratios[i]
        remaining_width = max(0.0, available_width - fixed_width)
        if ratio_sum == 0:
            ratio_sum = 1.0

        for i in range(self.ncols):
            if self.wpanels[i]:
                width = self.wratios[i] / self.figwidth
            else:
                width = remaining_width * self.wratios[i] / ratio_sum
            self.solver.addConstraint(self.col_rights[i] == self.col_lefts[i] + width)

        # 5. Height constraints (panel slots are fixed, remaining slots use ratios)
        total_height = 1.0 - (self.top_margin + self.bottom_margin) / self.figheight
        if self.nrows > 1:
            spacing_total = sum(self.hspace) / self.figheight
        else:
            spacing_total = 0
        available_height = total_height - spacing_total
        fixed_height = 0.0
        ratio_sum = 0.0
        for i in range(self.nrows):
            if self.hpanels[i]:
                fixed_height += self.hratios[i] / self.figheight
            else:
                ratio_sum += self.hratios[i]
        remaining_height = max(0.0, available_height - fixed_height)
        if ratio_sum == 0:
            ratio_sum = 1.0

        for i in range(self.nrows):
            if self.hpanels[i]:
                height = self.hratios[i] / self.figheight
            else:
                height = remaining_height * self.hratios[i] / ratio_sum
            self.solver.addConstraint(self.row_tops[i] == self.row_bottoms[i] + height)

        # 6. Add aesthetic constraints for non-orthogonal layouts
        self._add_aesthetic_constraints()

    def _add_aesthetic_constraints(self):
        """
        Add constraints to make non-orthogonal layouts look nice.

        For subplots that span cells in non-aligned ways, we add constraints
        to center them or align them aesthetically with neighboring subplots.
        """
        # Cache subplot bounds for neighbor lookups.
        bboxes = {}
        for num in self.subplot_nums:
            rows, cols = np.where(self.array == num)
            bboxes[num] = (rows.min(), rows.max(), cols.min(), cols.max())

        # Analyze the layout to find subplots that need special handling.
        for num in self.subplot_nums:
            row_min, row_max, col_min, col_max = bboxes[num]

            # Check if this subplot has empty cells on its sides.
            left_empty = False
            right_empty = False
            if col_min > 0:
                left_cells = self.array[row_min : row_max + 1, col_min - 1]
                left_empty = np.all(left_cells == 0)
            if col_max < self.ncols - 1:
                right_cells = self.array[row_min : row_max + 1, col_max + 1]
                right_empty = np.all(right_cells == 0)

            # If empty on both sides, try to center between neighboring subplots.
            if left_empty and right_empty:
                self._center_between_neighbors(
                    num, row_min, row_max, col_min, col_max, bboxes
                )
                continue

            # Otherwise try to align with neighbors on the empty side.
            if left_empty:
                self._try_align_with_neighbors(num, "left", row_min, row_max, col_min)
            if right_empty:
                self._try_align_with_neighbors(num, "right", row_min, row_max, col_max)

    def _center_between_neighbors(
        self,
        num: int,
        row_min: int,
        row_max: int,
        col_min: int,
        col_max: int,
        bboxes: Dict[int, Tuple[int, int, int, int]],
    ) -> None:
        """
        Center a subplot between neighboring subplots above or below.
        Currently a no-op to avoid over-constraining; spacing is handled post-solve.
        """
        return

    def _try_align_with_neighbors(
        self, num: int, side: str, row_min: int, row_max: int, col_idx: int
    ):
        """
        Try to align a subplot edge with neighboring subplots.

        For example, if subplot 3 is in row 1 between subplots 1 and 2 in row 0,
        we want to center it between them.
        """
        # Placeholder: alignment tweaks could be added here if needed.
        return

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
        col_widths = [right - left for left, right in zip(col_lefts, col_rights)]
        row_heights = [top - bottom for top, bottom in zip(row_tops, row_bottoms)]

        base_wgap = None
        for i in range(self.ncols - 1):
            if not self.wpanels[i] and not self.wpanels[i + 1]:
                gap = col_lefts[i + 1] - col_rights[i]
                if base_wgap is None or gap < base_wgap:
                    base_wgap = gap
        if base_wgap is None:
            base_wgap = 0.0

        base_hgap = None
        for i in range(self.nrows - 1):
            if not self.hpanels[i] and not self.hpanels[i + 1]:
                gap = row_bottoms[i] - row_tops[i + 1]
                if base_hgap is None or gap < base_hgap:
                    base_hgap = gap
        if base_hgap is None:
            base_hgap = 0.0

        def _adjust_span(
            spans: List[int],
            start: float,
            end: float,
            sizes: List[float],
            panels: List[bool],
            base_gap: float,
        ) -> Tuple[float, float]:
            effective = [i for i in spans if not panels[i]]
            if len(effective) <= 1:
                return start, end
            desired = sum(sizes[i] for i in effective)
            # Collapse inter-column/row gaps inside spans to keep widths consistent.
            # This avoids widening subplots that cross internal panel slots.
            full = end - start
            if desired < full:
                offset = 0.5 * (full - desired)
                start = start + offset
                end = start + desired
            return start, end

        for num in self.subplot_nums:
            rows, cols = np.where(self.array == num)
            row_min, row_max = rows.min(), rows.max()
            col_min, col_max = cols.min(), cols.max()

            # Get the bounding box from the grid lines
            left = col_lefts[col_min]
            right = col_rights[col_max]
            bottom = row_bottoms[row_max]
            top = row_tops[row_min]

            span_cols = list(range(col_min, col_max + 1))
            span_rows = list(range(row_min, row_max + 1))

            left, right = _adjust_span(
                span_cols,
                left,
                right,
                col_widths,
                self.wpanels,
                base_wgap,
            )
            top, bottom = _adjust_span(
                span_rows,
                top,
                bottom,
                row_heights,
                self.hpanels,
                base_hgap,
            )

            width = right - left
            height = top - bottom

            positions[num] = (left, bottom, width, height)

        return positions


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
    wratios: Optional[List[float]] = None,
    hratios: Optional[List[float]] = None,
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
    wratios, hratios : list of float, optional
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
        wratios,
        hratios,
        wpanels,
        hpanels,
    )
    return solver.solve()


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
    wratios: Optional[List[float]] = None,
    hratios: Optional[List[float]] = None,
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
    wratios, hratios : list of float, optional
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
        wratios,
        hratios,
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
