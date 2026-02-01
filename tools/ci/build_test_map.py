#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def build_map(coverage_file: str, repo_root: str) -> dict[str, list[str]]:
    try:
        from coverage import Coverage
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            f"coverage.py is required to build the test map: {exc}"
        ) from exc

    cov = Coverage(data_file=coverage_file)
    cov.load()
    data = cov.get_data()

    files_map: dict[str, set[str]] = {}
    for filename in data.measured_files():
        if not filename:
            continue
        rel = os.path.relpath(filename, repo_root)
        if rel.startswith(".."):
            continue
        try:
            contexts_by_line = data.contexts_by_lineno(filename)
        except Exception:
            continue

        contexts = set()
        for ctxs in contexts_by_line.values():
            if not ctxs:
                continue
            for ctx in ctxs:
                if not ctx:
                    continue
                # Pytest-cov can append "|run"/"|setup"/"|teardown" to nodeids.
                # Strip phase suffixes so selection uses valid nodeids.
                contexts.add(ctx.split("|", 1)[0])
        if contexts:
            files_map[rel] = contexts

    return {path: sorted(contexts) for path, contexts in files_map.items()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a test impact map from coverage contexts."
    )
    parser.add_argument("--coverage-file", default=".coverage")
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.root)
    mapping = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": build_map(args.coverage_file, repo_root),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
