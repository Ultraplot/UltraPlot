from __future__ import annotations

import importlib.util
import re
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CITATION_CFF = ROOT / "CITATION.cff"
README = ROOT / "README.rst"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"
PYPROJECT = ROOT / "pyproject.toml"
ZENODO_SCRIPT = ROOT / "tools" / "release" / "publish_zenodo.py"


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


def _load_publish_zenodo():
    """
    Import the Zenodo release helper directly from the repo checkout.
    """
    spec = importlib.util.spec_from_file_location("publish_zenodo", ZENODO_SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load publish_zenodo from {ZENODO_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_metadata_matches_latest_git_tag():
    """
    Citation metadata should track the latest tagged release.
    """
    version, release_date = _latest_release_tag()
    assert _citation_scalar("version") == version
    assert _citation_scalar("date-released") == release_date


def test_zenodo_release_metadata_is_built_from_repository_sources():
    """
    Zenodo metadata should be derived from the maintained repository metadata.
    """
    publish_zenodo = _load_publish_zenodo()
    citation = yaml.safe_load(CITATION_CFF.read_text(encoding="utf-8"))
    with PYPROJECT.open("rb") as handle:
        pyproject = tomllib.load(handle)
    metadata = publish_zenodo.build_metadata(citation, pyproject)
    assert metadata["title"] == citation["title"]
    assert metadata["upload_type"] == "software"
    assert metadata["version"] == _citation_scalar("version")
    assert metadata["publication_date"] == _citation_scalar("date-released")
    assert metadata["creators"][0]["name"] == "van Elteren, Casper"
    assert metadata["creators"][0]["orcid"] == "0000-0001-9862-8936"


def test_zenodo_json_is_not_committed():
    """
    Zenodo metadata should no longer be duplicated in a separate committed file.
    """
    assert not (ROOT / ".zenodo.json").exists()


def test_readme_citation_section_uses_repository_metadata():
    """
    The README should point readers at the maintained citation metadata.
    """
    text = README.read_text(encoding="utf-8")
    assert "CITATION.cff" in text
    assert "@software{" not in text


def test_publish_workflow_creates_github_release_and_pushes_to_zenodo():
    """
    Release tags should create a GitHub release and publish the same dist to Zenodo.
    """
    text = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    assert 'tags: ["v*"]' in text
    assert "softprops/action-gh-release@v2" in text
    assert "publish-zenodo:" in text
    assert "ZENODO_ACCESS_TOKEN" in text
    assert "tools/release/publish_zenodo.py --dist-dir dist" in text
