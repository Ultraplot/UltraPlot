#!/usr/bin/env python3
"""
Text-domain rc defaults.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from .core import build_core_rc_table

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


def build_text_rc_table(ns: Mapping[str, Any]) -> RcTable:
    """
    Build text-domain rc entries.
    """
    core = build_core_rc_table(ns)
    return {key: value for key, value in core.items() if key.startswith(_TEXT_PREFIXES)}
