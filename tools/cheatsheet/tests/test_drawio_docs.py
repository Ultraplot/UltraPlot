"""Integration checks for the lightweight draw.io Sphinx output."""
import base64
from pathlib import Path
import urllib.parse
import zlib

import pytest
from sphinx.application import Sphinx


EXTENSIONS = Path(__file__).resolve().parents[3] / "docs" / "_ext"


@pytest.mark.parametrize("builder", ["html", "dirhtml"])
@pytest.mark.parametrize("compressed", [False, True])
def test_lazy_drawio(tmp_path, builder, compressed):
    source = tmp_path / "src"
    source.mkdir()
    (source / "conf.py").write_text(
        f"import sys\nsys.path.insert(0, {str(EXTENSIONS)!r})\n"
        "extensions = ['drawio']\nmaster_doc = 'index'\n"
    )
    (source / "index.rst").write_text(
        "Diagrams\n========\n\n.. toctree::\n\n   nested/sheet\n"
    )
    nested = source / "nested"
    nested.mkdir()
    (nested / "sheet.rst").write_text(
        "Sheet\n=====\n\n.. drawio:: ../sheet.drawio\n   :page: Large\n"
        "   :class: custom-sheet\n\n.. drawio:: ../sheet.drawio\n   :page: 0\n"
    )
    graph = '<mxGraphModel><root><mxCell id="svg-heavy-payload" /></root></mxGraphModel>'
    if compressed:
        compressor = zlib.compressobj(wbits=-15)
        data = urllib.parse.quote(graph).encode()
        payload = base64.b64encode(compressor.compress(data) + compressor.flush()).decode()
    else:
        payload = graph
    diagram = source / "sheet.drawio"
    diagram.write_text(f'<mxfile><diagram name="Large">{payload}</diagram></mxfile>')
    output = tmp_path / "out"
    app = Sphinx(str(source), str(source), str(output), str(tmp_path / "doctrees"), builder)
    app.build()
    page = output / ("nested/sheet.html" if builder == "html" else "nested/sheet/index.html")
    markup = page.read_text()
    assert "svg-heavy-payload" not in markup
    assert "data-mxgraph" not in markup
    assert markup.count("data-drawio-url=") == 2
    assert "drawio-lazy custom-sheet" in markup
    prefix = "../" if builder == "html" else "../../"
    assert f'data-drawio-url="{prefix}_drawio/' in markup
    assets = list((output / "_drawio").glob("*.xml"))
    assert len(assets) == 1  # repeated pages share the cacheable asset
    assert "svg-heavy-payload" in assets[0].read_text()
    assert (output / "_static/drawio-lazy.js").exists()
    assert str(diagram) in app.env.dependencies["nested/sheet"]
    # Assets must also be restored when rendering cached doctrees.
    assets[0].unlink()
    app.build(force_all=True)
    assert assets[0].exists()
