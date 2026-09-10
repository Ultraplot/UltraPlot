from __future__ import annotations

import inspect
import logging
import os
import pydoc
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

# stdout is reserved for MCP JSON-RPC when using the stdio transport.
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(message)s",
)

log = logging.getLogger("ultraplot-mcp")


PACKAGE_ROOT = Path(__file__).resolve().parent

# Development checkout:
#
# ultraplot/
# ├── docs/
# ├── ultraplot/
# │   └── mcp.py
# └── pyproject.toml
#
REPO = Path(
    os.environ.get(
        "ULTRAPLOT_REPO",
        PACKAGE_ROOT.parent,
    )
).resolve()

SOURCE_DOCS = REPO / "docs"

# For distributions, the docs can eventually be bundled here:
#
# ultraplot/
# ├── mcp.py
# └── _mcp_docs/
#
PACKAGED_DOCS = PACKAGE_ROOT / "_mcp_docs"

if "ULTRAPLOT_MCP_DOCS" in os.environ:
    DOCS = Path(os.environ["ULTRAPLOT_MCP_DOCS"]).resolve()
elif SOURCE_DOCS.is_dir():
    DOCS = SOURCE_DOCS
elif PACKAGED_DOCS.is_dir():
    DOCS = PACKAGED_DOCS
else:
    DOCS = SOURCE_DOCS

log.debug("cwd = %s", Path.cwd())
log.debug("package root = %s", PACKAGE_ROOT)
log.debug("repo = %s", REPO)
log.debug("docs = %s", DOCS)
log.debug("docs exists = %s", DOCS.exists())


mcp = MCPServer(
    "UltraPlot",
    instructions="""
Tools for understanding and using the UltraPlot Python plotting library.

Prefer UltraPlot-native idioms over equivalent low-level Matplotlib code.

When answering UltraPlot-specific questions:
1. Inspect the live UltraPlot API when relevant.
2. Search the UltraPlot documentation and examples.
3. Prefer documented behavior over guessing.
4. Inspect source code when documentation is insufficient.

The tools operate against the UltraPlot version installed alongside this MCP.
""".strip(),
)


IGNORED_DOCS = {
    "whats_new.rst",
    "changelog.rst",
    "changes.rst",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "different",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "per",
    "the",
    "to",
    "use",
    "using",
    "what",
    "when",
    "where",
    "which",
    "with",
}


def _query_terms(query: str) -> list[str]:
    """Normalize a search query into meaningful terms."""
    terms = re.findall(r"\w+", query.lower())

    filtered = [term for term in terms if term not in STOPWORDS and len(term) > 1]

    return filtered or terms


def _text_files():
    """Yield searchable documentation files."""
    if not DOCS.is_dir():
        return

    seen: set[Path] = set()

    for pattern in ("**/*.rst", "**/*.md", "**/*.py"):
        for path in DOCS.glob(pattern):
            if path in seen:
                continue

            seen.add(path)

            if path.name.lower() in IGNORED_DOCS:
                continue

            yield path


def _score_document(
    text: str,
    query: str,
    terms: list[str],
    path: Path,
) -> float:
    """Calculate a simple relevance score."""
    lower = text.lower()
    query_lower = query.lower().strip()
    stem = path.stem.lower()

    score = 0.0
    matched_terms = 0

    # Exact phrase matches are particularly useful.
    if query_lower:
        score += lower.count(query_lower) * 50

    for term in terms:
        matches = re.findall(
            rf"\b{re.escape(term)}\w*\b",
            lower,
        )

        occurrences = len(matches)

        if occurrences:
            matched_terms += 1
            score += occurrences

        # A query matching the document name is strong evidence.
        if term in stem:
            score += 20

    # Reward matching multiple distinct concepts.
    score += matched_terms * 5

    if terms and matched_terms == len(terms):
        score += 20

    return score


def _best_match_position(
    text: str,
    query: str,
    terms: list[str],
) -> int:
    """Find a useful position for the returned snippet."""
    lower = text.lower()
    query_lower = query.lower().strip()

    # Exact phrase first.
    if query_lower:
        position = lower.find(query_lower)
        if position >= 0:
            return position

    # Find regions containing several query terms close together.
    positions: list[int] = []

    for term in terms:
        for match in re.finditer(
            rf"\b{re.escape(term)}\w*\b",
            lower,
        ):
            positions.append(match.start())

    if not positions:
        return 0

    positions.sort()

    # Find the densest window.
    best_position = positions[0]
    best_count = 0
    window = 2000

    for position in positions:
        count = sum(position <= other <= position + window for other in positions)

        if count > best_count:
            best_count = count
            best_position = position

    return best_position


