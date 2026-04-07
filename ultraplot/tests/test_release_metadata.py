from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CITATION_CFF = ROOT / "CITATION.cff"
README = ROOT / "README.rst"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"
PYPROJECT = ROOT / "pyproject.toml"
SYNC_CITATION_SCRIPT = ROOT / "tools" / "release" / "sync_citation.py"
ZENODO_SCRIPT = ROOT / "tools" / "release" / "publish_zenodo.py"


def _citation_scalar(key):
    """
    Extract a quoted top-level scalar from the repository CFF metadata.
    """
    text = CITATION_CFF.read_text(encoding="utf-8")
    match = re.search(rf'^{re.escape(key)}:\s*"([^"]+)"\s*$', text, re.MULTILINE)
    assert match is not None, f"Missing {key!r} in {CITATION_CFF}"
    return match.group(1)


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


def _load_sync_citation():
    """
    Import the citation sync helper directly from the repo checkout.
    """
    spec = importlib.util.spec_from_file_location("sync_citation", SYNC_CITATION_SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load sync_citation from {SYNC_CITATION_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sync_citation_updates_release_metadata(tmp_path):
    """
    Release automation should be able to sync CITATION.cff from a tag.
    """
    sync_citation = _load_sync_citation()
    citation = tmp_path / "CITATION.cff"
    citation.write_text(CITATION_CFF.read_text(encoding="utf-8"), encoding="utf-8")

    changed = sync_citation.sync_citation(
        citation,
        tag="v9.9.9",
        release_date="2030-01-02",
        repo_root=ROOT,
    )

    text = citation.read_text(encoding="utf-8")
    assert changed is True
    assert 'version: "9.9.9"' in text
    assert 'date-released: "2030-01-02"' in text


def test_zenodo_release_metadata_is_built_from_repository_sources():
    """
    Zenodo metadata should be derived from the maintained repository metadata.
    """
    publish_zenodo = _load_publish_zenodo()
    citation = yaml.safe_load(CITATION_CFF.read_text(encoding="utf-8"))
    pyproject = publish_zenodo.load_pyproject(PYPROJECT)
    metadata = publish_zenodo.build_metadata(citation, pyproject)
    assert metadata["title"] == citation["title"]
    assert metadata["upload_type"] == "software"
    assert metadata["version"] == _citation_scalar("version")
    assert metadata["publication_date"] == _citation_scalar("date-released")
    assert metadata["creators"][0]["name"] == "van Elteren, Casper"
    assert metadata["creators"][0]["orcid"] == "0000-0001-9862-8936"


def test_zenodo_uploads_use_octet_stream(tmp_path, monkeypatch):
    """
    Zenodo bucket uploads should use a generic binary content type.
    """
    publish_zenodo = _load_publish_zenodo()
    calls = []

    def fake_api_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return None

    monkeypatch.setattr(publish_zenodo, "api_request", fake_api_request)
    (tmp_path / "ultraplot-2.1.5.tar.gz").write_bytes(b"sdist")
    (tmp_path / "ultraplot-2.1.5-py3-none-any.whl").write_bytes(b"wheel")

    publish_zenodo.upload_dist_files(
        {"id": 18492463, "links": {"bucket": "https://zenodo.example/files/bucket"}},
        "token",
        tmp_path,
    )

    assert len(calls) == 2
    assert all(method == "PUT" for method, _, _ in calls)
    assert all(
        kwargs["content_type"] == "application/octet-stream" for _, _, kwargs in calls
    )


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
    Release tags should sync citation metadata, create a GitHub release, and
    publish the same dist to Zenodo.
    """
    text = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    assert 'tags: ["v*"]' in text
    assert text.count("tools/release/sync_citation.py --tag") >= 2
    assert "softprops/action-gh-release@v2" in text
    assert "publish-zenodo:" in text
    assert "ZENODO_ACCESS_TOKEN" in text
    assert "tools/release/publish_zenodo.py --dist-dir dist" in text
