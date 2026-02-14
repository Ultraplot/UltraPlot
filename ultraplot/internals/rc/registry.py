#!/usr/bin/env python3
"""
Utilities for composing rc tables from modular providers.
"""

from __future__ import annotations

from typing import Any, Callable

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]


def merge_rc_tables(*tables: RcTable) -> RcTable:
    """
    Merge rc tables and fail on duplicate keys.
    """
    merged: RcTable = {}
    for table in tables:
        overlap = merged.keys() & table.keys()
        if overlap:
            overlap_str = ", ".join(sorted(overlap))
            raise ValueError(f"Duplicate rc keys while merging tables: {overlap_str}")
        merged.update(table)
    return merged
