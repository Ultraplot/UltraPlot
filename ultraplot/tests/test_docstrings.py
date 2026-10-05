#!/usr/bin/env python3
"""Tests for shared and build-time materialized docstrings."""

import inspect
import runpy
from pathlib import Path

import ultraplot as uplt


def _load_docstring_expander():
    path = Path(__file__).resolve().parents[2] / "tools" / "expand_docstrings.py"
    return runpy.run_path(str(path))


def test_build_docstring_expansion_preserves_numpy_indentation(tmp_path):
    """Build-time expansion should match runtime normalize-before-substitute semantics."""
    rewrite_file = _load_docstring_expander()["_rewrite_file"]
    package_root = tmp_path / "pkg"
    package_root.mkdir()
    path = package_root / "example.py"
    path.write_text(
        "def example():\n"
        '    """Summary.\n'
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    %(params)s\n"
        '    """\n'
    )
    snippets = {
        "params": (
            "first : int\n" "    First value.\n" "second : str\n" "    Second value."
        )
    }

    assert rewrite_file(path, package_root, snippets) == 1

    namespace = {}
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    assert inspect.getdoc(namespace["example"]) == (
        "Summary.\n"
        "\n"
        "Parameters\n"
        "----------\n"
        "first : int\n"
        "    First value.\n"
        "second : str\n"
        "    Second value."
    )


def test_subplots_parameter_docstrings_are_numpy_style():
    """Shared subplot parameter snippets should render as valid NumPy-style entries."""
    doc = inspect.getdoc(uplt.subplots) or ""
    assert (
        "projection : str, `cartopy.crs.Projection`, "
        "or `~mpl_toolkits.basemap.Basemap`, optional"
    ) in doc
    assert "\nprojection :\n" not in doc
    assert (
        "Whether subplots are numbered in row-major (``'C'``) "
        "or column-major (``'F'``)"
    ) in doc

