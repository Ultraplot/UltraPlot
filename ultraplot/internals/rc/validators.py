#!/usr/bin/env python3
"""
Validator aliases for declarative rc settings.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

RcValidator = Callable[[Any], Any]


def build_validator_aliases(ns: Mapping[str, Any]) -> dict[str, RcValidator]:
    """
    Build a compact validator alias map from rcsetup namespace.
    """
    return {
        "bool": ns["_validate_bool"],
        "color": ns["_validate_color"],
        "float": ns["_validate_float"],
        "int": ns["_validate_int"],
        "string": ns["_validate_string"],
    }
