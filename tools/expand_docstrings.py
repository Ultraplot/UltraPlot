"""Materialize UltraPlot runtime docstring snippets in a copied package tree."""

from __future__ import annotations

import ast
import importlib
import re
import sys
from pathlib import Path

_PLACEHOLDER = re.compile(r"%\\(([^)]+)\\)s")


def _iter_docstring_literals(node):
    """Yield string literal nodes that are actual Python docstrings."""
    body = getattr(node, "body", ())
    if body:
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            yield first.value
    for child in body:
        if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            yield from _iter_docstring_literals(child)


def _module_name(package_root: Path, path: Path) -> str:
    relative = path.relative_to(package_root)
    if relative.name == "__init__.py":
        parts = relative.parent.parts
    else:
        parts = relative.with_suffix("").parts
    return ".".join((package_root.name, *parts))


def _expand(text: str, snippets) -> tuple[str, bool]:
    """Expand registered placeholders and report whether unknown keys remain."""
    missing = False

    def replace(match):
        nonlocal missing
        try:
            return str(snippets[match.group(1)])
        except KeyError:
            missing = True
            return match.group(0)

    return _PLACEHOLDER.sub(replace, text), missing


def _rewrite_file(path: Path, package_root: Path, snippets) -> int:
    source = path.read_bytes()
    tree = ast.parse(source, filename=str(path))
    literals = [
        node
        for node in _iter_docstring_literals(tree)
        if _PLACEHOLDER.search(node.value)
    ]
    if not literals:
        return 0

    expanded = [_expand(node.value, snippets) for node in literals]
    if any(missing for _, missing in expanded):
        # Some registries live in the module containing the documented object,
        # so import only when a key cannot be resolved from the central registry.
        importlib.import_module(_module_name(package_root, path))
        expanded = [_expand(node.value, snippets) for node in literals]

    lines = source.splitlines(keepends=True)
    offsets = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)

    replacements = []
    for node, (text, _) in zip(literals, expanded):
        if text == node.value:
            continue
        start = offsets[node.lineno - 1] + node.col_offset
        end = offsets[node.end_lineno - 1] + node.end_col_offset
        replacements.append((start, end, repr(text).encode("utf-8")))

    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    if replacements:
        path.write_bytes(source)
    return len(replacements)


def expand_package(package_root: Path) -> int:
    """Expand docstrings in package_root without touching checked-in sources."""
    package_root = Path(package_root).resolve()
    build_root = package_root.parent

    # Imports must resolve to the copied build tree, never the checkout.
    for name in tuple(sys.modules):
        if name == "ultraplot" or name.startswith("ultraplot."):
            del sys.modules[name]
    sys.path.insert(0, str(build_root))
    try:
        snippets = importlib.import_module("ultraplot.internals.docstring")._snippet_manager
        changed = 0
        for path in sorted(package_root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            changed += _rewrite_file(path, package_root, snippets)
        return changed
    finally:
        try:
            sys.path.remove(str(build_root))
        except ValueError:
            pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    count = expand_package(args.package)
    print(f"Expanded {count} docstrings in {args.package}")
