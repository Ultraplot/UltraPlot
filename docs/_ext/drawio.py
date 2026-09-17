from __future__ import annotations

import base64
import html
import json
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

from docutils import nodes
from docutils.parsers.rst import Directive, directives


def _decode_diagram(diagram: ET.Element) -> str:
    """Return an mxGraphModel XML string from a <diagram> element."""

    # Uncompressed draw.io files can contain mxGraphModel directly.
    graph = diagram.find("mxGraphModel")
    if graph is not None:
        return ET.tostring(graph, encoding="unicode")

    # Normal compressed draw.io representation:
    # base64 -> raw DEFLATE -> URL decode
    encoded = (diagram.text or "").strip()

    if not encoded:
        raise ValueError("Draw.io diagram contains no data")

    compressed = base64.b64decode(encoded)
    inflated = zlib.decompress(compressed, -15).decode("utf-8")

    return urllib.parse.unquote(inflated)


def _get_page(path: Path, selector: str | None) -> str:
    root = ET.parse(path).getroot()
    diagrams = root.findall("diagram")

    if not diagrams:
        raise ValueError(f"No diagrams found in {path}")

    # Default to first page.
    if selector is None:
        return _decode_diagram(diagrams[0])

    # Numeric selector = page index.
    try:
        index = int(selector)
    except ValueError:
        index = None

    if index is not None:
        try:
            return _decode_diagram(diagrams[index])
        except IndexError:
            raise ValueError(
                f"Page index {index} does not exist in {path}"
            ) from None

    # Otherwise treat selector as page name.
    for diagram in diagrams:
        if diagram.get("name") == selector:
            return _decode_diagram(diagram)

    names = [d.get("name", "<unnamed>") for d in diagrams]
    raise ValueError(
        f"Page {selector!r} not found in {path}. "
        f"Available pages: {', '.join(names)}"
    )


class DrawioDirective(Directive):
    required_arguments = 1
    has_content = False

    option_spec = {
        "page": directives.unchanged,
        "class": directives.class_option,
    }

    def run(self):
        env = self.state.document.settings.env

        # Resolve relative to the .rst file containing the directive.
        source = Path(env.doc2path(env.docname)).resolve()
        path = (source.parent / self.arguments[0]).resolve()

        if not path.exists():
            raise self.error(f"Draw.io file not found: {path}")

        # Tell Sphinx that changes to the .drawio file should rebuild this page.
        env.note_dependency(str(path))

        try:
            xml = _get_page(path, self.options.get("page"))
        except (ET.ParseError, ValueError) as exc:
            raise self.error(str(exc)) from exc

        config = {
            "xml": xml,
            "resize": True,
            "fit": True,
            "nav": False,
            "lightbox": False,
            "toolbar": "",
        }

        classes = ["mxgraph", *self.options.get("class", [])]

        # data-mxgraph is an HTML attribute, so escape the complete JSON string.
        payload = html.escape(
            json.dumps(config, separators=(",", ":")),
            quote=True,
        )

        markup = (
            f'<div class="{" ".join(classes)}" '
            f'data-mxgraph="{payload}"></div>'
        )

        return [nodes.raw("", markup, format="html")]


def setup(app):
    app.add_directive("drawio", DrawioDirective)

    # Official diagrams.net viewer.
    app.add_js_file(
        "https://viewer.diagrams.net/js/viewer-static.min.js"
    )

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
