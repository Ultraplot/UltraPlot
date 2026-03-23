import importlib.util
import json
import os
import subprocess
import sys
import ast
from pathlib import Path

import pytest


def _run(code):
    env = os.environ.copy()
    proc = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.stdout.strip()


def test_import_is_lightweight():
    code = """
import json
import sys
pre = set(sys.modules)
import ultraplot  # noqa: F401
post = set(sys.modules)
new = {name.split('.', 1)[0] for name in (post - pre)}
heavy = {"matplotlib", "IPython", "cartopy", "mpl_toolkits"}
print(json.dumps(sorted(new & heavy)))
"""
    out = _run(code)
    assert out == "[]"


def test_star_import_exposes_public_api():
    code = """
from ultraplot import *  # noqa: F403
assert "rc" in globals()
assert "Figure" in globals()
assert "Axes" in globals()
print("ok")
"""
    out = _run(code)
    assert out == "ok"


def test_setup_eager_imports_modules():
    code = """
import sys
import ultraplot as uplt
assert "ultraplot.axes" not in sys.modules
uplt.setup(eager=True)
assert "ultraplot.axes" in sys.modules
print("ok")
"""
    out = _run(code)
    assert out == "ok"


def test_setup_uses_rc_eager_import():
    code = """
import sys
import ultraplot as uplt
uplt.setup(eager=False)
assert "ultraplot.axes" not in sys.modules
uplt.rc["ultraplot.eager_import"] = True
uplt.setup()
assert "ultraplot.axes" in sys.modules
print("ok")
"""
    out = _run(code)
    assert out == "ok"


def test_dir_populates_attr_map(monkeypatch):
    import ultraplot as uplt

    monkeypatch.setattr(uplt, "_ATTR_MAP", None, raising=False)
    names = dir(uplt)
    assert "close" in names
    assert uplt._ATTR_MAP is not None


def test_extra_and_registry_accessors(monkeypatch):
    import ultraplot as uplt

    monkeypatch.setattr(uplt, "_REGISTRY_ATTRS", None, raising=False)
    assert hasattr(uplt.colormaps, "get_cmap")
    assert uplt.internals.__name__.endswith("internals")
    assert isinstance(uplt.LogNorm, type)


def test_all_triggers_eager_load(monkeypatch):
    import ultraplot as uplt

    monkeypatch.delattr(uplt, "__all__", raising=False)
    names = uplt.__all__
    assert "setup" in names
    assert "pyplot" in names


def test_optional_module_attrs():
    import ultraplot as uplt

    if importlib.util.find_spec("cartopy") is None:
        with pytest.raises(AttributeError):
            _ = uplt.cartopy
    else:
        assert uplt.cartopy.__name__ == "cartopy"

    if importlib.util.find_spec("mpl_toolkits.basemap") is None:
        with pytest.raises(AttributeError):
            _ = uplt.basemap
    else:
        assert uplt.basemap.__name__.endswith("basemap")

    with pytest.raises(AttributeError):
        getattr(uplt, "pytest_plugins")


def test_figure_submodule_does_not_clobber_callable():
    import ultraplot as uplt

    assert isinstance(uplt.figure(), uplt.Figure)


def test_internals_lazy_attrs():
    from ultraplot import internals

    assert internals.__name__.endswith("internals")
    assert "rcsetup" in dir(internals)
    assert internals.rcsetup is not None
    assert internals.warnings is not None
    assert str(internals._version_mpl)
    assert issubclass(internals.UltraPlotWarning, Warning)
    rc_matplotlib = internals._get_rc_matplotlib()
    assert "axes.grid" in rc_matplotlib


def test_docstring_missing_triggers_lazy_import():
    from ultraplot.internals import docstring

    with pytest.raises(KeyError):
        docstring._snippet_manager["ticker.not_a_real_key"]
    with pytest.raises(KeyError):
        docstring._snippet_manager["does_not_exist.key"]


def _collect_type_checking_names():
    root = Path(__file__).resolve().parents[2]
    init_path = root / "ultraplot" / "__init__.py"
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name):
            if node.test.id != "TYPE_CHECKING":
                continue
            names = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Import):
                    for alias in child.names:
                        names.add(alias.asname or alias.name.split(".")[0])
                elif isinstance(child, ast.ImportFrom):
                    for alias in child.names:
                        names.add(alias.asname or alias.name)
                elif isinstance(child, ast.AnnAssign) and isinstance(
                    child.target, ast.Name
                ):
                    names.add(child.target.id)
            return names
    raise AssertionError("Missing TYPE_CHECKING export block in ultraplot.__init__")


def test_type_checking_block_exposes_core_lazy_api():
    names = _collect_type_checking_names()
    expected = {
        "Figure",
        "colormaps",
        "figure",
        "pyplot",
        "rc",
        "show_colors",
        "subplot",
        "subplots",
    }
    assert expected.issubset(names)


def test_package_marks_itself_typed():
    import ultraplot as uplt

    typed_marker = Path(uplt.__file__).resolve().with_name("py.typed")
    assert typed_marker.is_file()


def test_pyproject_includes_typed_marker():
    root = Path(__file__).resolve().parents[2]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '[tool.setuptools.package-data]' in text
    assert 'ultraplot = ["py.typed"]' in text
