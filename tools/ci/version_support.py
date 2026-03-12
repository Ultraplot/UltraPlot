#!/usr/bin/env python3
"""
Shared helpers for UltraPlot's supported Python/Matplotlib version contract.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"


def load_pyproject(path: Path = PYPROJECT) -> dict:
    """
    Load the project metadata used to define the supported version contract.
    """
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _expand_half_open_minor_range(spec: str) -> list[str]:
    """
    Expand same-major constraints like ``>=3.10,<3.15`` into minor versions.

    This fallback is only safe when the lower and upper bounds are within the
    same major series. Once support crosses a major boundary, the project
    should declare the supported minors explicitly in ``tool.ultraplot``.
    """
    min_match = re.search(r">=\s*(\d+\.\d+)", spec)
    max_match = re.search(r"<\s*(\d+\.\d+)", spec)
    if min_match is None or max_match is None:
        return []
    major_min, minor_min = map(int, min_match.group(1).split("."))
    major_max, minor_max = map(int, max_match.group(1).split("."))
    if major_min != major_max:
        raise ValueError(
            f"Cannot infer supported minor versions from cross-major range {spec!r}. "
            "Declare explicit versions in [tool.ultraplot.core_versions]."
        )
    versions = []
    major, minor = major_min, minor_min
    while (major, minor) < (major_max, minor_max):
        versions.append(f"{major}.{minor}")
        minor += 1
    return versions


def _configured_core_versions(pyproject: dict, key: str) -> list[str]:
    """
    Return explicitly configured core versions, or an empty list if omitted.
    """
    return list(
        pyproject.get("tool", {})
        .get("ultraplot", {})
        .get("core_versions", {})
        .get(key, ())
    )


def _parse_half_open_minor_bounds(spec: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Parse ``>=X.Y,<A.B`` style bounds into comparable major/minor tuples.
    """
    min_match = re.search(r">=\s*(\d+\.\d+)", spec)
    max_match = re.search(r"<\s*(\d+\.\d+)", spec)
    if min_match is None or max_match is None:
        raise ValueError(f"Could not parse half-open minor range {spec!r}.")
    min_version = tuple(map(int, min_match.group(1).split(".")))
    max_version = tuple(map(int, max_match.group(1).split(".")))
    return min_version, max_version


def version_satisfies_half_open_minor_range(version: str, spec: str) -> bool:
    """
    Return whether a ``major.minor`` version falls within a ``>=,<`` range.
    """
    current = tuple(map(int, version.split(".")))
    minimum, maximum = _parse_half_open_minor_bounds(spec)
    return minimum <= current < maximum


def _validate_versions_against_spec(
    versions: list[str], spec: str, *, label: str
) -> list[str]:
    """
    Ensure explicitly configured versions remain inside the declared bounds.
    """
    invalid = [
        version
        for version in versions
        if not version_satisfies_half_open_minor_range(version, spec)
    ]
    if invalid:
        raise ValueError(
            f"Configured {label} versions {invalid!r} fall outside declared range {spec!r}."
        )
    return versions


def supported_python_versions(pyproject: dict | None = None) -> list[str]:
    """
    Return the supported Python minors derived from ``requires-python``.
    """
    pyproject = pyproject or load_pyproject()
    configured = _configured_core_versions(pyproject, "python")
    spec = pyproject["project"]["requires-python"]
    if configured:
        return _validate_versions_against_spec(configured, spec, label="python")
    return _expand_half_open_minor_range(spec)


def supported_matplotlib_versions(pyproject: dict | None = None) -> list[str]:
    """
    Return the supported Matplotlib minors derived from dependencies.
    """
    pyproject = pyproject or load_pyproject()
    configured = _configured_core_versions(pyproject, "matplotlib")
    for dep in pyproject["project"]["dependencies"]:
        if dep.startswith("matplotlib"):
            if configured:
                return _validate_versions_against_spec(
                    configured,
                    dep,
                    label="matplotlib",
                )
            return _expand_half_open_minor_range(dep)
    raise AssertionError("matplotlib dependency not found in pyproject.toml")


def supported_python_classifiers(pyproject: dict | None = None) -> list[str]:
    """
    Extract the explicit Python version classifiers from ``pyproject.toml``.
    """
    pyproject = pyproject or load_pyproject()
    prefix = "Programming Language :: Python :: "
    versions = []
    for classifier in pyproject["project"]["classifiers"]:
        if classifier.startswith(prefix):
            tail = classifier.removeprefix(prefix)
            if re.fullmatch(r"\d+\.\d+", tail):
                versions.append(tail)
    return versions


def build_core_test_matrix(
    python_versions: list[str], matplotlib_versions: list[str]
) -> list[dict[str, str]]:
    """
    Build the representative CI matrix from the supported version bounds.

    We intentionally sample the oldest, midpoint, and newest supported
    Python/Matplotlib combinations instead of exhaustively testing every pair.
    """
    midpoint_python = python_versions[len(python_versions) // 2]
    midpoint_mpl = matplotlib_versions[len(matplotlib_versions) // 2]
    candidates = [
        (python_versions[0], matplotlib_versions[0]),
        (midpoint_python, midpoint_mpl),
        (python_versions[-1], matplotlib_versions[-1]),
    ]
    matrix = []
    seen = set()
    for py_ver, mpl_ver in candidates:
        key = (py_ver, mpl_ver)
        if key in seen:
            continue
        seen.add(key)
        matrix.append({"python-version": py_ver, "matplotlib-version": mpl_ver})
    return matrix


def build_version_payload(pyproject: dict | None = None) -> dict:
    """
    Bundle the version contract into the shape expected by CI and tests.
    """
    pyproject = pyproject or load_pyproject()
    python_versions = supported_python_versions(pyproject)
    matplotlib_versions = supported_matplotlib_versions(pyproject)
    return {
        "python_versions": python_versions,
        "matplotlib_versions": matplotlib_versions,
        "test_matrix": build_core_test_matrix(python_versions, matplotlib_versions),
    }


def _emit_github_output(payload: dict) -> str:
    """
    Format the derived version payload for ``$GITHUB_OUTPUT`` consumption.
    """
    return "\n".join(
        (
            f"python-versions={json.dumps(payload['python_versions'], separators=(',', ':'))}",
            f"matplotlib-versions={json.dumps(payload['matplotlib_versions'], separators=(',', ':'))}",
            f"test-matrix={json.dumps(payload['test_matrix'], separators=(',', ':'))}",
        )
    )


def main() -> int:
    """
    CLI entry point used by GitHub Actions and local verification.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--format",
        choices=("json", "github-output"),
        default="json",
    )
    args = parser.parse_args()

    payload = build_version_payload()
    if args.format == "github-output":
        print(_emit_github_output(payload))
    else:
        print(json.dumps(payload))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
