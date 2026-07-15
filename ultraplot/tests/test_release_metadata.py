from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CITATION_CFF = ROOT / "CITATION.cff"
README = ROOT / "README.rst"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"

# Concept DOI: stable across releases, always resolves to the newest version.
CONCEPT_DOI = "10.5281/zenodo.15733564"


def _citation():
    return yaml.safe_load(CITATION_CFF.read_text(encoding="utf-8"))


def test_citation_pins_the_concept_doi():
    """
    Citing the concept DOI keeps every release under one record. A versioned DOI
    here would pin readers to whichever release happened to be current.
    """
    assert _citation()["doi"] == CONCEPT_DOI


def test_citation_does_not_pin_a_version():
    """
    The git tag is the single source of truth for the version: setuptools_scm
    derives the package version from it and Zenodo takes the archive version from
    the release. Restating it here means editing this file on every release, which
    is exactly how it silently drifted to 2.1.5 while the project shipped 2.4.0.
    """
    citation = _citation()
    assert "version" not in citation
    assert "date-released" not in citation


def test_zenodo_json_is_the_metadata_zenodo_reads():
    """
    Zenodo reads .zenodo.json in preference to CITATION.cff and ignores the CFF
    entirely when one exists. We ship it because the CFF -> Zenodo conversion is
    lossy: CFF must spell the license with its SPDX id ("MIT"), while Zenodo's
    vocabulary only knows the lowercase "mit", and a CFF-derived deposit carried a
    'doi' and a hand-pinned 'version' that Zenodo should be deciding itself.
    Releases stopped archiving the day CITATION.cff landed; this file is the
    controlled surface that removes the guesswork.
    """
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))

    # Zenodo mints the DOI and takes the version from the release tag. Pinning
    # either here is what we are getting away from.
    assert "doi" not in zenodo
    assert "version" not in zenodo

    # Must match Zenodo's license vocabulary, which is lowercase (GET
    # /api/vocabularies/licenses/mit -> 200, .../MIT -> 404).
    assert zenodo["license"] == zenodo["license"].lower()
    assert zenodo["upload_type"] == "software"
    assert zenodo["creators"][0]["orcid"] == "0000-0001-9862-8936"


def test_readme_citation_section_uses_repository_metadata():
    """The README should point readers at the maintained citation metadata."""
    text = README.read_text(encoding="utf-8")
    assert "CITATION.cff" in text
    assert "@software{" not in text


def test_publish_workflow_creates_github_release_on_tags():
    """
    Publishing the GitHub release is what triggers the Zenodo archive, via
    Zenodo's own webhook. If this step goes away, Zenodo silently stops updating.
    """
    text = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    assert 'tags: ["v*"]' in text
    assert "softprops/action-gh-release@" in text


def test_publish_workflow_has_no_zenodo_api_job():
    """
    Zenodo is synced by its GitHub integration, not by us. A second, API-based
    path would race the webhook and mint duplicate versions under the concept DOI.

    NOTE: Match on uncommented lines only -- the previous job sat commented out in
    this workflow for months, and a test asserting on the raw text passed against
    dead YAML the whole time.
    """
    live = [
        line
        for line in PUBLISH_WORKFLOW.read_text(encoding="utf-8").splitlines()
        if not re.match(r"^\s*#", line)
    ]
    text = "\n".join(live).lower()
    assert "zenodo_access_token" not in text
    assert "publish_zenodo" not in text
    assert "sync_citation" not in text


def test_zenodo_release_tooling_is_gone():
    """The API-based release scripts are removed; nothing should resurrect them."""
    assert not (ROOT / "tools" / "release" / "publish_zenodo.py").exists()
    assert not (ROOT / "tools" / "release" / "sync_citation.py").exists()
