import json
import subprocess
import sys
from pathlib import Path


def _git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def test_complexity_report_tracks_touched_block_deltas(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "ci@example.com")
    _git(repo, "config", "user.name", "CI User")

    path = repo / "sample.py"
    path.write_text(
        "\n".join(
            [
                "def stable(values):",
                "    return [value for value in values]",
                "",
                "def target(x):",
                "    if x:",
                "        return 1",
                "    return 0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "sample.py")
    _git(repo, "commit", "-m", "base")
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    path.write_text(
        "\n".join(
            [
                "def stable(values):",
                "    return [value for value in values]",
                "",
                "def target(x):",
                "    if x > 0:",
                "        return 1",
                "    if x < 0:",
                "        return -1",
                "    return 0",
                "",
                "def added(values):",
                "    total = 0",
                "    for value in values:",
                "        if value:",
                "            total += 1",
                "    return total",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "sample.py")
    _git(repo, "commit", "-m", "head")
    head_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    script = (
        Path(__file__).resolve().parents[2] / "tools" / "ci" / "complexity_report.py"
    )
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo),
            "--base-ref",
            base_sha,
            "--head-ref",
            head_sha,
            "--output-json",
            str(json_path),
            "--output-markdown",
            str(md_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["totals"]["files"] == 1
    assert report["totals"]["worsened_blocks"] == 1
    assert report["totals"]["added_blocks"] == 1
    assert report["totals"]["unchanged_blocks"] == 0
    assert "Complexity Report" in proc.stdout
    assert "target" in proc.stdout
    assert "added" in md_path.read_text(encoding="utf-8")

    blocks = report["files"][0]["blocks"]
    names_to_status = {block["name"]: block["status"] for block in blocks}
    assert names_to_status["target"] == "worsened"
    assert names_to_status["added"] == "added"
    assert "stable" not in names_to_status
