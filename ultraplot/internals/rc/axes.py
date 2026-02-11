#!/usr/bin/env python3
"""
Axes-domain rc defaults.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .core import build_core_rc_table
from .plot_types import build_plot_type_rc_table

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]

_TEXT_PREFIXES = (
    "abc.",
    "text.",
    "title.",
    "suptitle.",
    "leftlabel.",
    "rightlabel.",
    "toplabel.",
    "bottomlabel.",
    "font.",
)


def _plot_type_validators(ns: Mapping[str, Any]) -> dict[str, RcValidator]:
    return {
        "validate_bool": ns["_validate_bool"],
        "validate_color": ns["_validate_color"],
        "validate_float": ns["_validate_float"],
        "validate_int": ns["_validate_int"],
        "validate_string": ns["_validate_string"],
    }


def build_axes_rc_table(ns: Mapping[str, Any]) -> RcTable:
    """
    Build axes-domain rc entries.

    This includes all core settings except text/subplots domains and adds
    curved-quiver plot-type defaults.
    """
    core = build_core_rc_table(ns)
    table = {
        key: value
        for key, value in core.items()
        if not key.startswith("subplots.") and not key.startswith(_TEXT_PREFIXES)
    }
    plot_types = build_plot_type_rc_table(**_plot_type_validators(ns))
    table.update(
        {
            key: value
            for key, value in plot_types.items()
            if key.startswith("curved_quiver.")
        }
    )
    return table
