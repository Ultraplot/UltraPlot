#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib import error, parse, request

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised in release workflow
    raise SystemExit(
        "PyYAML is required to publish Zenodo releases. Install it before "
        "running tools/release/publish_zenodo.py."
    ) from exc


DEFAULT_API_URL = "https://zenodo.org/api"
DOI_PREFIX = "10.5281/zenodo."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish the current UltraPlot release artifacts to Zenodo."
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Directory containing the built release artifacts.",
    )
    parser.add_argument(
        "--citation",
        type=Path,
        default=Path("CITATION.cff"),
        help="Path to the repository CITATION.cff file.",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to the repository pyproject.toml file.",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("ZENODO_API_URL", DEFAULT_API_URL),
        help="Zenodo API base URL.",
    )
    parser.add_argument(
        "--access-token",
        default=os.environ.get("ZENODO_ACCESS_TOKEN"),
        help="Zenodo personal access token.",
    )
    return parser.parse_args()


def load_citation(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse to a mapping")
    return data


def load_pyproject(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def author_to_creator(author: dict) -> dict:
    family = author["family-names"].strip()
    given = author["given-names"].strip()
    creator = {"name": f"{family}, {given}"}
    orcid = author.get("orcid")
    if orcid:
        creator["orcid"] = normalize_orcid(orcid)
    return creator


def normalize_orcid(orcid: str) -> str:
    return orcid.removeprefix("https://orcid.org/").rstrip("/")


def build_related_identifiers(citation: dict) -> list[dict]:
    related = []
    repository = citation.get("repository-code", "").rstrip("/")
    version = citation["version"]
    if repository:
        related.append(
            {
                "relation": "isSupplementTo",
                "identifier": f"{repository}/tree/v{version}",
                "scheme": "url",
                "resource_type": "software",
            }
        )
    for reference in citation.get("references", []):
        url = reference.get("url")
        if not url:
            continue
        related.append(
            {
                "relation": "isDerivedFrom",
                "identifier": url,
                "scheme": "url",
            }
        )
    return related


def build_metadata(citation: dict, pyproject: dict) -> dict:
    project = pyproject["project"]
    creators = [author_to_creator(author) for author in citation["authors"]]
    description = project["description"].strip()
    repository = citation.get("repository-code")
    if repository:
        description = f"{description}\n\nSource code: {repository}"
    metadata = {
        "title": citation["title"],
        "upload_type": "software",
        "description": description,
        "creators": creators,
        "access_right": "open",
        "license": citation.get("license"),
        "keywords": citation.get("keywords", []),
        "version": citation["version"],
        "publication_date": citation["date-released"],
    }
    related = build_related_identifiers(citation)
    if related:
        metadata["related_identifiers"] = related
    return metadata


def doi_record_id(doi: str) -> str:
    value = doi.removeprefix("https://doi.org/").strip()
    if not value.startswith(DOI_PREFIX):
        raise ValueError(
            f"Unsupported Zenodo DOI {doi!r}. Expected prefix {DOI_PREFIX!r}."
        )
    return value.removeprefix(DOI_PREFIX)


def api_request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    json_data: dict | None = None,
    data: bytes | None = None,
    content_type: str | None = None,
    expect_json: bool = True,
):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = data
    if json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif content_type:
        headers["Content-Type"] = content_type
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req) as response:
            payload = response.read()
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {details}") from exc
    if not expect_json:
        return None
    if not payload:
        return None
    return json.loads(payload)


def resolve_concept_recid(api_url: str, doi: str) -> str:
    recid = doi_record_id(doi)
    record = api_request("GET", f"{api_url}/records/{recid}")
    return str(record.get("conceptrecid") or record.get("id") or recid)


def latest_record_id(api_url: str, conceptrecid: str) -> int:
    query = parse.urlencode(
        {
            "q": f"conceptrecid:{conceptrecid}",
            "all_versions": 1,
            "sort": "mostrecent",
            "size": 1,
        }
    )
    payload = api_request("GET", f"{api_url}/records?{query}")
    hits = payload.get("hits", {}).get("hits", [])
    if not hits:
        raise RuntimeError(
            f"Could not find any Zenodo records for conceptrecid {conceptrecid}."
        )
    return int(hits[0]["id"])


def create_new_version(api_url: str, token: str, record_id: int) -> dict:
    response = api_request(
        "POST",
        f"{api_url}/deposit/depositions/{record_id}/actions/newversion",
        token=token,
    )
    latest_draft = response.get("links", {}).get("latest_draft")
    if not latest_draft:
        raise RuntimeError(
            "Zenodo did not return links.latest_draft after requesting a new version."
        )
    return api_request("GET", latest_draft, token=token)


def clear_draft_files(draft: dict, token: str) -> None:
    files_url = draft.get("links", {}).get("files")
    deposition_id = draft["id"]
    if not files_url:
        return
    files = api_request("GET", files_url, token=token) or []
    for file_info in files:
        file_id = file_info["id"]
        api_request(
            "DELETE",
            f"{files_url}/{file_id}",
            token=token,
            expect_json=False,
        )
        print(f"Deleted inherited Zenodo file {file_id} from draft {deposition_id}.")


def upload_dist_files(draft: dict, token: str, dist_dir: Path) -> None:
    bucket_url = draft.get("links", {}).get("bucket")
    if not bucket_url:
        raise RuntimeError("Zenodo draft is missing the upload bucket URL.")
    for path in sorted(dist_dir.iterdir()):
        if not path.is_file():
            continue
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as handle:
            api_request(
                "PUT",
                f"{bucket_url}/{parse.quote(path.name)}",
                token=token,
                data=handle.read(),
                content_type=content_type,
            )
        print(f"Uploaded {path.name} to Zenodo draft {draft['id']}.")


def update_metadata(draft: dict, token: str, metadata: dict) -> dict:
    return api_request(
        "PUT",
        draft["links"]["self"],
        token=token,
        json_data={"metadata": metadata},
    )


def publish_draft(draft: dict, token: str) -> dict:
    return api_request("POST", draft["links"]["publish"], token=token)


def validate_inputs(dist_dir: Path, access_token: str | None) -> None:
    if not access_token:
        raise SystemExit(
            "Missing Zenodo access token. Set ZENODO_ACCESS_TOKEN or pass "
            "--access-token."
        )
    if not dist_dir.is_dir():
        raise SystemExit(f"Distribution directory {dist_dir} does not exist.")
    files = [path for path in dist_dir.iterdir() if path.is_file()]
    if not files:
        raise SystemExit(f"Distribution directory {dist_dir} does not contain files.")


def main() -> int:
    args = parse_args()
    validate_inputs(args.dist_dir, args.access_token)
    citation = load_citation(args.citation)
    pyproject = load_pyproject(args.pyproject)
    metadata = build_metadata(citation, pyproject)
    conceptrecid = resolve_concept_recid(args.api_url, citation["doi"])
    record_id = latest_record_id(args.api_url, conceptrecid)
    draft = create_new_version(args.api_url, args.access_token, record_id)
    clear_draft_files(draft, args.access_token)
    upload_dist_files(draft, args.access_token, args.dist_dir)
    draft = update_metadata(draft, args.access_token, metadata)
    published = publish_draft(draft, args.access_token)
    doi = published.get("doi") or published.get("metadata", {}).get("doi")
    print(
        f"Published Zenodo release record {published['id']} for "
        f"version {metadata['version']} ({doi})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
