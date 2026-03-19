from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CITATION_CFF = ROOT / "CITATION.cff"
ZENODO_JSON = ROOT / ".zenodo.json"
README = ROOT / "README.rst"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"


def _citation_scalar(key):
    """
    Extract a quoted top-level scalar from the repository CFF metadata.
    """
    text = CITATION_CFF.read_text(encoding="utf-8")
    match = re.search(rf'^{re.escape(key)}:\s*"([^"]+)"\s*$', text, re.MULTILINE)
    assert match is not None, f"Missing {key!r} in {CITATION_CFF}"
    return match.group(1)


def _latest_release_tag():
    """
    Return the latest release tag and tag date from the local git checkout.
    """
    try:
        tag_result = subprocess.run(
            ["git", "tag", "--sort=-v:refname"],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"Could not inspect git tags: {exc}")
    tags = [tag for tag in tag_result.stdout.splitlines() if tag.startswith("v")]
    if not tags:
        pytest.skip("No release tags found in this checkout")
    tag = tags[0]
    date_result = subprocess.run(
        [
            "git",
            "for-each-ref",
            f"refs/tags/{tag}",
            "--format=%(creatordate:short)",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return tag.removeprefix("v"), date_result.stdout.strip()


def test_release_metadata_matches_latest_git_tag():
    """
    Citation metadata should track the latest tagged release.
    """
    version, release_date = _latest_release_tag()
    assert _citation_scalar("version") == version
    assert _citation_scalar("date-released") == release_date


def test_zenodo_metadata_is_valid_and_synced():
    """
    Zenodo metadata should parse as JSON and match the citation file.
    """
    metadata = json.loads(ZENODO_JSON.read_text(encoding="utf-8"))
    assert metadata["version"] == _citation_scalar("version")
    assert metadata["publication_date"] == _citation_scalar("date-released")


def test_readme_citation_section_uses_repository_metadata():
    """
    The README should point readers at the maintained citation metadata.
    """
    text = README.read_text(encoding="utf-8")
    assert "CITATION.cff" in text
    assert "@software{" not in text


def test_publish_workflow_creates_github_release_for_tags():
    """
    Release tags should create a GitHub release so Zenodo can archive it.
    """
    text = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    assert 'tags: ["v*"]' in text
    assert "softprops/action-gh-release@v2" in text
