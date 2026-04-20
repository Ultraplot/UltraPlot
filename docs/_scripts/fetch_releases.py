"""
Dynamically build the "What's new?" page from the GitHub releases feed.

The release notes on GitHub are written in Markdown and frequently mix raw
HTML (``<details><summary>`` blocks wrapping fenced code samples). The
previous implementation converted the body to RST via ``m2r2``, which left
the inner Markdown code fences inside ``.. raw:: html`` directives — Sphinx
then rendered them as literal text. This module instead converts each
release body to HTML (so fences become ``<pre><code>`` elements) and emits
a single ``.. raw:: html`` block per release wrapped in a styling hook
``div.uplt-whats-new-release-body``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import markdown
import requests

GITHUB_REPO = "ultraplot/ultraplot"
OUTPUT_RST = Path("whats_new.rst")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"

# Markdown extensions: fenced code (for ```python blocks), tables, attribute
# lists for class hooks, and md_in_html so block-level HTML such as
# ``<details>`` correctly contains parsed Markdown children.
_MD_EXTENSIONS = ("fenced_code", "tables", "attr_list", "md_in_html")

# Strip the trailing "by @user in PR_URL" attribution that GitHub auto-adds
# to release notes. Keep the PR link in parentheses so credit/traceability
# remains while removing the contributor handles from rendered output.
# GitHub author handles can include ``[bot]`` suffixes (``@dependabot[bot]``,
# ``@pre-commit-ci[bot]``); ``\w`` alone misses the brackets.
_PR_ATTRIBUTION = re.compile(
    r" by @[\w.\-]+(?:\[bot\])? in (https://github\.com/[^\s]+)"
)

# Match an ATX heading line, tolerating up-to-3 leading spaces. Authors
# occasionally indent whole sections by two spaces in the GitHub release
# editor (e.g. v2.0.1's "### Layout, Rendering, and Geo Improvements"),
# which python-markdown then parses as a paragraph rather than a heading.
# We capture the ``#`` run so we can both strip the indent and downgrade
# one level — the page already provides the H1 ("What's new?") and each
# release contributes a per-release RST H2, so body headings start at H2.
_ATX_HEADING = re.compile(r"^[ ]{0,3}(#{1,5})(?=\s)", flags=re.MULTILINE)


def _strip_pr_attribution(text: str) -> str:
    return _PR_ATTRIBUTION.sub(r" (\1)", text)


def _downgrade_headings(text: str) -> str:
    """Demote every Markdown ATX heading by one level (``#`` → ``##``, etc.)."""
    return _ATX_HEADING.sub(lambda m: "#" + m.group(1), text)


def _normalize_unicode(text: str) -> str:
    return text.replace("→", "->")


def _indent_html(html: str, indent: str = "   ") -> str:
    """Indent every line of ``html`` by ``indent`` for inclusion under ``.. raw:: html``."""
    return "\n".join(indent + line if line else line for line in html.splitlines())


def format_release_body(text: str) -> str:
    """
    Convert a GitHub release body (Markdown + embedded HTML) into an RST
    ``.. raw:: html`` block wrapped in ``div.uplt-whats-new-release-body``.

    Parameters
    ----------
    text : str
        Raw Markdown release body as returned by the GitHub releases API.

    Returns
    -------
    str
        Indented RST snippet ready to be appended to ``whats_new.rst``.
    """
    cleaned = _downgrade_headings(
        _normalize_unicode(_strip_pr_attribution(text or ""))
    ).strip()
    html_body = markdown.markdown(cleaned, extensions=list(_MD_EXTENSIONS))
    wrapped = f'<div class="uplt-whats-new-release-body">\n{html_body}\n</div>'
    return ".. raw:: html\n\n" + _indent_html(wrapped) + "\n"


def _format_release_title(release: dict) -> str:
    """
    Build the per-release section title in ``"<tag>: <name>"`` form,
    de-duplicating the tag if it is already a prefix of the release name.
    """
    tag = release["tag_name"].lower()
    title = (release.get("name") or "").strip()
    if title.lower().startswith(tag):
        title = title[len(tag) :].lstrip(" :-—–")
    return f"{tag}: {title}" if title else tag


def fetch_all_releases() -> list[dict]:
    """Fetch every GitHub release across paginated responses."""
    releases: list[dict] = []
    page = 1
    while True:
        response = requests.get(GITHUB_API_URL, params={"per_page": 30, "page": page})
        if response.status_code != 200:
            print(f"Error fetching releases: {response.status_code}")
            break
        page_data = response.json()
        if not page_data:
            break
        releases.extend(page_data)
        page += 1
    return releases


def _render_releases(releases: Iterable[dict]) -> str:
    """Render an iterable of release dicts to the full ``whats_new.rst`` body."""
    header = "What's new?"
    out = f".. _whats_new:\n\n{header}\n{'=' * len(header)}\n\n"
    for release in releases:
        title = _format_release_title(release)
        date = release["published_at"][:10]
        heading = f"{title} ({date})"
        out += f"{heading}\n{'-' * len(heading)}\n\n"
        out += format_release_body(release.get("body") or "") + "\n"
    return out


def fetch_releases() -> str:
    """Fetch the latest releases from GitHub and format them as RST."""
    releases = fetch_all_releases()
    if not releases:
        print("Error fetching releases!")
        return ""
    return _render_releases(releases)


def write_rst() -> None:
    """Write fetched releases to ``whats_new.rst``."""
    content = fetch_releases()
    if content:
        OUTPUT_RST.write_text(content, encoding="utf-8")
        print(f"Updated {OUTPUT_RST}")
    else:
        print("No updates to write.")


if __name__ == "__main__":
    write_rst()
