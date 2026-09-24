#!/usr/bin/env python3
"""Remove vector colorbar seams without rebuilding an edited draw.io layout."""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote, unquote
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def crisp_colorbars(root):
    """Touch one-dimensional QuadMesh colorbars, preserving 2D plot meshes."""
    changed = 0
    for group in root.iter(f"{{{SVG}}}g"):
        if not group.get("id", "").startswith("QuadMesh"):
            continue
        paths = group.findall(f"{{{SVG}}}path")
        # A colorbar consists of rectangles all sharing one coordinate extent.
        import re
        boxes = []
        for path in paths:
            coords = [float(v) for v in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", path.get("d", ""))]
            if len(coords) < 8 or len(coords) % 2:
                break
            xs, ys = coords[::2], coords[1::2]
            boxes.append((min(xs), max(xs), min(ys), max(ys)))
        if not boxes or len(boxes) != len(paths):
            continue
        vertical = len({b[:2] for b in boxes}) == 1
        horizontal = len({b[2:] for b in boxes}) == 1
        if not (vertical or horizontal):
            continue
        if group.get("shape-rendering") != "crispEdges":
            group.set("shape-rendering", "crispEdges")
            changed += 1
    return changed


def patch_drawio(path):
    tree = ET.parse(path)
    before = deepcopy(tree.getroot())
    changed_ids = set()
    bars = strips = 0
    for cell in tree.findall(".//mxCell"):
        original = cell.get("style", "")
        style = dict(item.split("=", 1) for item in original.split(";") if "=" in item)
        image = style.get("image", "")
        if image.startswith("data:image/svg+xml,"):
            svg = ET.fromstring(unquote(image.split(",", 1)[1]))
            count = crisp_colorbars(svg)
            if count:
                encoded = quote(ET.tostring(svg, encoding="unicode"), safe="")
                original = original.replace(image, "data:image/svg+xml," + encoded)
                bars += count
        geometry = cell.find("mxGeometry")
        if geometry is not None:
            width = float(geometry.get("width", "0"))
            height = float(geometry.get("height", "0"))
            # Swatch segments only; leave section rails and plot geometry alone.
            if 0 < width < 5 and 8 <= height <= 16 and style.get("strokeColor") == "none" and "fillColor" in style:
                original = original.replace("strokeColor=none;", f"strokeColor={style['fillColor']};strokeWidth=0.5;")
                strips += 1
        if original != cell.get("style", ""):
            cell.set("style", original)
            changed_ids.add(cell.get("id"))
    # Verify that text, geometry, hierarchy and every other user edit survive.
    comparison = deepcopy(tree.getroot())
    old = {c.get("id"): c for c in before.findall(".//mxCell")}
    for cell in comparison.findall(".//mxCell"):
        if cell.get("id") in changed_ids:
            cell.set("style", old[cell.get("id")].get("style"))
    assert ET.tostring(comparison) == ET.tostring(before)
    if changed_ids:
        tree.write(path, encoding="utf-8", xml_declaration=True)
    return bars, strips


def patch_preview(path):
    tree = ET.parse(path)
    bars = strips = 0
    for image in tree.getroot().iter(f"{{{SVG}}}image"):
        href = image.get("href", "")
        if not href.startswith("data:image/svg+xml;base64,"):
            continue
        svg = ET.fromstring(base64.b64decode(href.split(",", 1)[1]))
        count = crisp_colorbars(svg)
        if count:
            image.set("href", "data:image/svg+xml;base64," + base64.b64encode(ET.tostring(svg)).decode())
            bars += count
    for rect in tree.getroot().iter(f"{{{SVG}}}rect"):
        w, h = float(rect.get("width", "0")), float(rect.get("height", "0"))
        if 0 < w < 5 and 8 <= h <= 16 and rect.get("stroke") == "none":
            rect.set("stroke", rect.get("fill"))
            rect.set("stroke-width", "0.5")
            rect.set("shape-rendering", "crispEdges")
            strips += 1
    if bars or strips:
        tree.write(path, encoding="utf-8", xml_declaration=True)
    return bars, strips


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print("Colorbars, swatch segments:", patch_drawio(args.path))


if __name__ == "__main__":
    main()
