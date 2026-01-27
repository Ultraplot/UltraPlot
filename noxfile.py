from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import tempfile
from pathlib import Path

import nox

PROJECT_ROOT = Path(__file__).parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["tests"]


def _load_pyproject() -> dict:
    try:
        import tomllib
    except ImportError:  # pragma: no cover - py<3.11
        import tomli as tomllib
    with PYPROJECT_PATH.open("rb") as f:
        return tomllib.load(f)


def _version_range(requirement: str) -> list[str]:
    min_match = re.search(r">=(\d+\.\d+)", requirement)
    max_match = re.search(r"<(\d+\.\d+)", requirement)
    if not (min_match and max_match):
        return []
    min_v = tuple(map(int, min_match.group(1).split(".")))
    max_v = tuple(map(int, max_match.group(1).split(".")))
    versions = []
    current = min_v
    while current < max_v:
        versions.append(".".join(map(str, current)))
        current = (current[0], current[1] + 1)
    return versions


def _matrix_versions() -> tuple[list[str], list[str]]:
    data = _load_pyproject()
    python_req = data["project"]["requires-python"]
    py_versions = _version_range(python_req)
    mpl_req = next(
        dep for dep in data["project"]["dependencies"] if dep.startswith("matplotlib")
    )
    mpl_versions = _version_range(mpl_req) or ["3.9"]
    return py_versions, mpl_versions


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
