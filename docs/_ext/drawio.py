from __future__ import annotations

import base64
import hashlib
import html
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.osutil import relative_uri


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


class drawio_node(nodes.General, nodes.Element):
    pass


def _visit_drawio_html(self, node):
    # Write at HTML translation time so cached doctrees also recreate assets
    # when the output directory is cleaned. Content hashes allow browser caching.
    xml = node["xml"]
    digest = hashlib.sha256(xml.encode("utf-8")).hexdigest()
    asset = f"_drawio/{digest}.xml"
    path = Path(self.builder.outdir) / asset
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(xml, encoding="utf-8")
    url = relative_uri(self.builder.get_target_uri(self.builder.current_docname), asset)
    classes = html.escape(" ".join(["drawio-lazy", *node["classes"]]), quote=True)
    url = html.escape(url, quote=True)
    self.body.append(
        f'<div class="{classes}" data-drawio-url="{url}" '
        'style="min-height:24rem" aria-busy="true">'
        f'<a href="{url}">Load diagram</a>'
        '<noscript> (JavaScript is required to view this diagram.)</noscript>'
        '</div>'
    )
    raise nodes.SkipNode


def _skip_drawio(self, node):
    raise nodes.SkipNode


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

        node = drawio_node()
        node["xml"] = xml
        node["classes"] = self.options.get("class", [])
        return [node]


def _copy_loader(app, exception):
    if exception is None and app.builder.format == "html":
        target = Path(app.outdir) / "_static" / "drawio-lazy.js"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(__file__).with_name("drawio-lazy.js").read_bytes())


def setup(app):
    app.add_directive("drawio", DrawioDirective)

    app.add_node(
        drawio_node,
        html=(_visit_drawio_html, None),
        latex=(_skip_drawio, None),
        text=(_skip_drawio, None),
    )
    # Copy our loader without requiring changes to html_static_path.
    app.connect("build-finished", _copy_loader)
    app.add_js_file("drawio-lazy.js", loading_method="defer")

    return {
        "version": "2.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
