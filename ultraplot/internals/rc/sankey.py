#!/usr/bin/env python3
"""
Sankey-domain rc defaults.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .plot_types import build_plot_type_rc_table

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]


def build_sankey_rc_table(ns: Mapping[str, Any]) -> RcTable:
    """
    Build sankey-domain rc entries.
    """
    table = build_plot_type_rc_table(
        validate_bool=ns["_validate_bool"],
        validate_color=ns["_validate_color"],
        validate_float=ns["_validate_float"],
        validate_int=ns["_validate_int"],
        validate_string=ns["_validate_string"],
    )
    return {key: value for key, value in table.items() if key.startswith("sankey.")}
