#!/usr/bin/env python3
"""
Build the UltraPlot cheatsheet.

Renders every figure part with UltraPlot, then hands the assets to Typst to
lay out. This mirrors how matplotlib builds its own cheatsheets: small scripts
produce the panels, and the document engine assembles them.

    micromamba run -n ultraplot-dev python tools/cheatsheet/build.py
    micromamba run -n ultraplot-dev python tools/cheatsheet/build.py --figures
    micromamba run -n ultraplot-dev python tools/cheatsheet/build.py --typst
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "parts")
ROOT = os.path.dirname(os.path.dirname(HERE))

#: Part modules, in the order their output appears on the page.
MODULES = ("layout", "icons", "features", "color", "guides", "geo")


def render_figures():
    """
    Run every part script in its own process, so one failure is isolated.
    """
    sys.path.insert(0, PARTS)
    for name in MODULES:
        print(f"{name}.py")
        result = subprocess.run(
            [sys.executable, os.path.join(PARTS, f"{name}.py")],
            cwd=PARTS,
        )
        if result.returncode:
            raise SystemExit(f"{name}.py failed with code {result.returncode}")


def compile_document(name, stem, png=True):
    """
    Compile one Typst document to PDF, and optionally to PNG pages.
    """
    source = os.path.join(HERE, name)
    pdf = os.path.join(ROOT, f"{stem}.pdf")
    subprocess.run(["typst", "compile", "--root", HERE, source, pdf], check=True)
    print(f"  {os.path.relpath(pdf, ROOT)}")
    if png:
        pattern = os.path.join(ROOT, stem + "_p{p}.png")
        subprocess.run(
            [
                "typst",
                "compile",
                "--root",
                HERE,
                "--format",
                "png",
                "--ppi",
                "150",
                source,
                pattern,
            ],
            check=True,
        )
        print(f"  {os.path.relpath(pattern, ROOT)}")


def compile_typst(png=True):
    """
    Compile both sheets: the three-page cheatsheet and the plot-type poster.
    """
    compile_document("cheatsheet.typ", "ultraplot_cheatsheet", png=png)
    compile_document("poster.typ", "ultraplot_plot_types", png=png)


def write_docs_page():
    """
    Regenerate the documentation's visual plot-type index.
    """
    subprocess.run([sys.executable, os.path.join(HERE, "docs_index.py")], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures", action="store_true", help="only render figures")
    parser.add_argument("--typst", action="store_true", help="only run typst")
    parser.add_argument("--docs", action="store_true", help="only write the docs page")
    args = parser.parse_args()
    only = args.figures or args.typst or args.docs
    if args.figures or not only:
        render_figures()
    if args.typst or not only:
        compile_typst()
    if args.docs or not only:
        write_docs_page()


if __name__ == "__main__":
    main()
