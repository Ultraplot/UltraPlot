#!/usr/bin/env python3
"""
Generate Astro markdown API pages from the UltraPlot source tree.

This script intentionally parses source files with ``ast`` instead of importing
modules, so generation does not depend on optional runtime dependencies.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SymbolDoc:
    kind: str
    name: str
    signature: str
    summary: str


@dataclass
class ModuleDoc:
    module: str
    source_path: Path
    summary: str
    classes: list[SymbolDoc]
    functions: list[SymbolDoc]


def _summary_from_docstring(doc: str | None) -> str:
    if not doc:
        return "No module docstring available."
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line
    return "No module docstring available."


def _module_name(root: Path, pyfile: Path) -> str:
    rel = pyfile.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return "ultraplot" if not parts else "ultraplot." + ".".join(parts)


def _format_signature(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        try:
            return f"({ast.unparse(node.args)})"
        except Exception:
            return "(...)"
    if isinstance(node, ast.ClassDef) and node.bases:
        try:
            bases = ", ".join(ast.unparse(base) for base in node.bases)
            return f"({bases})"
        except Exception:
            return "(...)"
    return ""


def _parse_module(pyfile: Path, package_root: Path) -> ModuleDoc:
    source = pyfile.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(pyfile))
    module_doc = ast.get_docstring(tree)
    module_name = _module_name(package_root, pyfile)

    classes: list[SymbolDoc] = []
    functions: list[SymbolDoc] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            classes.append(
                SymbolDoc(
                    kind="class",
                    name=node.name,
                    signature=_format_signature(node),
                    summary=_summary_from_docstring(ast.get_docstring(node)),
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            functions.append(
                SymbolDoc(
                    kind="function",
                    name=node.name,
                    signature=_format_signature(node),
                    summary=_summary_from_docstring(ast.get_docstring(node)),
                )
            )

    return ModuleDoc(
        module=module_name,
        source_path=pyfile,
        summary=_summary_from_docstring(module_doc),
        classes=classes,
        functions=functions,
    )


def _module_output_path(output_root: Path, module_name: str) -> Path:
    parts = module_name.split(".")
    return output_root.joinpath(*parts).with_suffix(".md")


def _write_module_page(output_root: Path, module_doc: ModuleDoc, repo_root: Path) -> str:
    dest = _module_output_path(output_root, module_doc.module)
    dest.parent.mkdir(parents=True, exist_ok=True)
    source_rel = module_doc.source_path.relative_to(repo_root).as_posix()
    title = module_doc.module
    lines = [
        "---",
        f'title: "{title}"',
        f'description: "{module_doc.summary.replace(chr(34), chr(39))}"',
        f'source: "{source_rel}"',
        "---",
        "",
        f"`{module_doc.module}`",
        "",
        module_doc.summary,
        "",
    ]

    if module_doc.classes:
        lines += ["## Public Classes", ""]
        for item in module_doc.classes:
            lines += [f"### `{item.name}{item.signature}`", "", item.summary, ""]

    if module_doc.functions:
        lines += ["## Public Functions", ""]
        for item in module_doc.functions:
            lines += [f"### `{item.name}{item.signature}`", "", item.summary, ""]

    if not module_doc.classes and not module_doc.functions:
        lines += ["No public classes or functions were detected in this module.", ""]

    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest.relative_to(output_root).with_suffix("").as_posix()


def _discover_modules(package_root: Path) -> list[Path]:
    files = sorted(package_root.rglob("*.py"))
    out: list[Path] = []
    for pyfile in files:
        rel = pyfile.relative_to(package_root)
        if rel.parts and rel.parts[0] in {"tests", "__pycache__"}:
            continue
        out.append(pyfile)
    return out


def _write_api_index(output_root: Path, links: list[tuple[str, str]]) -> None:
    index_path = output_root / "index.md"
    lines = [
        "---",
        'title: "API Reference"',
        'description: "Auto-generated API reference pages from UltraPlot source."',
        "order: 20",
        "---",
        "",
        "This section is generated from the `ultraplot/` source tree.",
        "",
        "## Modules",
        "",
    ]
    for module_name, slug in links:
        lines.append(f"- [`{module_name}`](/docs/api/{slug})")
    lines.append("")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path("ultraplot"),
        help="Path to the python package root (default: ultraplot).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("site/src/content/docs/api"),
        help="Output directory for generated markdown pages.",
    )
    parser.add_argument(
        "--max-modules",
        type=int,
        default=0,
        help="Optional cap on number of modules to generate (0 = no cap).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    package_root = (repo_root / args.package_root).resolve()
    output_root = (repo_root / args.output).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    modules = _discover_modules(package_root)
    if args.max_modules > 0:
        modules = modules[: args.max_modules]

    links: list[tuple[str, str]] = []
    for pyfile in modules:
        module_doc = _parse_module(pyfile, package_root)
        slug = _write_module_page(output_root, module_doc, repo_root)
        links.append((module_doc.module, slug))

    links.sort(key=lambda item: item[0])
    _write_api_index(output_root, links)
    print(f"Generated {len(links)} module pages in {output_root}")


if __name__ == "__main__":
    main()
