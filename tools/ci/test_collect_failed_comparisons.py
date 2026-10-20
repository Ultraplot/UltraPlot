"""Unit tests for the CI's failure-only image artifact collector."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from collect_failed_comparisons import collect


class TestFailureArtifacts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.results = self.root / "results"
        self.results.mkdir()
        self.output = self.root / "artifacts"

    def test_passing_run_creates_no_artifact(self) -> None:
        (self.results / "results.json").write_text(
            json.dumps({"test_ok": {"status": "passed"}}), encoding="utf-8"
        )
        (self.results / "junit.xml").write_text(
            '<testsuite><testcase name="test_ok"/></testsuite>', encoding="utf-8"
        )

        self.assertEqual(collect(self.results, self.output), 0)
        self.assertFalse(self.output.exists())

    def test_failed_images_are_selected_and_linked(self) -> None:
        failed = "module.test_failed"
        for filename in ("baseline.png", "result.png", "result-failed-diff.png"):
            target = self.results / failed / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"image data")

        (self.results / "results.json").write_text(
            json.dumps({
                "module.test_passed": {"status": "passed", "result_image": "passed/result.png"},
                failed: {
                    "status": "failed",
                    "status_msg": "Image mismatch",
                    "baseline_image": f"{failed}/baseline.png",
                    "result_image": f"{failed}/result.png",
                    "diff_image": f"{failed}/result-failed-diff.png",
                },
            }),
            encoding="utf-8",
        )
        (self.results / "junit.xml").write_text(
            '<testsuite><testcase classname="module" name="test_failed"><failure/></testcase></testsuite>',
            encoding="utf-8",
        )

        self.assertEqual(collect(self.results, self.output), 1)
        self.assertFalse((self.output / "passed").exists())
        self.assertEqual(set(json.loads((self.output / "results.json").read_text())), {failed})
        for filename in ("baseline.png", "result.png", "result-failed-diff.png"):
            self.assertTrue((self.output / failed / filename).is_file())
            self.assertIn(filename, (self.output / "index.html").read_text())
        report = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn("<h1>UltraPlot Image comparison</h1>", report)
        self.assertIn("1 failed image comparisons; 1 JUnit failures/errors.", report)
        self.assertIn("<figcaption>Baseline</figcaption>", report)
        self.assertIn("<figcaption>Actual</figcaption>", report)
        self.assertIn("<figcaption>Difference</figcaption>", report)
        self.assertNotIn('id="search"', report)
        self.assertNotIn('id="lightbox"', report)
        self.assertIn("Image mismatch", report)
        self.assertIn('href="results.json"', report)
        self.assertNotIn("module.test_passed", report)
        self.assertNotIn("__ULTRAPLOT_", report)

    def test_html_escapes_untrusted_test_names(self) -> None:
        failed = '<script>alert("bad")</script>'
        (self.results / "results.json").write_text(
            json.dumps({
                failed: {
                    "status": "failed",
                    "status_msg": '<img src=x onerror="alert(1)">',
                }
            }),
            encoding="utf-8",
        )

        self.assertEqual(collect(self.results, self.output), 1)
        markup = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertNotIn(failed, markup)
        self.assertNotIn('<img src=x onerror="alert(1)">', markup)
        self.assertIn("&lt;script&gt;", markup)
        self.assertIn("&lt;img src=x", markup)

    def test_non_image_junit_failure_keeps_diagnostics(self) -> None:
        (self.results / "junit.xml").write_text(
            '<testsuite><testcase classname="module" name="test_crash"><error/></testcase></testsuite>',
            encoding="utf-8",
        )
        self.assertEqual(collect(self.results, self.output), 0)
        self.assertTrue((self.output / "junit.xml").is_file())
        self.assertIn("module.test_crash", (self.output / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
