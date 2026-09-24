"""Validate that the installed package exposes literal expanded docstrings."""

from __future__ import annotations

import ast
import re
from importlib.metadata import distribution
from pathlib import Path

PLACEHOLDER = re.compile(r"%\(([^)]+)\)s")


def _iter_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                yield node, doc


def main() -> None:
    package = Path(distribution("ultraplot").locate_file("ultraplot"))
    assert package.is_dir(), f"installed package not found: {package}"
    assert (package / "py.typed").is_file(), "installed package is missing py.typed"
    assert not list(package.rglob("*.pyi")), "installed package unexpectedly ships .pyi files"

    unresolved = []
    for path in package.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node, doc in _iter_docstrings(tree):
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
