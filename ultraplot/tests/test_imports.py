import ast
import importlib.util
import json
import os
import subprocess
import sys
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


def _parse_type_checking_names():
    """
    Parse ultraplot/__init__.py and return every name declared inside the
    ``if TYPE_CHECKING:`` block, mapped to its import origin.

    Returns a dict of ``{public_name: (module, original_name)}``.
    """
    init_path = Path(__file__).parent.parent / "__init__.py"
    tree = ast.parse(init_path.read_text(encoding="utf-8"))

    names = {}
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        # Match `if TYPE_CHECKING:` (handles both bare name and attribute access)
        test = node.test
        is_type_checking = (
            isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"
        ) or (isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")
        if not is_type_checking:
            continue
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.ImportFrom):
                for alias in stmt.names:
                    public_name = alias.asname or alias.name
                    names[public_name] = (stmt.module, alias.name)
            elif isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    public_name = alias.asname or alias.name.split(".")[0]
                    names[public_name] = (alias.name, None)
    return names


def test_type_checking_names_accessible_at_runtime():
    """
    Every name declared inside ``if TYPE_CHECKING:`` in ``__init__.py`` must
    also be accessible at runtime via the lazy loader.

    This ensures the TYPE_CHECKING block never silently drifts out of sync with
    what the package actually exposes.
    """
    import ultraplot

    declared = _parse_type_checking_names()
    assert declared, "TYPE_CHECKING block is empty or could not be parsed"

    missing = [name for name in declared if not hasattr(ultraplot, name)]
    assert not missing, (
        "Names declared in the TYPE_CHECKING block are not accessible at runtime.\n"
        "Either remove them from the TYPE_CHECKING block or expose them via the "
        "lazy loader / _LAZY_LOADING_EXCEPTIONS:\n"
        + "\n".join(f"  ultraplot.{n}" for n in missing)
    )


def test_type_checking_block_covers_public_all():
    """
    Every name in ``ultraplot.__all__`` that is a public class or callable
    should be declared in the TYPE_CHECKING block so type checkers can resolve it.

    The following categories are intentionally excluded:

    - Registry-derived names (e.g. ``LogNorm``) — populated dynamically from
      matplotlib at runtime; cannot be enumerated statically.
    - Submodule names (e.g. ``internals``) — are modules, not types.
    - Module-level scalars defined directly in ``__init__.py`` (``name``,
      ``version``, ``__version__``, ``setup``) — already visible to type checkers
      without an import.
    - Deprecated ``_rename_objs`` wrappers (e.g. ``RcConfigurator``,
      ``inline_backend_fmt``, ``Colors``) — their runtime type is a dynamically
      generated class/function from ``internals.warnings``; they cannot be
      imported cleanly and are not worth exposing to type checkers.
    """
    import types
    import ultraplot

    declared = set(_parse_type_checking_names())
    all_names = set(ultraplot.__all__)

    # Registry-derived names — dynamically populated from matplotlib.
    ultraplot._build_registry_map()
    registry_names = set(ultraplot._REGISTRY_ATTRS or {})

    # Submodule names — are modules, not types.
    submodule_names = {
        n
        for n in all_names
        if isinstance(getattr(ultraplot, n, None), types.ModuleType)
    }

    # Names already defined at module-level in __init__.py itself — type
    # checkers see them directly without needing an import statement.
    init_level = {"__version__", "version", "name", "setup"}

    # Deprecated _rename_objs wrappers — their __module__ is internals.warnings
    # because that is where the wrapper factory lives.
    deprecated_wrappers = {
        n
        for n in all_names
        if getattr(getattr(ultraplot, n, None), "__module__", "").endswith(
            "internals.warnings"
        )
    }

    expected = (
        all_names - registry_names - submodule_names - init_level - deprecated_wrappers
    )
    missing_from_type_checking = sorted(expected - declared)
    assert not missing_from_type_checking, (
        "Names in ultraplot.__all__ are missing from the TYPE_CHECKING block.\n"
        "Add them to the ``if TYPE_CHECKING:`` block in ultraplot/__init__.py:\n"
        + "\n".join(f"  {n}" for n in missing_from_type_checking)
    )


def test_docstring_missing_triggers_lazy_import():
    from ultraplot.internals import docstring

    with pytest.raises(KeyError):
        docstring._snippet_manager["ticker.not_a_real_key"]
    with pytest.raises(KeyError):
        docstring._snippet_manager["does_not_exist.key"]
