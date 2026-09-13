#!/usr/bin/env python3
"""Build docs icons and draw.io assets without overwriting an edited diagram.

Default: render all required assets and update the docs plot-type index.
--drawio PATH explicitly assembles a new diagram and SVG/PNG previews.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PARTS = HERE / "parts"
MODULES = ("icons", "features", "drawio_details")


def render_figures():
    for name in MODULES:
        subprocess.run([sys.executable, str(PARTS / f"{name}.py")], cwd=PARTS, check=True)


def write_docs_page():
    subprocess.run([sys.executable, str(HERE / "docs_index.py")], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures", action="store_true", help="render figure assets")
    parser.add_argument("--docs", action="store_true", help="update the docs index and missing icons")
    parser.add_argument("--drawio", type=Path, metavar="OUTPUT", help="explicitly generate a diagram and previews at this path")
    args = parser.parse_args()
    default = not (args.figures or args.docs or args.drawio)
    if args.figures or default:
        render_figures()
    if args.docs or default:
        write_docs_page()
    if args.drawio:
        subprocess.run([sys.executable, str(HERE / "drawio.py"),
                        "--output", str(args.drawio.resolve()), "--png"], check=True)


if __name__ == "__main__":
    main()
