from html import unescape
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs" / "_scripts" / "fetch_releases.py"


def _load_module():
    spec = spec_from_file_location("uplt_fetch_releases", SCRIPT)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_format_release_body_renders_raw_html():
    module = _load_module()
    body = """
# UltraPlot v9.9.9

Highlights
----------

* Fix a regression by @cvanelteren in https://github.com/Ultraplot/UltraPlot/pull/123
* Replace arrows → with ASCII

```python
print("ok")
```
"""
    rendered = module.format_release_body(body)

    assert rendered.startswith(".. raw:: html")
    assert '<div class="uplt-whats-new-release-body">' in rendered
    assert "<h2>UltraPlot v9.9.9</h2>" in rendered
    assert "by @cvanelteren in" not in rendered
    assert "->" in unescape(rendered)
    assert '<code class="language-python">' in rendered


def test_fetch_releases_formats_titles(monkeypatch):
    module = _load_module()
    monkeypatch.setattr(
        module,
        "fetch_all_releases",
        lambda: [
            {
                "tag_name": "v1.2.3",
                "name": "v1.2.3: Release title",
                "published_at": "2026-04-02T10:00:00Z",
                "body": "Hello world",
            }
        ],
    )

    rendered = module.fetch_releases()

    assert ".. _whats_new:" in rendered
    assert "v1.2.3: Release title (2026-04-02)" in rendered
    assert ".. raw:: html" in rendered


def test_format_release_body_preserves_code_inside_details():
    """Regression test for the original issue — fenced code blocks nested inside
    ``<details>`` must turn into proper ``<pre><code>`` HTML, not literal
    backticks. The previous m2r2 pipeline left them unrendered."""
    module = _load_module()
    body = (
        "# v9.9.9\n\n"
        "<details><summary>snippet</summary>\n\n"
        "```python\n"
        "import ultraplot as uplt\n"
        "fig, ax = uplt.subplots()\n"
        "```\n\n"
        "</details>\n"
    )

    rendered = module.format_release_body(body)

    assert "<details><summary>snippet</summary>" in rendered
    assert '<pre><code class="language-python">' in rendered
    assert "import ultraplot as uplt" in rendered
    # No literal Markdown fences should leak through into the output
    assert "```python" not in rendered


def test_format_release_body_indents_for_raw_html_directive():
    """Every line of the wrapper must be indented by three spaces so the block
    is parsed as the body of the ``.. raw:: html`` directive."""
    module = _load_module()
    rendered = module.format_release_body("# Heading\n\nBody")

    lines = rendered.splitlines()
    assert lines[0] == ".. raw:: html"
    assert lines[1] == ""
    # All subsequent non-empty lines must start with the 3-space indent
    for line in lines[2:]:
        if line:
            assert line.startswith("   "), line


def test_fetch_releases_handles_empty_body(monkeypatch):
    """A release with an empty body must not crash and must still emit the
    section heading."""
    module = _load_module()
    monkeypatch.setattr(
        module,
        "fetch_all_releases",
        lambda: [
            {
                "tag_name": "v0.0.1",
                "name": "v0.0.1",
                "published_at": "2026-01-01T00:00:00Z",
                "body": None,
            }
        ],
    )

    rendered = module.fetch_releases()

    assert "v0.0.1 (2026-01-01)" in rendered
    assert ".. raw:: html" in rendered


def test_fetch_releases_returns_empty_string_when_api_returns_nothing(monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "fetch_all_releases", lambda: [])
    assert module.fetch_releases() == ""


def test_format_release_body_recognises_indented_atx_headings():
    """Some GitHub release bodies (e.g. v2.0.1) indent whole sections by two
    spaces in the source Markdown. python-markdown won't parse ``  ### Foo``
    as an ATX heading, so without normalisation those headings render as
    paragraphs (literal ``###`` text). The script must strip up to three
    leading spaces from heading lines before parsing."""
    module = _load_module()
    body = (
        "  ### Layout, Rendering, and Geo Improvements\n\n"
        "  - Bullet one\n"
        "  - Bullet two\n"
    )

    rendered = module.format_release_body(body)

    assert "<h4>Layout, Rendering, and Geo Improvements</h4>" in rendered
    assert "### Layout" not in rendered
    assert "<p>### " not in rendered


def test_format_release_body_strips_bot_attribution():
    """``@dependabot[bot]`` and ``@pre-commit-ci[bot]`` style handles must be
    stripped along with regular ``@user`` ones; only the PR URL should
    remain."""
    module = _load_module()
    body = (
        "* Bump deps by @dependabot[bot] in "
        "https://github.com/Ultraplot/UltraPlot/pull/671\n"
        "* Autoupdate by @pre-commit-ci[bot] in "
        "https://github.com/Ultraplot/UltraPlot/pull/674\n"
        "* Real fix by @cvanelteren in "
        "https://github.com/Ultraplot/UltraPlot/pull/696\n"
    )

    rendered = module.format_release_body(body)

    assert "@dependabot" not in rendered
    assert "@pre-commit-ci" not in rendered
    assert "@cvanelteren" not in rendered
    assert "https://github.com/Ultraplot/UltraPlot/pull/671" in rendered
    assert "https://github.com/Ultraplot/UltraPlot/pull/696" in rendered
