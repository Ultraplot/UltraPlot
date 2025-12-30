import json
import os
import subprocess
import sys


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
