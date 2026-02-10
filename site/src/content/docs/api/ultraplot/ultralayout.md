---
title: "ultraplot.ultralayout"
description: "UltraLayout: Advanced constraint-based layout system for non-orthogonal subplot arrangements."
source: "ultraplot/ultralayout.py"
---

`ultraplot.ultralayout`

UltraLayout: Advanced constraint-based layout system for non-orthogonal subplot arrangements.

## Public Classes

### `UltraLayoutSolver`

UltraLayout: Constraint-based layout solver using kiwisolver for subplot positioning.

### `ColorbarLayoutSolver`

Constraint-based solver for inset colorbar frame alignment.

## Public Functions

### `is_orthogonal_layout(array: np.ndarray)`

Check if a subplot array follows an orthogonal (grid-aligned) layout.

### `compute_ultra_positions(array: np.ndarray, figwidth: float=10.0, figheight: float=8.0, wspace: Optional[List[float]]=None, hspace: Optional[List[float]]=None, left: float=0.125, right: float=0.125, top: float=0.125, bottom: float=0.125, wratios: Optional[List[float]]=None, hratios: Optional[List[float]]=None, wpanels: Optional[List[bool]]=None, hpanels: Optional[List[bool]]=None)`

Compute subplot positions using UltraLayout for non-orthogonal layouts.

### `get_grid_positions_ultra(array: np.ndarray, figwidth: float, figheight: float, wspace: Optional[List[float]]=None, hspace: Optional[List[float]]=None, left: float=0.125, right: float=0.125, top: float=0.125, bottom: float=0.125, wratios: Optional[List[float]]=None, hratios: Optional[List[float]]=None, wpanels: Optional[List[bool]]=None, hpanels: Optional[List[bool]]=None)`

Get grid line positions using UltraLayout.
