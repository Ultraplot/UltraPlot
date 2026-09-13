#!/usr/bin/env python3
"""Build a self-contained, editable A3 draw.io cheatsheet from existing assets.

Run after build.py --figures. Requires Pygments for editable code highlighting.
The SVG preview shares the same geometry; --png additionally requires CairoSVG.
"""
from __future__ import annotations

import argparse
import base64
import json
from html import escape
import re

from pygments.lexers import PythonLexer
from fix_svg_seams import crisp_colorbars
from pygments.token import Comment, Keyword, Name, Number, Operator, String
from pathlib import Path
import struct
from urllib.parse import quote
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
WIDTH, HEIGHT = 1680, 1188
INK, MUTED = "#182b3a", "#556471"
COLORS = ["#265c86", "#257a89", "#548348", "#aa7731", "#92556f"]
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


class Sheet:
    def __init__(self):
        self.document = ET.Element("mxfile", host="app.diagrams.net", type="device")
        diagram = ET.SubElement(self.document, "diagram", id="ultraplot-reference", name="UltraPlot cheatsheet")
        model = ET.SubElement(diagram, "mxGraphModel", dx=str(WIDTH), dy=str(HEIGHT),
                              grid="1", gridSize="10", page="1", pageScale="1",
                              pageWidth=str(WIDTH), pageHeight=str(HEIGHT), background="#ffffff",
                              math="0", shadow="0")
        self.root = ET.SubElement(model, "root")
        ET.SubElement(self.root, "mxCell", id="0")
        ET.SubElement(self.root, "mxCell", id="1", parent="0")
        self.svg = ET.Element(f"{{{SVG_NS}}}svg", width=str(WIDTH), height=str(HEIGHT),
                              viewBox=f"0 0 {WIDTH} {HEIGHT}")
        self.count = 1
        self.rect(0, 0, WIDTH, HEIGHT, "#ffffff", "none")

    def cell(self, x, y, w, h, value, style):
        assert x >= 0 and y >= 0 and x + w <= WIDTH and y + h <= HEIGHT
        self.count += 1
        cell = ET.SubElement(self.root, "mxCell", id=str(self.count), value=value,
                             style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), **{"as": "geometry"})

    def element(self, tag, **attrs):
        return ET.SubElement(self.svg, f"{{{SVG_NS}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()})

    def rect(self, x, y, w, h, fill, stroke="#d4dee5"):
        swatch = 0 < w < 5 and 8 <= h <= 16 and stroke == "none"
        if swatch:
            stroke = fill  # overlap neighbouring colour strips to hide SVG seams
        stroke_width = .5 if swatch else .7
        self.cell(x, y, w, h, "", f"rounded=0;whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};strokeWidth={stroke_width};")
        rect = self.element("rect", x=x, y=y, width=w, height=h, fill=fill, stroke=stroke, stroke_width=stroke_width)
        if swatch:
            rect.set("shape-rendering", "crispEdges")

    def text(self, x, y, w, text, size=12, color=INK, bold=False, mono=False, height=None):
        if size < 20:  # Keep the masthead size; enlarge the reading text.
            size = round(size * 1.12, 2)
        lines = text.splitlines()
        h = height or len(lines) * size * 1.35 + 4
        font = "DejaVu Sans Mono" if mono else "DejaVu Serif"
        runs = [[] for _ in lines]
        if mono:
            # Unprocessed tokens preserve the exact source, including incomplete
            # recipes and ellipses used in compact API captions.
            line_index = 0
            for offset, kind, value in PythonLexer().get_tokens_unprocessed(text):
                tint = color
                rest = text[offset + len(value):]
                if kind in Comment:
                    tint = "#657782"
                elif kind in String:
                    tint = "#347044"
                elif kind in Keyword:
                    tint = "#854b89"
                elif kind in Number:
                    tint = "#a45b26"
                elif kind in Name and re.match(r"\s*\(", rest):
                    tint = "#235e91"
                elif kind in Name and re.match(r"\s*=(?!=)", rest):
                    tint = "#815f2c"
                elif kind in Operator:
                    tint = "#596777"
                for j, part in enumerate(value.split("\n")):
                    if j:
                        line_index += 1
                    if part and line_index < len(runs):
                        runs[line_index].append((part, tint))
            html_lines = ["".join(
                f'<span style="color:{tint}">{escape(part)}</span>'
                for part, tint in line) for line in runs]
            value = ('<div style="white-space:pre;line-height:135%;text-align:left;">'
                     + '<br>'.join(html_lines) + '</div>')
        else:
            value = text
            runs = [[(line, color)] for line in lines]
        self.cell(x, y, w, h, value,
                  f"text;html={1 if mono else 0};whiteSpace=wrap;overflow=hidden;align=left;verticalAlign=top;"
                  f"spacing=0;fontFamily={font};fontSize={size};fontColor={color};"
                  f"fontStyle={1 if bold else 0};strokeColor=none;fillColor=none;")
        node = self.element("text", x=x, y=y + size, font_family=font, font_size=size,
                            fill=color, font_weight="bold" if bold else "normal")
        node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        for i, line in enumerate(runs):
            span = ET.SubElement(node, f"{{{SVG_NS}}}tspan", x=str(x), y=str(y + size + i * size * 1.35))
            for part, tint in line:
                token = ET.SubElement(span, f"{{{SVG_NS}}}tspan", fill=tint)
                token.text = part
        return h

    def picture(self, name, x, y, w, h):
        path = ASSETS / (name + ".svg")
        if path.exists():
            svg = ET.parse(path).getroot()
            crisp_colorbars(svg)
            _, _, iw, ih = map(float, svg.attrib["viewBox"].split())
            # Normalize the XML and remove the external SVG DTD declaration.
            raw = ET.tostring(svg, encoding="utf-8")
            mime = "image/svg+xml"
            drawio_uri = "data:image/svg+xml," + quote(raw.decode(), safe="")
        else:
            path = ASSETS / (name + ".png")
            if not path.exists():
                raise SystemExit(f"Missing {path}. Run tools/cheatsheet/build.py --figures first.")
            raw = path.read_bytes()
            iw, ih = struct.unpack(">II", raw[16:24])
            mime = "image/png"
            drawio_uri = "data:image/png," + base64.b64encode(raw).decode()
        scale = min(w / iw, h / ih)
        pw, ph = round(iw * scale, 3), round(ih * scale, 3)
        px, py = round(x + (w - pw) / 2, 3), round(y + (h - ph) / 2, 3)
        self.cell(px, py, pw, ph, "", "shape=image;verticalLabelPosition=bottom;verticalAlign=top;"
                  f"imageAspect=1;aspect=fixed;image={drawio_uri};")
        self.element("image", x=px, y=py, width=pw, height=ph,
                     href=f"data:{mime};base64,{base64.b64encode(raw).decode()}")


def build():
    """Dense galleries with extra room for sharing, legends and colorbars."""
    s = Sheet()
    s.text(24, 12, 550, "UltraPlot", 40, bold=True)
    s.text(253, 28, 750, "WHAT ULTRAPLOT ADDS", 22, COLORS[0], bold=True)
    s.text(1100, 18, 550, "A companion to the Matplotlib cheatsheet", 15, bold=True)
    s.text(1100, 43, 550, "import ultraplot as uplt\nfig, ax = uplt.subplots()", 13, MUTED, mono=True)
    s.text(24, 70, 1625, "Layout, guides and plotting conveniences — with room for the details that make a multi-panel figure work.", 14, MUTED)

    def panel(x, y, w, h, title, color):
        s.rect(x, y, w, h, "#ffffff")
        s.rect(x, y, w, 3, color, "none")
        s.text(x + 10, y + 9, w - 20, title, 16 if w < 300 else 17, color, bold=True)

    def icon(asset, label, x, y, w, size, color=INK):
        s.picture(asset, x + (w - size) / 2, y, size, size)
        s.text(x + 3, y + size + 4, w - 6, label, 10.2, color, mono=True)

    # The three sharing renders use the same 2x2 data with different ranges.
    panel(24, 106, 690, 345, "ADVANCED AXIS SHARING", COLORS[0])
    for i, (key, label, note) in enumerate([
        ("none", "share=False", "Independent axes"),
        ("limits", "share='limits'", "Limits per row / column"),
        ("all", "share='all'", "Limits across all panels"),
    ]):
        x = 34 + i * 224
        s.text(x, 146, 214, label, 12, COLORS[0], bold=True, mono=True)
        s.picture("drawio/sharing_" + key, x, 168, 208, 161)
        s.text(x, 334, 214, note, 11, MUTED)
    s.text(34, 350, 670,
           "'labels': share axis labels  •  'limits': also link limits  •  True: also hide inner tick labels",
           10.6, MUTED)
    s.text(34, 373, 670,
           "uplt.subplots(nrows=2, ncols=2, sharex='all', sharey='limits',\n"
           "              span=True, sharexticklabels=False)\n"
           "axs.share_labels(axis='both')  # centre labels across this grid", 11.3, mono=True)
    s.text(34, 430, 670,
           "spanx / spany: spanning labels  •  sharexlimits / shareylabels: individual overrides",
           10.7, MUTED)

    panel(732, 106, 924, 345, "SUBPLOTS, LABELS & ANNOTATIONS", COLORS[0])
    layouts = [
        ("mosaic_array", "subplots([[…]])"), ("physical_units", "refwidth='55mm'"),
        ("subplotgrid", "axs[:, 1]"), ("spanning_labels", "span=True"),
        ("abc_labels", "abc='a.'"), ("edge_labels", "toplabels="),
        ("corner_titles", "urtitle="), ("format", "axs.format(…)"),
        ("panel_axes", "panel_axes('r')"), ("inset_axes", "inset_axes(…)"),
        ("dualx", "dualx(f)"), ("curved_text", "curvedtext()"),
    ]
    for i, (asset, label) in enumerate(layouts):
        icon("features/" + asset, label, 742 + (i % 6) * 150,
             148 + (i // 6) * 142, 150, 111, COLORS[0])
    s.text(742, 429, 900, "Slice and format a grid in one call; use physical units for axes, panels and spacing.", 11, MUTED)

    panel(24, 467, 690, 345, "COLORBARS: OUTSIDE, STACKED OR INSET", COLORS[1])
    for i, (asset, label) in enumerate([
        ("outer_guides", "loc='r'"), ("stacked_guides", "repeated loc='b'"),
        ("inset_guides", "loc='ll'"),
    ]):
        icon("features/" + asset, label, 34 + i * 224, 510, 214, 147, COLORS[1])
    s.text(34, 685, 670,
           "ax.pcolormesh(Z, levels=7, colorbar='r')\n"
           "ax.colorbar(m, loc='b', width='3mm', length=.7)\n"
           "fig.colorbar(m, loc='b', col=1)  # align to a figure column",
           11.5, mono=True)
    s.text(34, 746, 670,
           "Outer guides take layout slots; repeated guides queue on the same side.\n"
           "Sides: l r t b   •   Insets: ul ur ll lr   •   levels= / values= set colour intervals.",
           11.4, MUTED)
    s.text(34, 788, 670, "Control width in physical units and length as a fraction of the available span.", 11, MUTED)

    panel(732, 467, 636, 345, "LEGENDS FOR DATA ENCODINGS", COLORS[1])
    legends = [
        ("cat", "catlegend()", "Categories", "ax.catlegend(names,\n  colors=colors,\n  markers=markers)"),
        ("size", "sizelegend()", "Marker areas", "ax.sizelegend(\n  [12, 60, 150],\nlabels=['S','M','L'])"),
        ("num", "numlegend()", "Numeric keys", "ax.numlegend(\n  levels=[0, .5, 1],\n  cmap='batlow')"),
        ("entry", "entrylegend()", "Custom entries", "ax.entrylegend([\n {'label': 'Model',\n  'line': True}])"),
    ]
    for i, (asset, label, note, code) in enumerate(legends):
        x = 742 + i * 154
        s.text(x, 507, 146, label, 11.2, COLORS[1], bold=True, mono=True)
        s.picture("drawio/legend_" + asset, x, 533, 146, 139)
        s.text(x, 676, 146, note, 11.3, MUTED)
        s.text(x, 699, 146, code, 10, mono=True)
    s.text(742, 758, 616,
           "ax.plot(Y, labels=names, legend='b')  •  ax.geolegend(…)",
           10.7, mono=True)
    s.text(742, 786, 616,
           "Also on fig; add=False returns handles and labels for combined legends.",
           11, MUTED)

    panel(1386, 467, 270, 345, "BUNDLED COLORMAPS", COLORS[3])
    palette_path = ASSETS / "drawio" / "colormaps.json"
    if not palette_path.exists():
        raise SystemExit("Run parts/drawio_details.py to generate colormap samples.")
    palettes = json.loads(palette_path.read_text())
    for group_index, (group, entries) in enumerate(palettes.items()):
        y = 508 + group_index * 84
        s.text(1396, y, 250, group, 12, COLORS[3], bold=True)
        for row, entry in enumerate(entries):
            yy = y + 23 + row * 18
            s.text(1396, yy - 1, 72, entry["name"], 10.7, mono=True)
            colors = entry["colors"]
            for j, color in enumerate(colors):
                s.rect(1472 + j * 174 / len(colors), yy, 174 / len(colors), 12, color, "none")
    s.text(1396, 769, 250, "cmap='batlow'  # any plot\nuplt.show_cmaps()  # all maps", 10.5, mono=True)

    panel(24, 828, 1110, 311, "MORE PLOT TYPES & USEFUL VARIANTS", COLORS[4])
    plots = [
        ("beeswarm", "beeswarm"), ("ridgeline", "ridgeline"),
        ("lollipop", "lollipop"), ("parametric", "parametric"),
        ("curved_quiver", "curved_quiver"), ("graph", "graph"),
        ("sankey", "sankey"), ("ribbon", "ribbon"),
        ("chord_diagram", "chord_diagram"), ("radar_chart", "radar_chart"),
        ("phylogeny", "phylogeny"), ("taylor", "taylor"),
        ("bar-stack-True", "bar(stack=True)"), ("bar-negpos-True", "bar(negpos=True)"),
        ("area-stack-True", "area(stack=True)"), ("area-negpos-True", "area(negpos=True)"),
    ]
    for i, (asset, label) in enumerate(plots):
        icon("icons/" + asset, label, 34 + (i % 8) * 136,
             869 + (i // 8) * 125, 136, 96, COLORS[4])
    s.text(34, 1117, 1090,
           "Polar: chord_diagram, radar_chart, phylogeny  •  Taylor: proj='taylor'  •  Transposed variants: plotx, scatterx, …",
           10.3, MUTED)

    panel(1152, 828, 504, 311, "GEOGRAPHY & MAP FORMATTING", COLORS[3])
    s.picture("drawio/geography", 1162, 868, 234, 139)
    s.picture("drawio/regional_map", 1402, 862, 244, 145)
    s.text(1162, 1009, 234, "proj='robin' + colour levels + guide", 10.6, MUTED)
    s.text(1402, 1009, 244, "proj='merc' + lon/lat formatting", 10.6, MUTED)
    s.text(1162, 1032, 484,
           "fig, ax = uplt.subplots(proj='merc')\n"
           "ax.pcolormesh(lon, lat, Z, cmap='roma', colorbar='b')\n"
           "ax.format(land=True, ocean=True, coast=True,\n"
           "          borders=True, rivers=True, lonlabels='b',\n"
           "          latlabels='l', lonlim=(-15, 40), latlim=(30, 63))",
           10.5, mono=True)
    s.text(1162, 1116, 484, "Bundled colormaps: batlow, roma, …  •  uplt.show_cmaps()", 10.5, MUTED)
    s.text(24, 1150, 1630,
           "ultraplot.readthedocs.io  •  Built-in conveniences beyond Matplotlib’s core API; many can also be assembled manually in Matplotlib.",
           12, MUTED)
    s.text(24, 1167, 1630,
           "Companion to matplotlib.org/cheatsheets  •  All plots rendered with UltraPlot  •  Editable draw.io text and layout; embedded SVG plots",
           10, MUTED)
    return s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "ultraplot_cheatsheet.drawio")
    parser.add_argument("--png", action="store_true", help="also render the SVG preview using CairoSVG")
    args = parser.parse_args()
    sheet = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(sheet.document)
    ET.ElementTree(sheet.document).write(args.output, encoding="utf-8", xml_declaration=True)
    svg = args.output.with_suffix(".svg")
    ET.ElementTree(sheet.svg).write(svg, encoding="utf-8", xml_declaration=True)
    print(f"{args.output} ({sheet.count - 1} editable objects)")
    print(svg)
    if args.png:
        import cairosvg
        png = args.output.with_suffix(".png")
        cairosvg.svg2png(url=str(svg), write_to=str(png),
                         output_width=WIDTH * 2, output_height=HEIGHT * 2)
        print(png)


if __name__ == "__main__":
    main()
