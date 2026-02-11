#!/usr/bin/env python3
"""
rc defaults for plot-type specific settings.
"""

from __future__ import annotations

from typing import Any, Callable

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]


def build_plot_type_rc_table(
    *,
    validate_bool: RcValidator,
    validate_color: RcValidator,
    validate_float: RcValidator,
    validate_int: RcValidator,
    validate_string: RcValidator,
) -> RcTable:
    """
    Return rc table entries scoped to plot types.

    Validators are passed from rcsetup to avoid import cycles and keep
    validation behavior centralized.
    """
    return {
        # Curved quiver settings
        "curved_quiver.arrowsize": (
            1.0,
            validate_float,
            "Default size scaling for arrows in curved quiver plots.",
        ),
        "curved_quiver.arrowstyle": (
            "-|>",
            validate_string,
            "Default arrow style for curved quiver plots.",
        ),
        "curved_quiver.scale": (
            1.0,
            validate_float,
            "Default scale factor for curved quiver plots.",
        ),
        "curved_quiver.grains": (
            15,
            validate_int,
            "Default number of grains (segments) for curved quiver arrows.",
        ),
        "curved_quiver.density": (
            10,
            validate_int,
            "Default density of arrows for curved quiver plots.",
        ),
        "curved_quiver.arrows_at_end": (
            True,
            validate_bool,
            "Whether to draw arrows at the end of curved quiver lines by default.",
        ),
        # Sankey settings
        "sankey.nodepad": (
            0.02,
            validate_float,
            "Vertical padding between nodes in layered sankey diagrams.",
        ),
        "sankey.nodewidth": (
            0.03,
            validate_float,
            "Node width for layered sankey diagrams (axes-relative units).",
        ),
        "sankey.margin": (
            0.05,
            validate_float,
            "Margin around layered sankey diagrams (axes-relative units).",
        ),
        "sankey.flow.alpha": (
            0.75,
            validate_float,
            "Flow transparency for layered sankey diagrams.",
        ),
        "sankey.flow.curvature": (
            0.5,
            validate_float,
            "Flow curvature for layered sankey diagrams.",
        ),
        "sankey.node.facecolor": (
            "0.75",
            validate_color,
            "Default node facecolor for layered sankey diagrams.",
        ),
    }
