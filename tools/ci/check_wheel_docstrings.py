"""Validate that built wheels expose literal expanded docstrings."""

from __future__ import annotations

import ast
import re
import sys
import zipfile
from pathlib import Path

PLACEHOLDER = re.compile(r"%\\(([^)]+)\\)s")


def _iter_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                yield node, doc


def main(wheel: Path) -> None:
    unresolved = []
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert "ultraplot/py.typed" in names, "wheel is missing py.typed"
        assert not any(name.endswith(".pyi") for name in names), (
            "wheel unexpectedly ships .pyi files"
        )

        for name in names:
            if not name.startswith("ultraplot/") or not name.endswith(".py"):
                continue
            source = archive.read(name).decode("utf-8")
            tree = ast.parse(source, filename=name)
            for node, doc in _iter_docstrings(tree):
                for key in PLACEHOLDER.findall(doc):
                    # This one is syntax documentation inside the manager itself.
                    if name == "ultraplot/internals/docstring.py" and key == "name":
                        continue
                    unresolved.append(
                        f"{name}:{getattr(node, 'lineno', 1)}: {key}"
                    )

        plot_source = archive.read("ultraplot/axes/plot.py").decode("utf-8")
        plot_tree = ast.parse(plot_source, filename="ultraplot/axes/plot.py")
        plot_axes = next(
            node
            for node in plot_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PlotAxes"
        )
        plot = next(
            node
            for node in plot_axes.body
            if isinstance(node, ast.FunctionDef) and node.name == "plot"
        )
        plot_doc = ast.get_docstring(plot) or ""
        assert "Plot standard lines" in plot_doc
        assert "Parameters" in plot_doc

    assert not unresolved, "Unexpanded wheel docstrings:\n" + "\n".join(unresolved)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_wheel_docstrings.py path/to/ultraplot.whl")
    main(Path(sys.argv[1]))
