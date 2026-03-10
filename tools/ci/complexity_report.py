#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from radon.complexity import cc_rank, cc_visit
except Exception as exc:  # pragma: no cover - diagnostic path
    raise SystemExit(
        f"radon is required to build the complexity report: {exc}"
    ) from exc


HUNK_PATTERN = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass(frozen=True)
class BlockMetric:
    name: str
    lineno: int
    endline: int
    complexity: int
    rank: str


@dataclass(frozen=True)
class BlockDelta:
    path: str
    name: str
    status: str
    base_complexity: int | None
    head_complexity: int | None
    base_rank: str | None
    head_rank: str | None
    delta: int | None


@dataclass(frozen=True)
class FileReport:
    path: str
    status: str
    base_file_average: float | None
    head_file_average: float | None
    base_touched_average: float | None
    head_touched_average: float | None
    base_total_blocks: int
    head_total_blocks: int
    base_touched_blocks: int
    head_touched_blocks: int
    blocks: list[BlockDelta]


def _git(
    repo_root: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=check,
        capture_output=True,
        text=True,
    )


def _changed_python_files(repo_root: Path, base_ref: str, head_ref: str) -> list[str]:
    proc = _git(repo_root, "diff", "--name-only", base_ref, head_ref, "--", check=True)
    return sorted(
        path.replace("\\", "/")
        for path in proc.stdout.splitlines()
        if path.strip().endswith(".py")
    )


