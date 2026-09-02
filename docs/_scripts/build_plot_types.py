#!/usr/bin/env python3
"""
Regenerate the visual plot-type index before a documentation build.

Run from ``conf.py`` the same way ``fetch_releases.py`` is: the page and its
thumbnails are generated artefacts, so a clean checkout builds them rather than
carrying 60-odd PNGs in the repository. Rendering is skipped when the icons are
already present, so a local rebuild costs nothing.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GENERATOR = os.path.join(ROOT, "tools", "cheatsheet")

sys.path.insert(0, GENERATOR)


def main():
    try:
        import docs_index
    except ImportError as error:  # the tools folder is not shipped in sdists
        print(f"plot-type index skipped: {error}")
        return
    try:
        docs_index.main()
    except Exception as error:  # never fail the docs build over a thumbnail
        print(f"plot-type index skipped: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
