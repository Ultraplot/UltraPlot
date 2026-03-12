from __future__ import annotations

import importlib.util
import re
from pathlib import Path

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
