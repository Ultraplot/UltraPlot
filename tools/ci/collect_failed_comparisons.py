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

    cards = []
    for name, item in failed.items():
        images = []
        for field, label in _IMAGE_FIELDS:
            raw_path = item.get(field)
            if not raw_path:
                continue
            relative_path = Path(raw_path)
            source = (results_dir / relative_path).resolve()
            if not source.is_relative_to(results_dir) or not source.is_file():
                raise ValueError(f"Unexpected {field} path in pytest-mpl results: {raw_path}")
            destination = output_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            url = html.escape(quote(relative_path.as_posix(), safe="/"), quote=True)
            images.append(
                f'<figure><img loading="lazy" src="{url}" alt="{html.escape(label)}">'
                f'<figcaption>{html.escape(label)}</figcaption></figure>'
            )
        rms = item.get("rms")
        tolerance = item.get("tolerance")
        metrics = f"RMS: {rms}; tolerance: {tolerance}" if rms is not None else ""
        cards.append(
            f'<section><h2>{html.escape(name)}</h2><p>{html.escape(metrics)}</p>'
            f'<div class="images">{"".join(images)}</div>'
            f'<pre>{html.escape(item.get("status_msg") or "")}</pre></section>'
        )

    # Test errors unrelated to MPL may not produce an image; retain their names
    # and the complete JUnit diagnostics rather than silently hiding them.
    junit_list = "".join(f"<li>{html.escape(name)}</li>" for name in test_failures)
    markup = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Failed UltraPlot image comparisons</title>
<style>
body{{max-width:1200px;margin:2rem auto;padding:0 1rem;font-family:system-ui,sans-serif;color:#222}}
section{{border-top:1px solid #ccc;margin:2rem 0;padding-top:1rem}}
h2{{overflow-wrap:anywhere;font-size:1.15rem}}
.images{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}
figure{{margin:0}}img{{width:100%;height:auto;border:1px solid #ddd}}
figcaption{{font-weight:600;margin:.5rem 0}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5f5;padding:1rem}}
</style></head><body><h1>Failed UltraPlot image comparisons</h1>
<p>{len(failed)} image comparisons failed; {len(test_failures)} JUnit failures/errors.
See <a href="results.json">results.json</a> and <a href="junit.xml">junit.xml</a> for diagnostics.</p>
<details><summary>Failed JUnit test names</summary><ul>{junit_list}</ul></details>
{"".join(cards)}</body></html>
"""
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
