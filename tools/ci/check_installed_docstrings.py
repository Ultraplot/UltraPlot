"""Validate that the installed package exposes literal expanded docstrings."""

from __future__ import annotations

import ast
import inspect
import re
import warnings
from collections.abc import Iterator
from importlib.metadata import distribution
from pathlib import Path

from numpydoc.docscrape import NumpyDocString

PLACEHOLDER = re.compile(r"%\(([^)]+)\)s")
_NUMPY_DOCSTRINGS = {
    "ui.py": {
        "figure": (("Parameters", "Other parameters"), ("refnum", "refaspect")),
        "subplot": (("Other parameters", "Returns"), ("refnum", "refaspect")),
        "subplots": (
            ("Parameters", "Other parameters", "Returns"),
            ("array", "order", "projection", "refnum", "refaspect"),
        ),
    },
    "figure.py": {
        "Figure.__init__": (
            ("Parameters", "Other parameters"),
            ("refnum", "refaspect"),
        ),
        "Figure.subplots": (
            ("Parameters", "Other parameters", "Returns"),
            ("array", "order", "projection", "refnum", "refaspect"),
        ),
        "Figure.add_subplots": (
            ("Parameters", "Other parameters", "Returns"),
            ("array", "order", "projection", "refnum", "refaspect"),
        ),
    },
    "gridspec.py": {
        "GridSpec.__init__": (
            ("Parameters", "Other parameters"),
            ("nrows", "ncols", "left, right, top, bottom"),
        ),
    },
}


def _iter_docstrings(tree: ast.AST) -> Iterator[tuple[ast.AST, str]]:
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                yield node, doc


def _check_numpy_docstring(
    doc: str, sections: tuple[str, ...], parameters: tuple[str, ...]
) -> None:
    """Check literal structure before runtime decorators can normalize it."""
    lines = inspect.cleandoc(doc).splitlines()
    for section in sections:
        assert section in lines, f"Missing or indented section: {section}"
        index = lines.index(section)
        assert lines[index + 1 : index + 2] == ["-" * len(section)], section
    for parameter in parameters:
        declarations = [
            i for i, line in enumerate(lines) if line.startswith(parameter + " :")
        ]
        assert len(declarations) == 1, f"Missing or indented parameter: {parameter}"
        index = declarations[0]
        assert lines[index].split(" :", 1)[1].strip(), f"Missing type: {parameter}"
        description = lines[index + 1 : index + 2]
        assert (
            description and description[0].startswith("    ") and description[0].strip()
        ), f"Missing or unindented description: {parameter}"
    if "projection" in parameters:
        assert (
            "projection : str, `cartopy.crs.Projection`, "
            "or `~mpl_toolkits.basemap.Basemap`, optional"
        ) in lines, "Malformed projection declaration"
        assert (
            "Whether subplots are numbered in row-major (``'C'``) "
            "or column-major (``'F'``)"
        ) in "\n".join(lines), "Incorrect C/F ordering documentation"


def _check_numpy_docstrings(filename: str, tree: ast.Module) -> None:
    for name, (sections, parameters) in _NUMPY_DOCSTRINGS.get(filename, {}).items():
        node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef = tree
        for part in name.split("."):
            node = next(
                child
                for child in node.body
                if isinstance(
                    child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                )
                and child.name == part
            )
        doc = ast.get_docstring(node, clean=False)
        assert doc, f"Missing docstring: {filename}:{name}"
        try:
            _check_numpy_docstring(doc, sections, parameters)
        except AssertionError as exc:
            raise AssertionError(f"{filename}:{name}: {exc}") from exc


def _check_numpy_structure(doc: str) -> None:
    """Reject malformed sections and entries across all owned package docstrings."""
    doc = inspect.cleandoc(doc)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        parsed = NumpyDocString(doc)
    # Napoleon, used by our Sphinx build, supports Important as an admonition.
    unexpected = [
        str(warning.message).splitlines()[0]
        for warning in caught
        if str(warning.message).splitlines()[0] != "Unknown section Important"
    ]
    assert not unexpected, "; ".join(unexpected)
    for section in ("Parameters", "Other Parameters", "Returns", "Yields"):
        for entry in parsed[section]:
            assert (
                entry.desc
            ), f"Missing description in {section}: {entry.name or entry.type}"

    headings = {name.lower() for name in parsed.keys()}
    lines = doc.splitlines()
    section = ""
    for index, (line, underline) in enumerate(zip(lines, lines[1:])):
        if not underline.strip() or set(underline.strip()) != {"-"}:
            continue
        heading = line.strip().lower()
        if heading not in headings and heading != "important":
            continue
        # Code samples may themselves contain a nested NumPy-style docstring.
        if section == "examples" and line.startswith(" "):
            continue
        assert line == line.lstrip(), f"Indented section: {line.strip()}"
        assert (
            index == 0 or not lines[index - 1].strip()
        ), f"Missing blank line before section: {line}"
        section = heading


def main() -> None:
    package = Path(distribution("ultraplot").locate_file("ultraplot"))
    assert package.is_dir(), f"installed package not found: {package}"
    assert (package / "py.typed").is_file(), "installed package is missing py.typed"
    assert not list(
        package.rglob("*.pyi")
    ), "installed package unexpectedly ships .pyi files"

    unresolved = []
    for path in package.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        if path.parent == package:
            _check_numpy_docstrings(path.name, tree)
        for node, doc in _iter_docstrings(tree):
            if not {"tests", "externals"}.intersection(path.relative_to(package).parts):
                try:
                    _check_numpy_structure(doc)
                except (AssertionError, ValueError) as exc:
                    location = (
                        f"{path.relative_to(package)}:{getattr(node, 'lineno', 1)}"
                    )
                    raise AssertionError(f"{location}: {exc}") from exc
            for key in PLACEHOLDER.findall(doc):
                # This one is syntax documentation inside the manager itself.
                if path.name == "docstring.py" and key == "name":
                    continue
                unresolved.append(
                    f"{path.relative_to(package)}:{getattr(node, 'lineno', 1)}: {key}"
                )

    assert not unresolved, "Unexpanded installed docstrings:\n" + "\n".join(unresolved)


if __name__ == "__main__":
    main()
