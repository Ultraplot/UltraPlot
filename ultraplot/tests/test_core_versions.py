from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
NOXFILE = ROOT / "noxfile.py"
MAIN_WORKFLOW = ROOT / ".github" / "workflows" / "main.yml"
TEST_MAP_WORKFLOW = ROOT / ".github" / "workflows" / "test-map.yml"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"
VERSION_SUPPORT = ROOT / "tools" / "ci" / "version_support.py"


def _load_version_support():
    """
    Import the shared version helper directly from the repo checkout.
    """
    spec = importlib.util.spec_from_file_location("version_support", VERSION_SUPPORT)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load 'version_support' module from {VERSION_SUPPORT}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_python_classifiers_match_requires_python():
    """
    Supported Python classifiers should mirror the declared version range.
    """
    version_support = _load_version_support()
    pyproject = version_support.load_pyproject(PYPROJECT)
    assert version_support.supported_python_classifiers(pyproject) == (
        version_support.supported_python_versions(pyproject)
    )


def test_explicit_core_versions_stay_within_declared_bounds():
    """
    Explicitly configured core versions should stay inside the declared ranges.
    """
    version_support = _load_version_support()
    pyproject = version_support.load_pyproject(PYPROJECT)
    python_spec = pyproject["project"]["requires-python"]
    matplotlib_spec = next(
        dep
        for dep in pyproject["project"]["dependencies"]
        if dep.startswith("matplotlib")
    )
    assert all(
        version_support.version_satisfies_half_open_minor_range(version, python_spec)
        for version in version_support.supported_python_versions(pyproject)
    )
    assert all(
        version_support.version_satisfies_half_open_minor_range(
            version,
            matplotlib_spec,
        )
        for version in version_support.supported_matplotlib_versions(pyproject)
    )


def test_explicit_cross_major_matplotlib_versions_are_supported(tmp_path):
    """
    Explicit core-version lists should support future major-version upgrades.
    """
    version_support = _load_version_support()
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
[project]
requires-python = ">=3.12,<3.15"
classifiers = [
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
]
dependencies = ["matplotlib>=3.10,<4.2"]

[tool.ultraplot.core_versions]
python = ["3.12", "3.13", "3.14"]
matplotlib = ["3.10", "4.0", "4.1"]
""".strip(),
        encoding="utf-8",
    )
    pyproject = version_support.load_pyproject(pyproject_path)
    assert version_support.supported_matplotlib_versions(pyproject) == [
        "3.10",
        "4.0",
        "4.1",
    ]


def test_cross_major_range_filter_selects_valid_versions():
    """
    Range filtering should work across major boundaries once candidate minors exist.
    """
    version_support = _load_version_support()
    versions = ["3.9", "3.10", "3.11", "4.0", "4.1", "4.2"]
    assert version_support.select_versions_within_half_open_minor_range(
        versions,
        ">=3.10,<4.2",
    ) == ["3.10", "3.11", "4.0", "4.1"]


def test_main_workflow_uses_shared_version_support_script():
    """
    The matrix workflow should consume the shared version helper, not reparse inline.
    """
    text = MAIN_WORKFLOW.read_text(encoding="utf-8")
    assert "python tools/ci/version_support.py --format github-output" in text


def test_noxfile_uses_shared_version_support_module():
    """
    Local test matrix generation should reuse the shared version helper.
    """
    text = NOXFILE.read_text(encoding="utf-8")
    assert "VERSION_SUPPORT_PATH" in text
    assert "supported_python_versions" in text
    assert "supported_matplotlib_versions" in text


def test_test_map_workflow_pins_oldest_supported_python_and_matplotlib():
    """
    The cache-building workflow should exercise the lowest supported core pair.
    """
    version_support = _load_version_support()
    pyproject = version_support.load_pyproject(PYPROJECT)
    expected_python = version_support.supported_python_versions(pyproject)[0]
    expected_mpl = version_support.supported_matplotlib_versions(pyproject)[0]
    text = TEST_MAP_WORKFLOW.read_text(encoding="utf-8")
    assert f"python={expected_python}" in text
    assert f"matplotlib={expected_mpl}" in text


def test_publish_workflow_python_is_supported():
    """
    Package builds should run on a Python version that UltraPlot declares support for.
    """
    version_support = _load_version_support()
    pyproject = version_support.load_pyproject(PYPROJECT)
    supported = set(version_support.supported_python_versions(pyproject))
    text = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r'python-version:\s*"(\d+\.\d+)"', text)
    assert match is not None
    assert match.group(1) in supported


@pytest.mark.parametrize("matplotlib_version", ["3.9", "3.10", "3.11", "4.0"])
def test_environment_omits_only_incompatible_basemap(matplotlib_version):
    support = _load_version_support()
    environment = (
        "dependencies:\n"
        "  # basemap is an optional backend\n"
        "  - basemap >=1.4.1\n"
        "  - basemap-data\n"
        "  - matplotlib>=3.9\n"
        "  - cartopy\n"
        "  - pip:\n"
        "      - mpltern\n"
        "      - pycirclize\n"
    )
    result = support.environment_for_matplotlib(environment, matplotlib_version)
    expected = environment
    if matplotlib_version in ("3.11", "4.0"):
        expected = expected.replace("  - basemap >=1.4.1\n", "")
    assert result == expected


@pytest.mark.parametrize("matplotlib_version", ["3.9", "3.11"])
def test_environment_cli_writes_version_specific_yaml(tmp_path, matplotlib_version):
    output = tmp_path / "generated" / "environment.yml"
    subprocess.run(
        [
            sys.executable,
            str(VERSION_SUPPORT),
            "--matplotlib-version",
            matplotlib_version,
            "--environment-output",
            str(output),
        ],
        check=True,
    )
    environment = output.read_text(encoding="utf-8")
    assert ("  - basemap >=1.4.1\n" in environment) == (matplotlib_version == "3.9")
    assert "      - mpltern\n" in environment
    assert "      - pycirclize\n" in environment


def test_coverage_runs_the_supported_version_matrix():
    """New Matplotlib branches must contribute to the uploaded coverage."""
    text = MAIN_WORKFLOW.read_text(encoding="utf-8")
    coverage = text.split("\n  coverage:\n", 1)[1].split("\n  build:\n", 1)[0]
    assert "fromJson(needs.get-versions.outputs.test-matrix)" in coverage
    assert "matplotlib=${{ matrix.matplotlib-version }}" in coverage
    assert "--environment-output" in coverage
    assert "--cov=ultraplot --cov-branch" in coverage


@pytest.mark.parametrize(
    "python_version,matplotlib_version,expected",
    [("3.14", "3.10", True), ("3.14", "3.11", False), ("3.15", "3.10", False)],
)
def test_baseline_support_uses_base_metadata(
    tmp_path, python_version, matplotlib_version, expected
):
    """A new supported version must not run the older base's incompatible tests."""
    baseline = tmp_path / "pyproject.toml"
    baseline.write_text(
        '[project]\nrequires-python = ">=3.10,<3.15"\n'
        'dependencies = ["matplotlib>=3.9,<3.11"]\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(VERSION_SUPPORT),
            "--baseline-pyproject",
            str(baseline),
            "--python-version",
            python_version,
            "--matplotlib-version",
            matplotlib_version,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == f"baseline-supported={str(expected).lower()}"
