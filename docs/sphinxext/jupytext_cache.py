"""
Jupytext converter with a small on-disk cache for docs builds.
"""

import hashlib
import os
from pathlib import Path

import jupytext
import nbformat


def _get_cache_dir():
    """
    Return cache directory for converted jupytext notebooks.
    """
    override = os.environ.get("UPLT_DOCS_JUPYTEXT_CACHE_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    if os.environ.get("READTHEDOCS", "") == "True":
        return Path.home() / ".cache" / "ultraplot" / "jupytext"
    return Path(__file__).resolve().parent.parent / "_build" / ".jupytext-cache"


def reads_cached(inputstring, *, fmt="py:percent"):
    """
    Convert Jupytext source to a notebook and cache by content hash.
    """
    disabled = os.environ.get("UPLT_DOCS_DISABLE_JUPYTEXT_CACHE", "").strip().lower()
    if disabled in {"1", "true", "yes", "on"}:
        return jupytext.reads(inputstring, fmt=fmt)

    key = hashlib.sha256(
        (fmt + "\0" + getattr(jupytext, "__version__", "") + "\0" + inputstring).encode(
            "utf-8"
        )
    ).hexdigest()
    cache_file = _get_cache_dir() / f"{key}.ipynb"
    if cache_file.is_file():
        try:
            return nbformat.read(cache_file, as_version=4)
        except Exception:
            cache_file.unlink(missing_ok=True)

    notebook = jupytext.reads(inputstring, fmt=fmt)
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(notebook, cache_file)
    except Exception:
        pass
    return notebook
