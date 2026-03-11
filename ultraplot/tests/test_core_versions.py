from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
MAIN_WORKFLOW = ROOT / ".github" / "workflows" / "main.yml"
TEST_MAP_WORKFLOW = ROOT / ".github" / "workflows" / "test-map.yml"
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-pypi.yml"
VERSION_SUPPORT = ROOT / "tools" / "ci" / "version_support.py"


def _load_version_support():
    """
    Import the shared version helper directly from the repo checkout.
    """
    spec = importlib.util.spec_from_file_location("version_support", VERSION_SUPPORT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
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


def test_main_workflow_uses_shared_version_support_script():
    """
    The matrix workflow should consume the shared version helper, not reparse inline.
    """
    text = MAIN_WORKFLOW.read_text(encoding="utf-8")
    assert "python tools/ci/version_support.py --format github-output" in text


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