def _read_source(repo_root: Path, rev: str, path: str) -> str | None:
    proc = _git(repo_root, "show", f"{rev}:{path}", check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout


def _mean_complexity(blocks: dict[str, BlockMetric]) -> float | None:
    if not blocks:
        return None
    return sum(block.complexity for block in blocks.values()) / len(blocks)


def _block_name(block, parent: str | None = None) -> str:
    if parent:
        return f"{parent}.{block.name}"
    classname = getattr(block, "classname", None)
    if classname:
        return f"{classname}.{block.name}"
    return block.name


def _flatten_blocks(blocks, parent: str | None = None) -> list[BlockMetric]:
    flattened: list[BlockMetric] = []
    for block in blocks:
        name = _block_name(block, parent=parent)
        if type(block).__name__ != "Class":
            flattened.append(
                BlockMetric(
                    name=name,
                    lineno=block.lineno,
                    endline=getattr(block, "endline", block.lineno),
                    complexity=block.complexity,
                    rank=cc_rank(block.complexity),
                )
            )
        closures = getattr(block, "closures", [])
        if closures:
            flattened.extend(_flatten_blocks(closures, parent=name))
    return flattened


def _analyze_source(source: str | None) -> dict[str, BlockMetric]:
    if not source:
        return {}
    blocks = _flatten_blocks(cc_visit(source))
    return {block.name: block for block in blocks}


def _parse_changed_ranges(
    diff_text: str,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    old_ranges: list[tuple[int, int]] = []
    new_ranges: list[tuple[int, int]] = []
    for line in diff_text.splitlines():
        match = HUNK_PATTERN.match(line)
        if not match:
            continue
        old_start = int(match.group("old_start"))
        old_count = int(match.group("old_count") or "1")
        new_start = int(match.group("new_start"))
        new_count = int(match.group("new_count") or "1")
        if old_count:
            old_ranges.append((old_start, old_start + old_count - 1))
        if new_count:
            new_ranges.append((new_start, new_start + new_count - 1))
    return old_ranges, new_ranges


def _get_changed_ranges(
    repo_root: Path, base_ref: str, head_ref: str, path: str
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    proc = _git(
        repo_root,
        "diff",
        "--unified=0",
        "--no-color",
        base_ref,
        head_ref,
        "--",
        path,
        check=True,
    )
    return _parse_changed_ranges(proc.stdout)


def _intersects_ranges(block: BlockMetric, ranges: list[tuple[int, int]]) -> bool:
    for start, end in ranges:
        if block.lineno <= end and start <= block.endline:
            return True
    return False


def _filter_touched(
    blocks: dict[str, BlockMetric], ranges: list[tuple[int, int]]
) -> dict[str, BlockMetric]:
    if not ranges:
        return {}
    return {
        name: block
        for name, block in blocks.items()
        if _intersects_ranges(block, ranges)
    }


def _delta_status(
    base_block: BlockMetric | None, head_block: BlockMetric | None
) -> str:
    if base_block is None and head_block is None:  # pragma: no cover - defensive
        return "unchanged"
    if base_block is None:
        return "added"
    if head_block is None:
        return "removed"
    if head_block.complexity < base_block.complexity:
        return "improved"
    if head_block.complexity > base_block.complexity:
        return "worsened"
    return "unchanged"


def _file_status(
    base_average: float | None, head_average: float | None, blocks: list[BlockDelta]
) -> str:
    if base_average is None and head_average is None:
        if blocks:
            return blocks[0].status
        return "unchanged"
    if base_average is None:
        return "added"
    if head_average is None:
        return "removed"
    if head_average < base_average:
        return "improved"
    if head_average > base_average:
        return "worsened"
    return "unchanged"


def _build_file_report(
    repo_root: Path, base_ref: str, head_ref: str, path: str
) -> FileReport:
    base_source = _read_source(repo_root, base_ref, path)
    head_source = _read_source(repo_root, head_ref, path)
    base_blocks = _analyze_source(base_source)
    head_blocks = _analyze_source(head_source)
    old_ranges, new_ranges = _get_changed_ranges(repo_root, base_ref, head_ref, path)
    touched_base_blocks = _filter_touched(base_blocks, old_ranges)
    touched_head_blocks = _filter_touched(head_blocks, new_ranges)
    touched_names = sorted(set(touched_base_blocks) | set(touched_head_blocks))

    block_deltas: list[BlockDelta] = []
    for name in touched_names:
        base_block = touched_base_blocks.get(name)
        head_block = touched_head_blocks.get(name)
        delta = None
        if base_block is not None and head_block is not None:
            delta = head_block.complexity - base_block.complexity
        block_deltas.append(
            BlockDelta(
                path=path,
                name=name,
                status=_delta_status(base_block, head_block),
                base_complexity=base_block.complexity if base_block else None,
                head_complexity=head_block.complexity if head_block else None,
                base_rank=base_block.rank if base_block else None,
                head_rank=head_block.rank if head_block else None,
                delta=delta,
            )
        )

    base_touched_average = _mean_complexity(touched_base_blocks)
    head_touched_average = _mean_complexity(touched_head_blocks)
    return FileReport(
        path=path,
        status=_file_status(base_touched_average, head_touched_average, block_deltas),
        base_file_average=_mean_complexity(base_blocks),
        head_file_average=_mean_complexity(head_blocks),
        base_touched_average=base_touched_average,
        head_touched_average=head_touched_average,
        base_total_blocks=len(base_blocks),
        head_total_blocks=len(head_blocks),
        base_touched_blocks=len(touched_base_blocks),
        head_touched_blocks=len(touched_head_blocks),
        blocks=block_deltas,
    )


def build_report(repo_root: Path, base_ref: str, head_ref: str) -> dict[str, object]:
    file_reports = [
        _build_file_report(repo_root, base_ref, head_ref, path)
        for path in _changed_python_files(repo_root, base_ref, head_ref)
    ]
    block_deltas = [block for report in file_reports for block in report.blocks]
    totals = {
        "files": len(file_reports),
        "improved_files": sum(report.status == "improved" for report in file_reports),
        "worsened_files": sum(report.status == "worsened" for report in file_reports),
        "unchanged_files": sum(report.status == "unchanged" for report in file_reports),
        "added_files": sum(report.status == "added" for report in file_reports),
        "removed_files": sum(report.status == "removed" for report in file_reports),
        "improved_blocks": sum(block.status == "improved" for block in block_deltas),
        "worsened_blocks": sum(block.status == "worsened" for block in block_deltas),
        "unchanged_blocks": sum(block.status == "unchanged" for block in block_deltas),
        "added_blocks": sum(block.status == "added" for block in block_deltas),
        "removed_blocks": sum(block.status == "removed" for block in block_deltas),
    }
    return {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "files": [asdict(report) for report in file_reports],
        "totals": totals,
    }


def _format_score(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _format_complexity(value: int | None, rank: str | None) -> str:
    if value is None:
        return "-"
    if rank:
        return f"{value} ({rank})"
    return str(value)


def _format_delta(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value:+d}"


def _format_block_table(title: str, blocks: list[dict[str, object]]) -> list[str]:
    if not blocks:
        return []
    lines = [
        f"### {title}",
        "",
        "| File | Block | Base | Head | Delta |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for block in blocks:
        lines.append(
            "| {path} | `{name}` | {base} | {head} | {delta} |".format(
                path=block["path"],
                name=block["name"],
                base=_format_complexity(block["base_complexity"], block["base_rank"]),
                head=_format_complexity(block["head_complexity"], block["head_rank"]),
                delta=_format_delta(block["delta"]),
            )
        )
    lines.append("")
    return lines


def format_markdown(report: dict[str, object]) -> str:
    totals = report["totals"]
    files = report["files"]
    lines = [
        "## Complexity Report",
        "",
        (
            f"Compared `{report['base_ref']}` -> `{report['head_ref']}`. "
            "Lower cyclomatic complexity is better."
        ),
        "",
    ]
    if not files:
        lines.append("No changed Python files were found in this diff.")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            (
                "Touched blocks: "
                f"{totals['improved_blocks']} improved, "
                f"{totals['worsened_blocks']} worsened, "
                f"{totals['unchanged_blocks']} unchanged, "
                f"{totals['added_blocks']} added, "
                f"{totals['removed_blocks']} removed."
            ),
            (
                "Changed Python files: "
                f"{totals['files']} total, "
                f"{totals['improved_files']} improved, "
                f"{totals['worsened_files']} worsened, "
                f"{totals['unchanged_files']} unchanged, "
                f"{totals['added_files']} added, "
                f"{totals['removed_files']} removed."
            ),
            "",
            "### File Summary",
            "",
            "| File | Touched Avg Base | Touched Avg Head | Full Avg Base | Full Avg Head | Touched Blocks | Status |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for file_report in files:
        touched_total = max(
            file_report["base_touched_blocks"], file_report["head_touched_blocks"]
        )
        lines.append(
            "| {path} | {base_touched} | {head_touched} | {base_file} | {head_file} | {touched_total} | {status} |".format(
                path=file_report["path"],
                base_touched=_format_score(file_report["base_touched_average"]),
                head_touched=_format_score(file_report["head_touched_average"]),
                base_file=_format_score(file_report["base_file_average"]),
                head_file=_format_score(file_report["head_file_average"]),
                touched_total=touched_total,
                status=file_report["status"],
            )
        )
    lines.append("")

    all_blocks = [block for file_report in files for block in file_report["blocks"]]
    improved_blocks = sorted(
        (block for block in all_blocks if block["status"] == "improved"),
        key=lambda block: (block["delta"], block["path"], block["name"]),
    )[:10]
    worsened_blocks = sorted(
        (block for block in all_blocks if block["status"] == "worsened"),
        key=lambda block: (block["delta"], block["path"], block["name"]),
        reverse=True,
    )[:10]
    added_blocks = sorted(
        (block for block in all_blocks if block["status"] == "added"),
        key=lambda block: (block["path"], block["name"]),
    )[:10]
    removed_blocks = sorted(
        (block for block in all_blocks if block["status"] == "removed"),
        key=lambda block: (block["path"], block["name"]),
    )[:10]

    lines.extend(_format_block_table("Most Improved Blocks", improved_blocks))
    lines.extend(_format_block_table("Most Worsened Blocks", worsened_blocks))
    lines.extend(_format_block_table("Added Blocks", added_blocks))
    lines.extend(_format_block_table("Removed Blocks", removed_blocks))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a complexity comparison report for a git diff."
    )
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-json")
    parser.add_argument("--output-markdown")
    parser.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    report = build_report(repo_root, args.base_ref, args.head_ref)
    markdown = format_markdown(report)

    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.output_markdown:
        output_markdown = Path(args.output_markdown)
        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.write_text(markdown, encoding="utf-8")

    print(markdown, end="")
    if args.fail_on_regression and report["totals"]["worsened_blocks"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
