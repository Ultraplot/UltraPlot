#!/usr/bin/env python3
"""
Subplots-domain rc defaults.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .core import build_core_rc_table

RcValidator = Callable[[Any], Any]
RcEntry = tuple[Any, RcValidator, str]
RcTable = dict[str, RcEntry]


def build_subplots_rc_table(ns: Mapping[str, Any]) -> RcTable:
    """
    Build subplots-domain rc entries.
    """
    core = build_core_rc_table(ns)
    return {key: value for key, value in core.items() if key.startswith("subplots.")}
