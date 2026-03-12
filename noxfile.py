from __future__ import annotations

import json
import os
import shlex
import shutil
import tempfile
import importlib.util
from pathlib import Path

import nox

PROJECT_ROOT = Path(__file__).parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
VERSION_SUPPORT_PATH = PROJECT_ROOT / "tools" / "ci" / "version_support.py"

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["tests"]


def _load_version_support():
    """
    Import the shared version-support helper from the repo checkout.
    """
    spec = importlib.util.spec_from_file_location(
        "version_support",
        VERSION_SUPPORT_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load 'version_support' module from {VERSION_SUPPORT_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _matrix_versions() -> tuple[list[str], list[str]]:
    """
    Derive the supported Python/Matplotlib test matrix from the shared helper.
    """
    version_support = _load_version_support()
    data = version_support.load_pyproject(PYPROJECT_PATH)
    return (
        version_support.supported_python_versions(data),
        version_support.supported_matplotlib_versions(data),
    )


PYTHON_VERSIONS, MPL_VERSIONS = _matrix_versions()


def _mamba_root() -> Path:
    return PROJECT_ROOT / ".nox" / "micromamba"


def _mamba_exe(session: nox.Session) -> str:
    exe = os.environ.get("MAMBA_EXE", "micromamba")
    if shutil.which(exe):
        return exe
    session.error(
        "micromamba not found; install it or set MAMBA_EXE to the micromamba path."
    )
    return exe


def _mamba_env_name(python_version: str, matplotlib_version: str) -> str:
    return f"ultraplot-py{python_version}-mpl{matplotlib_version}"


def _ensure_mamba_env(
    session: nox.Session, python_version: str, matplotlib_version: str
) -> str:
    root = _mamba_root()
    env_name = _mamba_env_name(python_version, matplotlib_version)
    env_path = root / "envs" / env_name
    if env_path.exists():
        return env_name
    exe = _mamba_exe(session)
    env = os.environ.copy()
    env["MAMBA_ROOT_PREFIX"] = str(root)
    session.run(
        exe,
        "create",
        "-y",
        "-n",
        env_name,
        "-f",
        str(PROJECT_ROOT / "environment.yml"),
        f"python={python_version}",
        f"matplotlib={matplotlib_version}",
        external=True,
        env=env,
    )
    return env_name


def _mamba_run(session: nox.Session, env_name: str, *args: str) -> None:
    exe = _mamba_exe(session)
    env = os.environ.copy()
    env["MAMBA_ROOT_PREFIX"] = str(_mamba_root())
    quoted = " ".join(shlex.quote(arg) for arg in args)
    session.run(
        "bash",
        "-lc",
        f'eval "$({shlex.quote(exe)} shell hook -s bash)"; '
        f"micromamba activate {shlex.quote(env_name)}; {quoted}",
        external=True,
        env=env,
    )


def _install_ultraplot(session: nox.Session, env_name: str, path: str) -> None:
    _mamba_run(
        session,
        env_name,
        "python",
        "-m",
        "pip",
        "install",
        "--no-build-isolation",
        "--no-deps",
        path,
    )


def _selected_nodeids(env: dict[str, str]) -> list[str] | None:
    if env.get("TEST_MODE", "full") != "selected":
        return None
    tokens = env.get("TEST_NODEIDS", "").split()
    nodeids = [t for t in tokens if "::" in t or t.endswith(".py")]
    return nodeids or None


@nox.session(venv_backend="none")
@nox.parametrize("python_version", PYTHON_VERSIONS)
@nox.parametrize("matplotlib_version", MPL_VERSIONS)
def tests(session: nox.Session, python_version: str, matplotlib_version: str) -> None:
    env_name = _ensure_mamba_env(session, python_version, matplotlib_version)
    _install_ultraplot(session, env_name, ".")
    nodeids = _selected_nodeids(session.env)
    if nodeids:
        _mamba_run(
            session,
            env_name,
            "pytest",
            "--cov=ultraplot",
            "--cov-branch",
            "--cov-report",
            "term-missing",
            "--cov-report=xml",
            *nodeids,
        )
    else:
        _mamba_run(
            session,
            env_name,
            "pytest",
            "--cov=ultraplot",
            "--cov-branch",
            "--cov-report",
            "term-missing",
            "--cov-report=xml",
            "ultraplot",
        )


@nox.session
def select_tests(session: nox.Session) -> None:
    if len(session.posargs) >= 2:
        base, head = session.posargs[:2]
    else:
        base, head = "origin/main", "HEAD"
    ci_dir = PROJECT_ROOT / ".ci"
    ci_dir.mkdir(parents=True, exist_ok=True)
    changed = ci_dir / "changed.txt"
    with changed.open("w", encoding="utf-8") as changed_file:
        session.run(
            "git",
            "diff",
            "--name-only",
            base,
            head,
            external=True,
            stdout=changed_file,
        )
    selection = ci_dir / "selection.json"
    session.run(
        "python",
        "tools/ci/select_tests.py",
        "--map",
        str(ci_dir / "test-map.json"),
        "--changed-files",
        str(changed),
        "--output",
        str(selection),
        "--always-full",
        "pyproject.toml",
        "--always-full",
        "environment.yml",
        "--always-full",
        "ultraplot/__init__.py",
        "--ignore",
        "docs/**",
        "--ignore",
        "README.rst",
    )
    data = json.loads(selection.read_text(encoding="utf-8"))
    session.log("mode=%s", data.get("mode"))
    session.log("tests=%s", " ".join(data.get("tests", [])))


@nox.session
def build_test_map(session: nox.Session) -> None:
    env_name = _ensure_mamba_env(session, "3.11", "3.9")
    _install_ultraplot(session, env_name, ".")
    ci_dir = PROJECT_ROOT / ".ci"
    ci_dir.mkdir(parents=True, exist_ok=True)
    _mamba_run(
        session,
        env_name,
        "pytest",
        "-n",
        "auto",
        "--cov=ultraplot",
        "--cov-branch",
        "--cov-context=test",
        "--cov-report=",
        "ultraplot",
    )
    _mamba_run(
        session,
        env_name,
        "python",
        "tools/ci/build_test_map.py",
        "--coverage-file",
        ".coverage",
        "--output",
        str(ci_dir / "test-map.json"),
        "--root",
        ".",
    )


@nox.session(venv_backend="none")
@nox.parametrize("python_version", PYTHON_VERSIONS)
@nox.parametrize("matplotlib_version", MPL_VERSIONS)
def compare_baseline(
    session: nox.Session, python_version: str, matplotlib_version: str
) -> None:
    base_ref = session.env.get("BASE_REF", "origin/main")
    baseline_dir = Path(session.env.get("BASELINE_DIR", "ultraplot/tests/baseline"))
    results_dir = Path(session.env.get("RESULTS_DIR", "results"))
    baseline_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    env_name = _ensure_mamba_env(session, python_version, matplotlib_version)
    _install_ultraplot(session, env_name, ".")
    nodeids = _selected_nodeids(session.env)

    with tempfile.TemporaryDirectory() as tmpdir:
        session.run(
            "git",
            "worktree",
            "add",
            "--detach",
            tmpdir,
            base_ref,
            external=True,
        )
        try:
            _install_ultraplot(session, env_name, tmpdir)
            _mamba_run(
                session,
                env_name,
                "python",
                "-c",
                "import ultraplot as plt; plt.config.Configurator()._save_yaml('ultraplot.yml')",
            )
            if nodeids:
                _mamba_run(
                    session,
                    env_name,
                    "pytest",
                    "-W",
                    "ignore",
                    "--mpl-generate-path",
                    str(baseline_dir),
                    "--mpl-default-style=./ultraplot.yml",
                    *nodeids,
                )
            else:
                _mamba_run(
                    session,
                    env_name,
                    "pytest",
                    "-W",
                    "ignore",
                    "--mpl-generate-path",
                    str(baseline_dir),
                    "--mpl-default-style=./ultraplot.yml",
                    "ultraplot/tests",
                )
        finally:
            session.run(
                "git",
                "worktree",
                "remove",
                "--force",
                tmpdir,
                external=True,
            )
            session.run("git", "worktree", "prune", external=True)

    _install_ultraplot(session, env_name, ".")
    _mamba_run(
        session,
        env_name,
        "python",
        "-c",
        "import ultraplot as plt; plt.config.Configurator()._save_yaml('ultraplot.yml')",
    )
    if nodeids:
        _mamba_run(
            session,
            env_name,
            "pytest",
            "-W",
            "ignore",
            "--mpl",
            "--mpl-baseline-path",
            str(baseline_dir),
            "--mpl-results-path",
            str(results_dir),
            "--mpl-generate-summary=html",
            "--mpl-default-style=./ultraplot.yml",
            *nodeids,
        )
    else:
        _mamba_run(
            session,
            env_name,
            "pytest",
            "-W",
            "ignore",
            "--mpl",
            "--mpl-baseline-path",
            str(baseline_dir),
            "--mpl-results-path",
            str(results_dir),
            "--mpl-generate-summary=html",
            "--mpl-default-style=./ultraplot.yml",
            "ultraplot/tests",
        )


@nox.session
def build_dist(session: nox.Session) -> None:
    session.install(
        "--upgrade", "pip", "wheel", "setuptools", "setuptools_scm", "build", "twine"
    )
    session.run("python", "-m", "build", "--sdist", "--wheel", ".", "--outdir", "dist")
    session.run("python", "-m", "pip", "install", "dist/ultraplot*.whl")
    session.run(
        "python",
        "-c",
        "import ultraplot as u; assert not u.__version__.startswith('0.'), u.__version__",
    )
    session.run("python", "-m", "twine", "check", "dist/*")
