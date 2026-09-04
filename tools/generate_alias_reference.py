#!/usr/bin/env python3
"""Generate or verify the compatibility-alias reference table."""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ultraplot.internals.kwargs import (  # noqa: E402
    _alias_registry,
    _format_alias_reference,
)


OUTPUT = ROOT / "docs" / "aliases.rst"
SCRIPT = ROOT / "docs" / "_static" / "alias-explorer-v3.js"
START = ".. alias-table-start"
END = ".. alias-table-end"


def _validate_visual_contexts(source):
    """Ensure every registry context is reachable from the visual explorer."""
    values = re.findall(r'data-contexts="([^"]+)"', source)
    patterns = {
        pattern.strip()
        for value in values
        for pattern in value.split(",")
        if pattern.strip()
    }
    expected = {*_alias_registry, "rc (dotless)"}

    def covered(context):
        return context in patterns or any(
            pattern.endswith(".*") and context.startswith(pattern[:-1])
            for pattern in patterns
        )

    missing = sorted(context for context in expected if not covered(context))
    if missing:
        raise RuntimeError(
            "Visual alias explorer is missing contexts: " + ", ".join(missing)
        )


def _validate_api_targets():
    """Ensure every alias row can link to a canonical public API entry."""
    source = SCRIPT.read_text()
    _, marker, rest = source.partition("const apiTargets = {")
    if not marker:
        raise RuntimeError(f"Missing apiTargets mapping in {SCRIPT}.")
    mapping, marker, _ = rest.partition("\n  };")
    if not marker:
        raise RuntimeError(f"Could not parse apiTargets mapping in {SCRIPT}.")
    matches = re.findall(
        r'^\s*(?:"([^"]+)"|([A-Za-z][\w]*)):\s*"', mapping, re.MULTILINE
    )
    contexts = {quoted or bare for quoted, bare in matches}
    expected = {*_alias_registry, "rc (dotless)"}
    missing = sorted(expected - contexts)
    if missing:
        raise RuntimeError(
            "Alias API link mapping is missing contexts: " + ", ".join(missing)
        )


def _render(source):
    before, marker, rest = source.partition(START)
    if not marker:
        raise RuntimeError(f"Missing {START!r} marker in {OUTPUT}.")
    _, marker, after = rest.partition(END)
    if not marker:
        raise RuntimeError(f"Missing {END!r} marker in {OUTPUT}.")
    table = _format_alias_reference()
    return f"{before}{START}\n\n{table}\n\n{END}{after}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = OUTPUT.read_text()
    _validate_visual_contexts(source)
    _validate_api_targets()
    rendered = _render(source)
    if args.check:
        if source != rendered:
            raise SystemExit("Alias reference is stale; regenerate it.")
    else:
        OUTPUT.write_text(rendered)


if __name__ == "__main__":
    main()
