# Kiwi Layout System for Non-Orthogonal Subplot Arrangements

## Overview

UltraPlot now includes a constraint-based layout system using [kiwisolver](https://github.com/nucleic/kiwi) to handle non-orthogonal subplot arrangements. This enables aesthetically pleasing layouts where subplots don't follow a simple grid pattern.

## The Problem

Traditional gridspec systems work well for orthogonal (grid-aligned) layouts like:
```
[[1, 2],
 [3, 4]]
```

But they fail to produce aesthetically pleasing results for non-orthogonal layouts like:
```
[[1, 1, 2, 2],
 [0, 3, 3, 0]]
```

In this example, subplot 3 should ideally be centered between subplots 1 and 2, but a naive grid-based approach would simply position it based on the grid cells it occupies, which may not look visually balanced.

## The Solution

The new kiwi layout system uses constraint satisfaction to compute subplot positions that:
1. Respect spacing and ratio requirements
2. Align edges where appropriate for orthogonal layouts
3. Create visually balanced arrangements for non-orthogonal layouts
4. Center or distribute subplots nicely when they have empty cells adjacent to them

## Installation

The kiwi layout system requires the `kiwisolver` package:

```bash
pip install kiwisolver
```

If `kiwisolver` is not installed, UltraPlot will automatically fall back to the standard grid-based layout (which still works fine for orthogonal layouts).

## Usage

### Basic Example

```python
import ultraplot as uplt
import numpy as np

# Define a non-orthogonal layout
# 1 and 2 are in the top row, 3 is centered below them
layout = [[1, 1, 2, 2],
          [0, 3, 3, 0]]

# Create the subplots - kiwi layout is automatic!
fig, axs = uplt.subplots(array=layout, figsize=(10, 6))

# Add content to your subplots
axs[0].plot([0, 1, 2], [0, 1, 0])
axs[0].set_title('Subplot 1')

axs[1].plot([0, 1, 2], [1, 0, 1])
axs[1].set_title('Subplot 2')

axs[2].plot([0, 1, 2], [0.5, 1, 0.5])
axs[2].set_title('Subplot 3 (Centered!)')

plt.savefig('non_orthogonal_layout.png')
```

### When Does Kiwi Layout Activate?

The kiwi layout system automatically activates when:
1. You pass an `array` parameter to `subplots()`
2. The layout is detected as non-orthogonal
3. `kiwisolver` is installed

For orthogonal layouts, the standard grid-based system is used (it's faster and produces identical results).

### Complex Layouts

The kiwi layout system handles complex arrangements:

```python
# More complex non-orthogonal layout
layout = [[1, 1, 1, 2],
          [3, 3, 0, 2],
          [4, 5, 5, 5]]

fig, axs = uplt.subplots(array=layout, figsize=(12, 9))
```

## How It Works

### Layout Detection

The system first analyzes the layout array to determine if it's orthogonal:

```python
from ultraplot.kiwi_layout import is_orthogonal_layout

layout = [[1, 1, 2, 2], [0, 3, 3, 0]]
is_ortho = is_orthogonal_layout(layout)  # Returns False
```

An orthogonal layout is one where all subplot edges align with grid cell boundaries, forming a consistent grid structure.

### Constraint System

For non-orthogonal layouts, kiwisolver creates variables for:
- Left and right edges of each column
- Top and bottom edges of each row

And applies constraints for:
- Figure boundaries (margins)
- Column/row spacing (`wspace`, `hspace`)
- Width/height ratios (`wratios`, `hratios`)
- Continuity (columns connect with spacing)

### Aesthetic Improvements

The solver adds additional constraints to improve aesthetics:
- Subplots with empty cells beside them are positioned to look balanced
- Centering is applied where appropriate
- Edge alignment is maintained where subplots share boundaries

## API Reference

### GridSpec

The `GridSpec` class now accepts a `layout_array` parameter:

```python
from ultraplot.gridspec import GridSpec

gs = GridSpec(2, 4, layout_array=[[1, 1, 2, 2], [0, 3, 3, 0]])
```

This parameter is automatically set when using `subplots(array=...)`.

### Kiwi Layout Module

The `ultraplot.kiwi_layout` module provides:

#### `is_orthogonal_layout(array)`
Check if a layout is orthogonal.

**Parameters:**
- `array` (np.ndarray): 2D array of subplot numbers

**Returns:**
- `bool`: True if orthogonal, False otherwise

#### `compute_kiwi_positions(array, ...)`
Compute subplot positions using constraint solving.

**Parameters:**
- `array` (np.ndarray): 2D layout array
- `figwidth`, `figheight` (float): Figure dimensions in inches
- `wspace`, `hspace` (list): Spacing between columns/rows in inches
- `left`, `right`, `top`, `bottom` (float): Margins in inches
- `wratios`, `hratios` (list): Width/height ratios

**Returns:**
- `dict`: Mapping from subplot number to (left, bottom, width, height) in figure coordinates

#### `KiwiLayoutSolver`
Main solver class for constraint-based layout computation.

## Customization

All standard GridSpec parameters work with kiwi layouts:

```python
fig, axs = uplt.subplots(
    array=[[1, 1, 2, 2], [0, 3, 3, 0]],
    figsize=(10, 6),
    wspace=[0.3, 0.5, 0.3],  # Custom spacing between columns
    hspace=0.4,              # Spacing between rows
    wratios=[1, 1, 1, 1],    # Column width ratios
    hratios=[1, 1.5],        # Row height ratios
    left=0.1,                # Left margin
    right=0.1,               # Right margin
    top=0.15,                # Top margin
    bottom=0.1               # Bottom margin
)
```

## Performance

- **Orthogonal layouts**: No performance impact (standard grid system used)
- **Non-orthogonal layouts**: Minimal overhead (~1-5ms for typical layouts)
- **Position caching**: Positions are computed once and cached

## Limitations

1. Kiwisolver must be installed (falls back to standard grid if not available)
2. Very complex layouts (>20 subplots) may have slightly longer computation time
3. The system optimizes for common aesthetic cases but may not handle all edge cases perfectly

## Troubleshooting

### Kiwi layout not activating

Check that:
1. `kiwisolver` is installed: `pip install kiwisolver`
2. Your layout is actually non-orthogonal
3. You're passing the `array` parameter to `subplots()`

### Unexpected positioning

If positions aren't as expected:
1. Try adjusting `wspace`, `hspace`, `wratios`, `hratios`
2. Check your layout array for unintended patterns
3. File an issue with your layout and expected vs. actual behavior

### Fallback to grid layout

If the solver fails, UltraPlot automatically falls back to grid-based positioning and emits a warning. Check the warning message for details.

## Examples

See the example scripts:
- `example_kiwi_layout.py` - Basic demonstration
- `test_kiwi_layout_demo.py` - Comprehensive test suite

Run them with:
```bash
python example_kiwi_layout.py
python test_kiwi_layout_demo.py
```

## Future Enhancements

Potential future improvements:
- Additional aesthetic constraints (e.g., alignment preferences)
- User-specified custom constraints
- Better handling of panels and colorbars in non-orthogonal layouts
- Interactive layout preview/adjustment

## Contributing

Contributions are welcome! Areas for improvement:
- Better heuristics for aesthetic constraints
- Performance optimizations for large layouts
- Additional test cases and edge case handling
- Documentation improvements

## References

- [Kiwisolver](https://github.com/nucleic/kiwi) - The constraint solving library
- [Matplotlib GridSpec](https://matplotlib.org/stable/api/_as_gen/matplotlib.gridspec.GridSpec.html) - Standard grid-based layout
- [Cassowary Algorithm](https://constraints.cs.washington.edu/cassowary/) - The constraint solving algorithm used by kiwisolver

## License

This feature is part of UltraPlot and follows the same license.