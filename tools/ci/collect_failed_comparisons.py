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

    # The report is static and intentionally self-contained: it also works
    # directly from an extracted GitHub Actions artifact without a web server.
    cards = []
    retained_images = 0
    for name, item in sorted(
        failed.items(),
        key=lambda entry: (
            -(float(entry[1]["rms"]) if entry[1].get("rms") is not None else -1),
            entry[0],
        ),
    ):
        images = []
        for field, label in _IMAGE_FIELDS:
            raw_path = item.get(field)
            if not raw_path:
                images.append(
                    f'<figure class="image-panel">'
                    f'<figcaption>{html.escape(label)}<span>Not available</span></figcaption>'
                    f'<div class="image-frame missing">No image</div></figure>'
                )
                continue
            relative_path = Path(raw_path)
            source = (results_dir / relative_path).resolve()
            if not source.is_relative_to(results_dir) or not source.is_file():
                raise ValueError(f"Unexpected {field} path in pytest-mpl results: {raw_path}")
            destination = output_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            retained_images += 1
            url = html.escape(quote(relative_path.as_posix(), safe="/"), quote=True)
            escaped_label = html.escape(label, quote=True)
            images.append(
                f'<figure class="image-panel"><figcaption>{escaped_label}'
                f'<span>Click to enlarge ↗</span></figcaption>'
                f'<a class="image-frame" href="{url}" data-label="{escaped_label}"'
                f' aria-label="Enlarge {escaped_label} image for {html.escape(name, quote=True)}">'
                f'<img loading="lazy" src="{url}" alt="{escaped_label} image for '
                f'{html.escape(name, quote=True)}"></a></figure>'
            )

        metrics = []
        for field, label in (("rms", "RMS difference"), ("tolerance", "Tolerance")):
            value = item.get(field)
            if value is not None:
                display = f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
                metrics.append(
                    f'<span class="metric"><span class="metric-label">{label}</span>'
                    f'<span class="metric-value">{html.escape(display)}</span></span>'
                )
        if not metrics:
            metrics.append('<span class="metric">No numerical comparison available</span>')
        comparison_status = str(item.get("image_status") or "failed").upper()
        cards.append(
            f'<article class="comparison" data-test="{html.escape(name, quote=True)}">'
            f'<div class="card-head"><div class="card-top"><div>'
            f'<p class="test-caption">FAILING TEST</p><h3 class="test-name">{html.escape(name)}</h3>'
            f'</div><span class="pill">{html.escape(comparison_status)}</span></div>'
            f'<div class="metrics">{"".join(metrics)}</div></div>'
            f'<div class="image-grid">{"".join(images)}</div>'
            f'<details class="details"><summary>Diagnostic output</summary>'
            f'<pre>{html.escape(str(item.get("status_msg") or "No diagnostic text provided."))}</pre>'
            f'</details></article>'
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
        "__ULTRAPLOT_RETAINED_COUNT__": str(retained_images),
        "__ULTRAPLOT_CARDS__": "\n".join(cards),
        "__ULTRAPLOT_JUNIT_DETAILS__": junit_details,
        "__ULTRAPLOT_JUNIT_DOWNLOAD__": (
            '<a class="download" href="junit.xml" download>↓ JUnit XML</a>'
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
