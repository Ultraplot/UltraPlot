#!/usr/bin/env python3
"""Tests for shared and build-time materialized docstrings."""

import ast
import inspect
import runpy
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

import ultraplot as uplt
from ultraplot.internals import docstring


def _load_docstring_expander():
    path = Path(__file__).resolve().parents[2] / "tools" / "expand_docstrings.py"
    return runpy.run_path(str(path))


def test_build_docstring_expansion_preserves_numpy_indentation(tmp_path: Path) -> None:
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
    source = path.read_text()
    assert '    """Summary.\n' in source
    assert "    first : int\n        First value.\n" in source
    assert "\\n" not in source
    assert all(line == line.rstrip() for line in source.splitlines())

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


@pytest.mark.parametrize(
    ("filename", "objects"),
    [
        (
            "ui.py",
            {"figure": uplt.figure, "subplot": uplt.subplot, "subplots": uplt.subplots},
        ),
        (
            "figure.py",
            {
                "Figure.__init__": uplt.Figure.__init__,
                "Figure.subplots": uplt.Figure.subplots,
                "Figure.add_subplots": uplt.Figure.add_subplots,
            },
        ),
        ("gridspec.py", {"GridSpec.__init__": uplt.GridSpec.__init__}),
        (
            "ticker.py",
            {
                f"{name}.__init__": getattr(uplt, name).__init__
                for name in (
                    "DegreeLocator",
                    "LongitudeLocator",
                    "LatitudeLocator",
                    "DegreeFormatter",
                    "LongitudeFormatter",
                    "LatitudeFormatter",
                )
            },
        ),
    ],
)
def test_materialized_public_docstrings_match_runtime(
    tmp_path: Path, filename: str, objects: dict[str, Callable[..., object]]
) -> None:
    """Exercise actual source templates, including methods that contain only a snippet."""
    rewrite_file = _load_docstring_expander()["_rewrite_file"]
    source_root = Path(uplt.__file__).resolve().parent
    package_root = tmp_path / "ultraplot"
    package_root.mkdir()
    path = package_root / filename
    shutil.copyfile(source_root / filename, path)
    assert rewrite_file(path, package_root, docstring._snippet_manager) > 0
    tree = ast.parse(path.read_text())
    for name, obj in objects.items():
        node = tree
        for part in name.split("."):
            node = next(
                child for child in node.body if getattr(child, "name", None) == part
            )
        assert ast.get_docstring(node) == inspect.getdoc(obj)
    # A second build pass must leave the already materialized source untouched.
    source = path.read_bytes()
    assert rewrite_file(path, package_root, docstring._snippet_manager) == 0
    assert path.read_bytes() == source


@pytest.mark.parametrize(
    "text",
    [
        'Résumé with """quotes""", backslashes \\n and \\path, and 100%.\n\n    Indented text with \r and \x00.',
        'A single line with """quotes""" and a trailing quote "',
        "Summary.\n\n",
    ],
)
def test_materialized_docstrings_preserve_literal_characters(
    tmp_path: Path, text: str
) -> None:
    rewrite_file = _load_docstring_expander()["_rewrite_file"]
    path = tmp_path / "example.py"
    path.write_text('def example():\n    """%(example)s"""\n')
    assert rewrite_file(path, tmp_path, {"example": text}) == 1
    namespace = {}
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    assert inspect.getdoc(namespace["example"]) == inspect.cleandoc(text)


@pytest.mark.parametrize(
    "doc",
    [
        "Summary.\n\n    Parameters\n    ----------\n    first : int\n    Description.\nsecond : str\n    Second.",
        "Summary.\n\nParameters\n----------\nfirst : int\nDescription.",
        "Summary.\n\nParameters\n----------\nfirst :\nint\n    Description.",
    ],
)
def test_installed_docstring_check_rejects_malformed_parameters(doc: str) -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "tools"
        / "ci"
        / "check_installed_docstrings.py"
    )
    check_docstring = runpy.run_path(str(path))["_check_numpy_docstring"]
    with pytest.raises(AssertionError):
        check_docstring(doc, ("Parameters",), ("first",))


def test_subplots_parameter_docstrings_are_numpy_style() -> None:
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


def _load_installed_docstring_checker() -> dict:
    path = (
        Path(__file__).resolve().parents[2]
        / "tools"
        / "ci"
        / "check_installed_docstrings.py"
    )
    return runpy.run_path(str(path))


