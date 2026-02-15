#!/usr/bin/env python3
"""
rc table assembly helpers.
"""

from .deprecations import get_rc_removed, get_rc_renamed
from .registry import merge_rc_tables
from .settings import build_settings_rc_table
from .validators import build_validator_aliases

__all__ = [
    "build_settings_rc_table",
    "build_validator_aliases",
    "get_rc_removed",
    "get_rc_renamed",
    "merge_rc_tables",
]
