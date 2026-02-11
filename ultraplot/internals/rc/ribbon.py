#!/usr/bin/env python3
"""
Ribbon-domain rc defaults.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .core import build_core_rc_table
from .plot_types import build_plot_type_rc_table
from .registry import merge_rc_tables

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]


def build_ribbon_rc_table(ns: Mapping[str, Any]) -> RcTable:
    """
    Build ribbon-domain rc entries.

    Ribbon keys may be absent on branches where ribbon rc defaults have not yet
    landed on main; this function safely returns an empty table in that case.
    """
    core = build_core_rc_table(ns)
    plot_types = build_plot_type_rc_table(
        validate_bool=ns["_validate_bool"],
        validate_color=ns["_validate_color"],
        validate_float=ns["_validate_float"],
        validate_int=ns["_validate_int"],
        validate_string=ns["_validate_string"],
    )
    combined = merge_rc_tables(core, plot_types)
    return {key: value for key, value in combined.items() if key.startswith("ribbon.")}
