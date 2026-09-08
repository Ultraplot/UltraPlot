from __future__ import annotations

import inspect
import logging
import os
import pydoc
import re
import sys
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

# IMPORTANT:
# MCP stdio uses stdout for JSON-RPC communication, so all logging must go
# to stderr.
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(message)s",
)

log = logging.getLogger("ultraplot-mcp")


REPO = Path(
    os.environ.get(
        "ULTRAPLOT_REPO",
        Path(__file__).resolve().parents[1],
    )
).resolve()

DOCS = REPO / "docs"

log.debug("cwd  = %s", Path.cwd())
log.debug("REPO = %s", REPO)
log.debug("DOCS = %s", DOCS)
log.debug("DOCS exists = %s", DOCS.exists())


mcp = MCPServer(
    "UltraPlot",
    instructions="""
Tools for understanding and using the UltraPlot Python plotting library.

Use these tools to inspect the installed/current UltraPlot API and search the
UltraPlot documentation and examples.

Prefer UltraPlot-native idioms over equivalent low-level Matplotlib code.

When answering questions about UltraPlot behavior:
1. Inspect the live API when relevant.
2. Search the documentation for usage guidance and examples.
3. Do not guess UltraPlot-specific parameters when they can be looked up.
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
    """Return useful normalized search terms."""
    return [
        term
        for term in re.findall(r"\w+", query.lower())
        if term not in STOPWORDS and len(term) > 1
    ]


def _text_files(
    *,
    include_release_notes: bool = False,
):
    """Yield searchable documentation and example files."""
    if not DOCS.exists():
        return

    seen: set[Path] = set()

    for pattern in ("**/*.rst", "**/*.md", "**/*.py"):
        for path in DOCS.glob(pattern):
            if path in seen:
                continue

            seen.add(path)

            if not include_release_notes:
                if path.name.lower() in IGNORED_DOCS:
                    continue

            yield path


def _score_document(
    text: str,
    query: str,
    terms: list[str],
    path: Path,
) -> float:
    """Calculate a simple relevance score for a documentation file."""
    lower = text.lower()
    query_lower = query.lower().strip()
    stem = path.stem.lower()

    score = 0.0

    # Strongly reward exact phrase matches.
    if query_lower:
        score += lower.count(query_lower) * 50

    # Reward matching individual terms.
    matched_terms = 0

    for term in terms:
        occurrences = len(
            re.findall(
                rf"\b{re.escape(term)}\w*\b",
                lower,
            )
        )

        if occurrences:
            matched_terms += 1
            score += occurrences

        # Filename matches are particularly useful.
        if term in stem:
            score += 20

    # Reward documents that cover several distinct concepts in the query.
    score += matched_terms * 5

    # Strong bonus if all useful query terms appear somewhere.
    if terms and matched_terms == len(terms):
        score += 20

    return score


def _best_match_position(
    text: str,
    query: str,
    terms: list[str],
) -> int:
    """Find a useful position around which to extract a result snippet."""
    lower = text.lower()

    # Prefer exact phrase.
    exact = lower.find(query.lower().strip())
    if exact >= 0:
        return exact

    positions: list[int] = []

    for term in terms:
        match = re.search(
            rf"\b{re.escape(term)}\w*\b",
            lower,
        )
        if match:
            positions.append(match.start())

    if positions:
        return min(positions)

    return 0


def _snippet(
    text: str,
    query: str,
    terms: list[str],
    *,
    before: int = 700,
    after: int = 2200,
) -> str:
    """Extract a useful section of text around a search match."""
    position = _best_match_position(text, query, terms)

    start = max(0, position - before)
    end = min(len(text), position + after)

    snippet = text[start:end]

    # Make truncated results visually obvious.
    if start:
        snippet = "...\n" + snippet

    if end < len(text):
        snippet += "\n..."

    return snippet


def _search_files(
    query: str,
    *,
    limit: int = 8,
    include_release_notes: bool = False,
) -> list[dict[str, Any]]:
    """Shared implementation for documentation searches."""
    query = query.strip()

    if not query:
        return []

    terms = _query_terms(query)

    # Fall back to all query words if every word happened to be a stopword.
    if not terms:
        terms = re.findall(r"\w+", query.lower())

    results: list[dict[str, Any]] = []

    for path in _text_files(
        include_release_notes=include_release_notes,
    ):
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
                "path": str(path.relative_to(REPO)),
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
def ping() -> str:
    """Check whether the UltraPlot MCP server is running."""
    return "pong"


@mcp.tool()
def search_docs(
    query: str,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """
    Search the UltraPlot documentation and examples.

    Use this for questions about how to accomplish a plotting task, how
    UltraPlot features behave, or to find relevant examples.

    Release notes and changelog files are deliberately excluded from this
    search because they tend to dominate normal documentation queries.
    """
    log.debug(
        "search_docs(query=%r, limit=%r)",
        query,
        limit,
    )

    limit = max(1, min(limit, 20))

    return _search_files(
        query,
        limit=limit,
        include_release_notes=False,
    )


@mcp.tool()
def search_release_notes(
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Search UltraPlot release notes.

    Use this when asking when a feature was added, what changed between
    releases, whether behavior was recently modified, or for other
    version-history questions.
    """
    log.debug(
        "search_release_notes(query=%r, limit=%r)",
        query,
        limit,
    )

    limit = max(1, min(limit, 20))

    release_file = DOCS / "whats_new.rst"

    if not release_file.exists():
        return []

    try:
        text = release_file.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return []

    terms = _query_terms(query)

    if not terms:
        terms = re.findall(r"\w+", query.lower())

    score = _score_document(
        text,
        query,
        terms,
        release_file,
    )

    if score <= 0:
        return []

    return [
        {
            "path": str(release_file.relative_to(REPO)),
            "score": score,
            "content": _snippet(
                text,
                query,
                terms,
                before=900,
                after=3000,
            ),
        }
    ][:limit]


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
    log.debug("RAW symbol = %r", symbol)

    symbol = symbol.strip()

    # Be forgiving when a human accidentally includes the field label.
    if symbol.startswith("symbol:"):
        symbol = symbol.removeprefix("symbol:").strip()

    if not symbol.startswith("ultraplot"):
        symbol = f"ultraplot.{symbol}"

    log.debug("NORMALIZED symbol = %r", symbol)

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
    Return the Python source code for an UltraPlot object.

    Useful when documentation is insufficient and the implementation of the
    current UltraPlot checkout needs to be inspected.
    """
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

    ``path`` should normally be a path returned by ``search_docs``, for example:
        docs/subplots.py
        docs/projections.py
        docs/why.rst
    """
    path = path.strip()

    target = (REPO / path).resolve()

    if not target.is_relative_to(REPO):
        raise ValueError("Path must be inside the UltraPlot repository.")

    if not target.is_file():
        raise FileNotFoundError(path)

    # Only expose ordinary text/code documentation files.
    if target.suffix.lower() not in {
        ".py",
        ".rst",
        ".md",
        ".txt",
        ".toml",
    }:
        raise ValueError(f"Unsupported file type: {target.suffix}")

    return target.read_text(
        encoding="utf-8",
        errors="replace",
    )


if __name__ == "__main__":
    mcp.run()
