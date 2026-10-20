"""Create an artifact with only failed pytest-mpl image comparisons.

Run pytest-mpl with --mpl-generate-summary=json (not HTML). The latter
implicitly enables --mpl-results-always and saves passing test images.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

_IMAGE_FIELDS = (
    ("baseline_image", "Baseline"),
    ("result_image", "Actual"),
    ("diff_image", "Difference"),
)


def junit_failures(path: Path) -> list[str]:
    """Include non-image failures, for which pytest-mpl has no image result."""
    if not path.is_file():
        return []
    root = ET.parse(path).getroot()
    return [
        f"{case.get('classname', '')}.{case.get('name', '')}".lstrip(".")
        for case in root.iter("testcase")
        if case.find("failure") is not None or case.find("error") is not None
    ]


def collect(results_dir: Path, output_dir: Path) -> int:
    """Return the number of failed pytest-mpl comparisons copied."""
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
    test_failures = junit_failures(junit)

    # An entirely green run should not produce an artifact, even an empty zip.
    if not failed and not test_failures:
        print("No failed image comparisons or JUnit tests; no artifact to upload.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    if junit.is_file():
        shutil.copy2(junit, output_dir / "junit.xml")

    (output_dir / "results.json").write_text(
        json.dumps(failed, indent=2) + "\n", encoding="utf-8"
    )

    # Copy only failed comparisons. Linked images can be opened at full size.
    comparisons = []
    for name, item in sorted(failed.items()):
        images = []
        for field, label in _IMAGE_FIELDS:
            raw_path = item.get(field)
            if not raw_path:
                images.append(
                    f'<figure><figcaption>{html.escape(label)}</figcaption>'
                    '<p class="missing">Not available</p></figure>'
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
                f'<a href="{url}"><img loading="lazy" src="{url}" alt="{alt}"></a></figure>'
            )

        metrics = []
        for field, label in (("rms", "RMS"), ("tolerance", "Tolerance")):
            value = item.get(field)
            if value is not None:
                display = f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
                metrics.append(f"{label}: {html.escape(display)}")

        comparisons.append(
            f'<section class="comparison"><h2><code>{html.escape(name)}</code></h2>'
            f'<p class="metrics">{" · ".join(metrics) if metrics else "No numerical comparison available"}</p>'
            f'<div class="images">{"".join(images)}</div>'
            f'<details><summary>Error details</summary>'
            f'<pre>{html.escape(str(item.get("status_msg") or "No diagnostic text provided."))}</pre>'
            f'</details></section>'
        )

    # JUnit includes failures not covered by pytest-mpl (which have no images).
    junit_list = "".join(f"<li><code>{html.escape(name)}</code></li>" for name in test_failures)
    junit_details = (
        '<details class="junit"><summary>All JUnit failures / errors '
        f'({len(test_failures)})</summary><ul>{junit_list}</ul></details>'
        if test_failures else ""
    )
    template = Path(__file__).with_name("failed_comparisons_template.html").read_text(
        encoding="utf-8"
    )
    markup = template
    for marker, value in {
        "__ULTRAPLOT_IMAGE_COUNT__": str(len(failed)),
        "__ULTRAPLOT_JUNIT_COUNT__": str(len(test_failures)),
        "__ULTRAPLOT_CARDS__": "\n".join(comparisons),
        "__ULTRAPLOT_JUNIT_DETAILS__": junit_details,
        "__ULTRAPLOT_JUNIT_DOWNLOAD__": (
            ' · <a href="junit.xml">junit.xml</a>'
            if junit.is_file() else ""
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
