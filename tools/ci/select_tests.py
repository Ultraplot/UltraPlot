#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from fnmatch import fnmatch
from pathlib import Path


def load_map(path: str) -> dict[str, list[str]] | None:
    map_path = Path(path)
    if not map_path.is_file():
        return None
    with map_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("files", {})


def read_changed_files(path: str) -> list[str]:
    changed_path = Path(path)
    if not changed_path.is_file():
        return []
    return [
        line.strip()
        for line in changed_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select impacted pytest nodeids from a test map."
    )
    parser.add_argument("--map", dest="map_path", required=True)
    parser.add_argument("--changed-files", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--always-full", action="append", default=[])
    parser.add_argument("--ignore", action="append", default=[])
    parser.add_argument("--source-prefix", default="ultraplot/")
    parser.add_argument("--tests-prefix", default="ultraplot/tests/")
    args = parser.parse_args()

    files_map = load_map(args.map_path)
    changed_files = read_changed_files(args.changed_files)

    result = {"mode": "full", "tests": []}
    if not files_map or not changed_files:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0

    tests = set()
    for path in changed_files:
        path = path.replace("\\", "/")
        if matches_any(path, args.ignore):
            continue
        if matches_any(path, args.always_full):
            tests.clear()
            result["mode"] = "full"
            break
        if path.startswith(args.tests_prefix):
            tests.add(path)
            continue
        if path in files_map:
            tests.update(files_map[path])
            continue
        if path.startswith(args.source_prefix):
            tests.clear()
            result["mode"] = "full"
            break

    if tests:
        # Guard against parametrized tests recorded without parameters.
        # Falling back to file-level nodeids avoids pytest "not found" errors.
        normalized = set()
        for nodeid in tests:
            if "::" in nodeid and "[" not in nodeid:
                normalized.add(nodeid.split("::", 1)[0])
            else:
                normalized.add(nodeid)
        result["mode"] = "selected"
        result["tests"] = sorted(normalized)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
