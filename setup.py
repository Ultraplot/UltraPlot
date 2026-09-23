"""Setuptools hooks used only while building distribution artifacts."""

import runpy
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

_ROOT = Path(__file__).resolve().parent


class build_py(_build_py):
    """Copy Python sources, then materialize shared docstring snippets."""

    def run(self):
        super().run()
        namespace = runpy.run_path(str(_ROOT / "tools" / "expand_docstrings.py"))
        namespace["expand_package"](Path(self.build_lib) / "ultraplot")


setup(cmdclass={"build_py": build_py})