def test_package_docstring_structure() -> None:
    """Expand every owned source docstring and check its actual parser output."""
    expand = _load_docstring_expander()["_expand"]
    checker = _load_installed_docstring_checker()
    package = Path(uplt.__file__).resolve().parent
    for path in package.rglob("*.py"):
        if {"tests", "externals"}.intersection(path.relative_to(package).parts):
            continue
        tree = ast.parse(path.read_bytes())
        for node, doc in checker["_iter_docstrings"](tree):
            expanded, _ = expand(inspect.cleandoc(doc), docstring._snippet_manager)
            try:
                checker["_check_numpy_structure"](expanded)
            except (AssertionError, ValueError) as exc:
                raise AssertionError(
                    f"{path.name}:{getattr(node, 'lineno', 1)}: {exc}"
                ) from exc


@pytest.mark.parametrize(
    "doc",
    [
        "Parameters\n----------\nfirst : int\n    First.\n\nParameters\n----------\nsecond : int\n    Second.",
        "Parameters\n----------\nfirst : int\n    First.\nReturns\n-------\nint\n    Result.",
        "Parameters\n-----------\nfirst : int\n    First.",
        "Parameters\n----------\nfirst : int\nsecond : int\n    Second.",
        "Summary.\n\n    Other parameters\n    ----------------\n    first : int\n        First.\n\nNotes\n-----\nA note.",
    ],
)
def test_package_docstring_check_rejects_structural_errors(doc: str) -> None:
    check = _load_installed_docstring_checker()["_check_numpy_structure"]
    with pytest.raises((AssertionError, ValueError)):
        check(doc)


@pytest.mark.parametrize(
    ("obj", "section", "expected"),
    [
        (uplt.LongitudeLocator.__init__, "Parameters", {"dms", "lon0"}),
        (uplt.LongitudeFormatter.__init__, "Parameters", {"dms", "lon0"}),
        (
            uplt.Figure.__init__,
            "Other Parameters",
            {
                "leftlabelpad, toplabelpad, rightlabelpad, bottomlabelpad",
                "leftlabelsharedpad, toplabelsharedpad, rightlabelsharedpad, bottomlabelsharedpad",
            },
        ),
        (
            uplt.Axes.colorbar,
            "Parameters",
            {"loc", "length", "width", "bbox_to_anchor"},
        ),
        (
            uplt.PlotAxes.beeswarm,
            "Parameters",
            {"s, size, ms, markersize", "area_size", "absolute_size"},
        ),
        (uplt.PlotAxes.beeswarm, "Other Parameters", {"norm", "**kwargs"}),
        (uplt.Axes.catlegend, "Other Parameters", {"handle_kw", "add", "**kwargs"}),
    ],
)
def test_shared_parameters_remain_separate_entries(
    obj: Callable[..., object], section: str, expected: set[str]
) -> None:
    parse = _load_installed_docstring_checker()["NumpyDocString"]
    parsed = parse(inspect.getdoc(obj))
    entries = {entry.name: entry for entry in parsed[section]}
    assert expected <= entries.keys()
    assert all(entries[name].desc for name in expected)


@pytest.mark.parametrize(
    "name", ["catlegend", "entrylegend", "sizelegend", "numlegend", "geolegend"]
)
def test_semantic_legend_styles_are_documented_as_parameters(name: str) -> None:
    parse = _load_installed_docstring_checker()["NumpyDocString"]
    parsed = parse(inspect.getdoc(getattr(uplt.Axes, name)))
    entries = {entry.name: entry for entry in parsed["Other Parameters"]}
    assert {"handle_kw", "add", "**kwargs"} <= entries.keys()
    style_entries = {
        key: entry
        for key, entry in entries.items()
        if key not in {"handle_kw", "add", "**kwargs"}
    }
    keywords = {keyword.strip() for key in style_entries for keyword in key.split(",")}
    assert {"linewidth", "linestyle", "alpha", "antialiased"} <= keywords
    if name in {"catlegend", "entrylegend", "sizelegend"}:
        assert {
            "markersize",
            "markeredgewidth",
            "s",
            "fillstyle",
            "marker_transform",
        } <= keywords
    else:
        assert {
            "facecolor",
            "edgecolor",
            "hatch",
            "fill",
            "joinstyle",
            "capstyle",
        } <= keywords
    assert all(entry.type and entry.desc for entry in style_entries.values())
    notes = "\n".join(parsed["Notes"])
    assert "keywords can be passed directly or through" in notes
    assert "A style value resolved per legend entry" in notes
    assert "Plural" in notes


def test_package_docstring_check_preserves_sphinx_admonitions() -> None:
    from sphinx.ext.napoleon.docstring import NumpyDocstring

    doc = "Important\n---------\nKeep this note visible."
    _load_installed_docstring_checker()["_check_numpy_structure"](doc)
    assert ".. important:: Keep this note visible." in str(NumpyDocstring(doc))
