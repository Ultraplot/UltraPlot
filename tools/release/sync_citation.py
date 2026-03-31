#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync CITATION.cff release metadata from a git tag."
    )
    parser.add_argument(
        "--tag",
        required=True,
        help="Release tag to sync from, for example v2.1.5 or refs/tags/v2.1.5.",
    )
    parser.add_argument(
        "--citation",
        type=Path,
        default=Path("CITATION.cff"),
        help="Path to the repository CITATION.cff file.",
    )
    parser.add_argument(
        "--date",
        help="Explicit release date in YYYY-MM-DD format. Defaults to the git tag date.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the file contents instead of writing them.",
    )
    return parser.parse_args()


def normalize_tag(tag: str) -> str:
    return tag.strip().removeprefix("refs/tags/")


def tag_version(tag: str) -> str:
    tag = normalize_tag(tag)
    if not tag.startswith("v"):
        raise ValueError(f"Release tag must start with 'v', got {tag!r}.")
    return tag.removeprefix("v")


def resolve_release_date(tag: str, repo_root: Path) -> str:
    result = subprocess.run(
        [
            "git",
            "for-each-ref",
            f"refs/tags/{normalize_tag(tag)}",
            "--format=%(creatordate:short)",
        ],
        check=True,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if not value:
        raise ValueError(f"Could not resolve a release date for tag {tag!r}.")
    return value


def replace_scalar(text: str, key: str, value: str) -> str:
    pattern = rf'^(?P<prefix>{re.escape(key)}:\s*)"[^"]*"\s*$'
    updated, count = re.subn(
        pattern,
        rf'\g<prefix>"{value}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise ValueError(f"Missing quoted scalar {key!r} in CITATION metadata.")
    return updated


def sync_citation(
    citation_path: Path,
    *,
    tag: str,
    release_date: str | None = None,
    repo_root: Path | None = None,
    check: bool = False,
) -> bool:
    repo_root = repo_root or citation_path.resolve().parent
    version = tag_version(tag)
    release_date = release_date or resolve_release_date(tag, repo_root)
    original = citation_path.read_text(encoding="utf-8")
    updated = replace_scalar(original, "version", version)
    updated = replace_scalar(updated, "date-released", release_date)
    changed = updated != original
    if check:
        if changed:
            raise SystemExit(
                f"{citation_path} is out of date for {normalize_tag(tag)}. "
                "Run tools/release/sync_citation.py before releasing."
            )
        return False
    citation_path.write_text(updated, encoding="utf-8")
    return changed


def main() -> int:
    args = parse_args()
    changed = sync_citation(
        args.citation,
        tag=args.tag,
        release_date=args.date,
        repo_root=Path.cwd(),
        check=args.check,
    )
    action = "Validated" if args.check else "Updated"
    print(f"{action} {args.citation} for {normalize_tag(args.tag)}.")
    return 0 if (args.check or changed or not changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