def _snippet(
    text: str,
    query: str,
    terms: list[str],
    *,
    before: int = 600,
    after: int = 2400,
) -> str:
    """Extract a relevant chunk from a documentation file."""
    position = _best_match_position(
        text,
        query,
        terms,
    )

    start = max(0, position - before)
    end = min(len(text), position + after)

    result = text[start:end]

    if start:
        result = "...\n" + result

    if end < len(text):
        result += "\n..."

    return result


def _display_path(path: Path) -> str:
    """Return a stable user-facing documentation path."""
    relative = path.relative_to(DOCS)
    return str(Path("docs") / relative)


def _resolve_doc_path(path: str) -> Path:
    """Resolve a user-facing documentation path."""
    path = path.strip()

    supplied = Path(path)

    if supplied.parts and supplied.parts[0] == "docs":
        supplied = Path(*supplied.parts[1:])

    target = (DOCS / supplied).resolve()

    try:
        target.relative_to(DOCS.resolve())
    except ValueError as exc:
        raise ValueError("Path must be inside the UltraPlot documentation.") from exc

    return target


@mcp.tool()
def ping() -> str:
    """Check whether the UltraPlot MCP server is working."""
    log.info("ping")
    return "pong"


@mcp.tool()
def search_docs(
    query: str,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """
    Search UltraPlot documentation and examples.

    Use this for questions about plotting tasks, UltraPlot behavior,
    configuration, layouts, projections, legends, colorbars, plotting
    commands, formatting, and usage examples.

    Release notes are intentionally excluded.
    """
    log.info("search_docs: %r", query)

    query = query.strip()

    if not query:
        return []

    if not DOCS.is_dir():
        return [
            {
                "error": "UltraPlot documentation is not installed.",
                "docs_path": str(DOCS),
            }
        ]

    limit = max(1, min(limit, 20))
    terms = _query_terms(query)

    results: list[dict[str, Any]] = []

    for path in _text_files():
        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        score = _score_document(
            text,
            query,
            terms,
            path,
        )

        if score <= 0:
            continue

        results.append(
            {
                "path": _display_path(path),
                "score": score,
                "content": _snippet(
                    text,
                    query,
                    terms,
                ),
            }
        )

    results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    return results[:limit]


@mcp.tool()
def search_release_notes(
    query: str,
) -> list[dict[str, Any]]:
    """
    Search UltraPlot release notes.

    Use this for questions about when features were introduced,
    version history, recent changes, fixes, or deprecations.
    """
    log.info("search_release_notes: %r", query)

    path = DOCS / "whats_new.rst"

    if not path.is_file():
        return []

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return []

    query = query.strip()

    if not query:
        return []

    terms = _query_terms(query)

    score = _score_document(
        text,
        query,
        terms,
        path,
    )

    if score <= 0:
        return []

    return [
        {
            "path": _display_path(path),
            "score": score,
            "content": _snippet(
                text,
                query,
                terms,
                before=900,
                after=3200,
            ),
        }
    ]


@mcp.tool()
def get_api(symbol: str) -> dict[str, Any]:
    """
    Inspect a live UltraPlot Python object.

    Examples:
        ultraplot.subplots
        ultraplot.axes.Axes.format
        ultraplot.axes.PlotAxes.plot
        ultraplot.figure.Figure.colorbar

    The ``ultraplot.`` prefix may be omitted.
    """
    log.info("get_api: %r", symbol)

    symbol = symbol.strip()

    # Be forgiving when entered manually in MCP Inspector.
    if symbol.startswith("symbol:"):
        symbol = symbol.removeprefix("symbol:").strip()

    if not symbol.startswith("ultraplot"):
        symbol = f"ultraplot.{symbol}"

    obj = pydoc.locate(symbol)

    if obj is None:
        return {
            "found": False,
            "symbol": symbol,
        }

    try:
        unwrapped = inspect.unwrap(obj)
    except ValueError:
        unwrapped = obj

    try:
        signature = str(inspect.signature(unwrapped))
    except (TypeError, ValueError):
        signature = None

    try:
        source_file = inspect.getsourcefile(unwrapped)
    except TypeError:
        source_file = None

    try:
        source_line = inspect.getsourcelines(unwrapped)[1]
    except (OSError, TypeError):
        source_line = None

    try:
        docstring = inspect.getdoc(obj)
    except Exception:
        docstring = None

    return {
        "found": True,
        "symbol": symbol,
        "signature": signature,
        "docstring": docstring,
        "source_file": source_file,
        "source_line": source_line,
    }


@mcp.tool()
def get_source(
    symbol: str,
) -> dict[str, Any]:
    """
    Return source code for an UltraPlot Python object.

    Use this when the documentation does not fully explain the
    implementation or current behavior.
    """
    log.info("get_source: %r", symbol)

    symbol = symbol.strip()

    if not symbol.startswith("ultraplot"):
        symbol = f"ultraplot.{symbol}"

    obj = pydoc.locate(symbol)

    if obj is None:
        return {
            "found": False,
            "symbol": symbol,
        }

    try:
        obj = inspect.unwrap(obj)
    except ValueError:
        pass

    try:
        source = inspect.getsource(obj)
    except (OSError, TypeError):
        source = None

    try:
        source_file = inspect.getsourcefile(obj)
    except TypeError:
        source_file = None

    try:
        source_line = inspect.getsourcelines(obj)[1]
    except (OSError, TypeError):
        source_line = None

    return {
        "found": True,
        "symbol": symbol,
        "source_file": source_file,
        "source_line": source_line,
        "source": source,
    }


@mcp.tool()
def read_doc(path: str) -> str:
    """
    Read an UltraPlot documentation or example file.

    Normally use a path returned by ``search_docs``, for example:
        docs/subplots.py
        docs/projections.py
        docs/why.rst
    """
    log.info("read_doc: %r", path)

    target = _resolve_doc_path(path)

    if not target.is_file():
        raise FileNotFoundError(path)

    if target.suffix.lower() not in {
        ".py",
        ".rst",
        ".md",
        ".txt",
    }:
        raise ValueError(f"Unsupported documentation file type: {target.suffix}")

    return target.read_text(
        encoding="utf-8",
        errors="replace",
    )


def _mcp_server_command() -> list[str]:
    """
    Return a stable command Codex can use to launch this MCP.

    Prefer the installed console script. During development, fall back to
    the current Python interpreter and this module.
    """
    executable = shutil.which("ultraplot-mcp")

    if executable:
        return [str(Path(executable).resolve())]

    # Useful when testing directly from the source checkout.
    return [
        sys.executable,
        str(Path(__file__).resolve()),
    ]


def install_codex() -> None:
    """Register the UltraPlot MCP server with Codex."""
    codex = shutil.which("codex")

    if codex is None:
        raise RuntimeError(
            "Codex CLI was not found on PATH.\n"
            "Install Codex first, then run:\n\n"
            "    ultraplot-mcp install codex"
        )

    server_command = _mcp_server_command()

    command = [
        codex,
        "mcp",
        "add",
        "ultraplot",
        "--",
        *server_command,
    ]

    log.info(
        "Registering UltraPlot MCP with Codex: %s",
        " ".join(command),
    )

    try:
        subprocess.run(
            command,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Codex could not register the UltraPlot MCP.\n"
            "If an UltraPlot MCP entry already exists, remove or update "
            "that entry and try again."
        ) from exc

    print()
    print("UltraPlot MCP registered with Codex.")
    print()
    print("Codex will launch:")
    print()
    print("    " + " ".join(server_command))
    print()
    print("Restart Codex, then use /mcp to verify the connection.")


def _print_help() -> None:
    print("""Usage:
  ultraplot-mcp
      Run the UltraPlot MCP server over stdio.

  ultraplot-mcp install codex
      Register the installed UltraPlot MCP with Codex.

Examples:
  ultraplot-mcp
  ultraplot-mcp install codex
""")


def main() -> None:
    args = sys.argv[1:]

    if not args:
        mcp.run()
        return

    if args in (["-h"], ["--help"], ["help"]):
        _print_help()
        return

    if args == ["install", "codex"]:
        install_codex()
        return

    print(
        f"Unknown command: {' '.join(args)}\n",
        file=sys.stderr,
    )
    _print_help()
    raise SystemExit(2)


if __name__ == "__main__":
    main()
