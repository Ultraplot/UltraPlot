#!/usr/bin/env python3
"""
Helpers for composing rc parameter tables.
"""

from .axes import build_axes_rc_table
from .core import build_core_rc_table
from .deprecations import get_rc_removed, get_rc_renamed
from .plot_types import build_plot_type_rc_table
from .ribbon import build_ribbon_rc_table
from .registry import merge_rc_tables
from .sankey import build_sankey_rc_table
from .subplots import build_subplots_rc_table
from .text import build_text_rc_table

__all__ = [
    "build_axes_rc_table",
    "build_core_rc_table",
    "build_plot_type_rc_table",
    "build_ribbon_rc_table",
    "build_sankey_rc_table",
    "build_subplots_rc_table",
    "build_text_rc_table",
    "get_rc_removed",
    "get_rc_renamed",
    "merge_rc_tables",
]
