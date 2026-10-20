"""Collect failed pytest-mpl comparisons into a small HTML artifact.

Use --mpl-generate-summary=json, not HTML, when running pytest-mpl. Its HTML
option implicitly enables --mpl-results-always and saves passing images.
"""

from __future__ import annotations

import argparse
import html
import json
import platform
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import quote

_IMAGE_FIELDS = (
    ("baseline_image", "Baseline"),
    ("result_image", "Actual"),
    ("diff_image", "Difference"),
)


def junit_report(path: Path) -> tuple[dict[str, int] | None, list[str]]:
    """Return counts for the whole pytest run, excluding skipped tests."""
    if not path.is_file():
        return None, []

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        # A cancelled test run might leave a truncated JUnit XML file.
        return None, []

    counts = {"passed": 0, "failed": 0, "errors": 0}
    failures = []
    for case in root.iter("testcase"):
        if case.find("error") is not None:
            status = "errors"
        elif case.find("failure") is not None:
            status = "failed"
        elif case.find("skipped") is not None:
            continue
        else:
            status = "passed"
        counts[status] += 1
        if status != "passed":
            failures.append(
                f"{case.get('classname', '')}.{case.get('name', '')}".lstrip(".")
            )
    return counts, failures


def collect(results_dir: Path, output_dir: Path) -> int:
    """Copy failed image comparisons and return their count."""
    results_dir = results_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir == results_dir or results_dir in output_dir.parents:
        raise ValueError("Artifact output must not be inside the pytest-mpl results directory")

    summary = results_dir / "results.json"
    results = json.loads(summary.read_text(encoding="utf-8")) if summary.is_file() else {}
    if not isinstance(results, dict):
        raise ValueError("Unexpected pytest-mpl JSON summary format")

    failed = {name: item for name, item in results.items() if item.get("status") == "failed"}
    junit = results_dir / "junit.xml"
    counts, junit_failures = junit_report(junit)

    if not failed and not junit_failures:
        print("No failed tests; no artifact to upload.")
        return 0

    if counts is None:
        # The fallback covers image tests only; full-suite counts require JUnit.
        counts = {
            "passed": sum(item.get("status") == "passed" for item in results.values()),
            "failed": len(failed),
            "errors": 0,
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    if junit.is_file():
        shutil.copy2(junit, output_dir / "junit.xml")
    (output_dir / "results.json").write_text(
        json.dumps(failed, indent=2) + "\n", encoding="utf-8"
    )

    rows = []
    for index, (name, item) in enumerate(sorted(failed.items())):
        images = []
        for field, label in _IMAGE_FIELDS:
            raw_path = item.get(field)
            if not raw_path:
                images.append(
                    f'<figure><figcaption>{html.escape(label)}</figcaption>'
                    '<span class="missing">Not available</span></figure>'
                )
                continue

            relative_path = Path(raw_path)
            source = (results_dir / relative_path).resolve()
            if not source.is_relative_to(results_dir) or not source.is_file():
                raise ValueError(f"Unexpected {field} path in pytest-mpl results: {raw_path}")
            destination = output_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

            url = html.escape(quote(relative_path.as_posix(), safe="/"), quote=True)
            alt = html.escape(f"{label} image for {name}", quote=True)
            images.append(
                f'<figure><figcaption>{html.escape(label)}</figcaption>'
                f'<a href="{url}" title="View full image">'
                f'<img loading="lazy" src="{url}" alt="{alt}"></a></figure>'
            )

        def numeric(field: str) -> str:
            value = item.get(field)
            if value is None:
                return "—"
            return html.escape(f"{value:.5g}" if isinstance(value, (int, float)) else str(value))

        test_name = html.escape(name)
        status_text = html.escape(str(item.get("image_status") or "Failed").capitalize())
        diagnostic = html.escape(str(item.get("status_msg") or "No diagnostic text provided."))
        expanded = " open" if index == 0 else ""
        rows.extend([
            '<tr class="comparison-row">'
            f'<td><span class="test-name">{test_name}</span></td>'
            f'<td><span class="status">{status_text}</span></td>'
            f'<td class="numeric">{numeric("rms")}</td>'
            f'<td class="numeric">{numeric("tolerance")}</td>'
            f'<td><div class="image-strip">{"".join(images)}</div></td></tr>',
            f'<tr class="detail-row"><td colspan="5"><details{expanded}>'
            f'<summary>Test output</summary><pre>{diagnostic}</pre>'
            '</details></td></tr>',
        ])

    if not rows:
        rows.append(
            '<tr><td colspan="5" class="no-images">'
            'No failed image comparisons; see JUnit failures below.</td></tr>'
        )

    junit_list = "".join(
        f"<li><code>{html.escape(name)}</code></li>" for name in junit_failures
    )
    junit_details = (
        '<details class="junit"><summary>JUnit failures / errors '
        f'({len(junit_failures)})</summary><ul>{junit_list}</ul></details>'
        if junit_failures else ""
    )

    try:
        matplotlib_version = version("matplotlib")
    except PackageNotFoundError:
        matplotlib_version = "unknown"

    template = Path(__file__).with_name("failed_comparisons_template.html").read_text(
        encoding="utf-8"
    )
    markup = template
    for marker, value in {
        "__ULTRAPLOT_PASSED__": str(counts["passed"]),
        "__ULTRAPLOT_FAILED__": str(counts["failed"]),
        "__ULTRAPLOT_ERRORS__": str(counts["errors"]),
        "__ULTRAPLOT_IMAGE_COUNT__": str(len(failed)),
        "__ULTRAPLOT_GENERATED__": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "__ULTRAPLOT_ENVIRONMENT__": html.escape(
            f"Python {platform.python_version()} · Matplotlib {matplotlib_version}"
        ),
        "__ULTRAPLOT_ROWS__": "\n".join(rows),
        "__ULTRAPLOT_JUNIT_DETAILS__": junit_details,
        "__ULTRAPLOT_JUNIT_DOWNLOAD__": (
            ' · <a href="junit.xml">JUnit XML</a>' if junit.is_file() else ""
        ),
    }.items():
        markup = markup.replace(marker, value)

    (output_dir / "index.html").write_text(markup, encoding="utf-8")
    print(f"Prepared {len(failed)} failed image comparisons in {output_dir}")
    return len(failed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("failed-comparisons"))
    args = parser.parse_args()
    collect(args.results, args.output)


if __name__ == "__main__":
    main()
