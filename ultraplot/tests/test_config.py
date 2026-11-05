import importlib
import os
import pathlib
import subprocess
import sys
import threading
from queue import Queue

import pytest

import ultraplot as uplt


def test_wrong_keyword_reset():
    """
    The context should reset after a failed attempt.
    """
    # Init context
    uplt.rc.context()
    config = uplt.rc
    # Set a wrong key
    with pytest.raises(KeyError):
        config._get_item_dicts("non_existing_key", "non_existing_value")
    # Set a known good value
    config._get_item_dicts("coastcolor", "black")
    # Confirm we can still plot
    fig, ax = uplt.subplots(proj="cyl")
    ax.format(coastcolor="black")
    fig.canvas.draw()


def test_cycle_in_rc_file(tmp_path):
    """
    Test that loading an rc file correctly overwrites the cycle setting.
    """
    rc_content = "cycle: colorblind"
    rc_file = tmp_path / "test.rc"
    rc_file.write_text(rc_content)

    # Load the file directly. This should overwrite any existing settings.
    uplt.rc.load(str(rc_file))

    assert uplt.rc["cycle"] == "colorblind"


def test_sankey_rc_defaults():
    """
    Sanity check the new sankey defaults in rc.
    """
    assert uplt.rc["sankey.nodepad"] == 0.02
    assert uplt.rc["sankey.nodewidth"] == 0.03
    assert uplt.rc["sankey.margin"] == 0.05
    assert uplt.rc["sankey.flow.alpha"] == 0.75
    assert uplt.rc["sankey.flow.curvature"] == 0.5
    assert uplt.rc["sankey.node.facecolor"] == "0.75"


def test_ribbon_rc_defaults():
    """
    Sanity check ribbon defaults in rc.
    """
    assert uplt.rc["ribbon.xmargin"] == 0.12
    assert uplt.rc["ribbon.ymargin"] == 0.08
    assert uplt.rc["ribbon.rowheightratio"] == 2.2
    assert uplt.rc["ribbon.nodewidth"] == 0.018
    assert uplt.rc["ribbon.flow.curvature"] == 0.45
    assert uplt.rc["ribbon.flow.alpha"] == 0.58
    assert uplt.rc["ribbon.topic_labels"] is True
    assert uplt.rc["ribbon.topic_label_offset"] == 0.028
    assert uplt.rc["ribbon.topic_label_size"] == 7.4
    assert uplt.rc["ribbon.topic_label_box"] is True


import io
from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, patch

from ultraplot.utils import check_for_update


@patch("builtins.print")
@patch("importlib.metadata.version")
def test_package_not_installed(mock_version, mock_print):
    mock_version.side_effect = PackageNotFoundError
    check_for_update("fakepkg")
    mock_print.assert_not_called()


@patch("builtins.print")
@patch("importlib.metadata.version", return_value="1.0.0")
@patch("urllib.request.urlopen")
def test_network_failure(mock_urlopen, mock_version, mock_print):
    mock_urlopen.side_effect = Exception("Network down")
    check_for_update("fakepkg")
    mock_print.assert_not_called()


@patch("builtins.print")
@patch("importlib.metadata.version", return_value="1.0.0")
@patch("urllib.request.urlopen")
def test_no_update_available(mock_urlopen, mock_version, mock_print):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = io.StringIO('{"info": {"version": "1.0.0"}}')
    mock_urlopen.return_value = mock_resp

    check_for_update("fakepkg")
    mock_print.assert_not_called()


@patch("builtins.print")
@patch("importlib.metadata.version", return_value="1.0.0")
@patch("urllib.request.urlopen")
def test_update_available(mock_urlopen, mock_version, mock_print):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = io.StringIO('{"info": {"version": "1.2.0"}}')
    mock_urlopen.return_value = mock_resp

    check_for_update("fakepkg")
    mock_print.assert_called_once()
    msg = mock_print.call_args[0][0]
    assert "A newer version of fakepkg is available" in msg
    assert "1.0.0 → 1.2.0" in msg


@patch("builtins.print")
@patch("importlib.metadata.version", return_value="1.0.0dev")
@patch("urllib.request.urlopen")
def test_dev_version_skipped(mock_urlopen, mock_version, mock_print):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = io.StringIO('{"info": {"version": "2.0.0"}}')
    mock_urlopen.return_value = mock_resp

    check_for_update("fakepkg")
    mock_print.assert_not_called()


@pytest.mark.parametrize(
    "cycle, raises_error",
    [
        ("qual1", False),
        (["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"], False),
        (
            uplt.constructor.Cycle(
                ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]
            ),
            False,
        ),
        (uplt.colormaps.get_cmap("viridis"), False),
        (1234, True),
    ],
)
def test_cycle_rc_setting(cycle, raises_error):
    """
    Test various ways to set the cycle in rc
    """
    if raises_error:
        with pytest.raises(ValueError):
            uplt.rc["cycle"] = cycle
    else:
        uplt.rc["cycle"] = cycle


def test_cycle_consistent_across_threads():
    """
    Sanity check: concurrent reads of the prop cycle should be consistent.
    """
    import matplotlib as mpl

    expected = repr(mpl.rcParams["axes.prop_cycle"])
    q = Queue()
    start = threading.Barrier(4)

    def _read_cycle():
        start.wait()
        q.put(repr(mpl.rcParams["axes.prop_cycle"]))

    threads = [threading.Thread(target=_read_cycle) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    results = [q.get() for _ in threads]
    assert all(result == expected for result in results)


def test_cycle_mutation_does_not_corrupt_rcparams():
    """
    Stress test: concurrent cycle mutations should not corrupt rcParams.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    cycle_a = "colorblind"
    cycle_b = "default"
    plt.switch_backend("Agg")
    uplt.rc["cycle"] = cycle_a
    expected_a = repr(mpl.rcParams["axes.prop_cycle"])
    uplt.rc["cycle"] = cycle_b
    expected_b = repr(mpl.rcParams["axes.prop_cycle"])
    allowed = {expected_a, expected_b}

    start = threading.Barrier(2)
    done = threading.Event()
    results = Queue()

    def _writer():
        start.wait()
        for _ in range(200):
            uplt.rc["cycle"] = cycle_a
            uplt.rc["cycle"] = cycle_b
        done.set()

    def _reader():
        start.wait()
        while not done.is_set():
            results.put(repr(mpl.rcParams["axes.prop_cycle"]))
            fig, ax = uplt.subplots()
            ax.plot([0, 1], [0, 1])
            fig.canvas.draw()
            uplt.close(fig)

    threads = [
        threading.Thread(target=_writer),
        threading.Thread(target=_reader),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    observed = [results.get() for _ in range(results.qsize())]
    assert observed, "No rcParams observations were recorded."
    assert all(value in allowed for value in observed)


def _run_in_subprocess(code, *, cwd=None, env=None):
    root = pathlib.Path(__file__).resolve().parents[2]
    code = f"import sys\nsys.path.insert(0, {str(root)!r})\n" + code
    env = {**os.environ, **(env or {})}
    env["MPLBACKEND"] = "Agg"
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(cwd or root),
        env=env,
    )


@pytest.mark.parametrize("location", ["user", "local"])
@pytest.mark.parametrize("custom", [False, True])
@pytest.mark.parametrize("overrides", [False, True])
def test_startup_cycle_applies_to_first_plot(tmp_path, location, custom, overrides):
    """Startup rc files must synchronize the cycle before the first axes exists."""
    home = tmp_path / "home"
    work = tmp_path / "work"
    home.mkdir()
    work.mkdir()
    (tmp_path / "config").mkdir()
    cycle = "startup_test" if custom else "qual1"
    expected = (
        ["#123456", "#abcdef"]
        if custom
        else ["#5bbe94", "#91be64", "#e5cf6c", "#e87b70"]
    )
    folder = home if location == "user" else work
    content = f"cycle: {cycle}\nultraplot.check_for_latest_version: False\n"
    if overrides:
        content += (
            "axes.prop_cycle: cycler('color', ['red', 'blue'])\n"
            "patch.facecolor: green\n"
        )
    (folder / ".ultraplotrc").write_text(content)
    if custom:
        cycles = (
            home / ".ultraplot" / "cycles"
            if location == "user"
            else work / "ultraplot_cycles"
        )
        cycles.mkdir(parents=True)
        (cycles / f"{cycle}.hex").write_text(", ".join(expected) + "\n")
    if overrides:
        expected = ["#ff0000", "#0000ff"]
    result = _run_in_subprocess(
        "import matplotlib as mpl\n"
        "from matplotlib.colors import to_hex\n"
        "import ultraplot as uplt\n"
        f"assert uplt.rc.cycle == {cycle!r}\n"
        f"expected = {expected!r}\n"
        "actual = [to_hex(c) for c in mpl.rcParams['axes.prop_cycle'].by_key()['color']]\n"
        "assert actual[:len(expected)] == expected, actual\n"
        + (
            "assert to_hex(mpl.rcParams['patch.facecolor']) == '#008000'\n"
            if overrides
            else ""
        )
        + "fig, ax = uplt.subplots()\n"
        "lines = ax.plot([[i] * len(expected) for i in range(3)])\n"
        "actual = [to_hex(line.get_color()) for line in lines]\n"
        "assert actual == expected, actual\n"
        "uplt.close(fig)\n",
        cwd=work,
        env={
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "MPLCONFIGDIR": str(tmp_path / "mpl"),
        },
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "statement",
    [
        "from ultraplot.config import rc",
        "import ultraplot.config as config; rc = config.rc",
        "import ultraplot.colors; from ultraplot.config import rc",
        "import ultraplot.ticker; from ultraplot.config import rc",
        "from ultraplot.constructor import Cycle; "
        "assert len(Cycle('qual1')) > 0; from ultraplot.config import rc",
        "import ultraplot.scale; from ultraplot.config import rc",
        "from ultraplot.config import rc_matplotlib, rc_ultraplot; "
        "assert rc_matplotlib['font.size'] == 23; "
        "assert rc_ultraplot['cycle'] == 'qual1'; "
        "rc_matplotlib['font.size'] = 31; "
        "import ultraplot as uplt; uplt.setup(eager=False); "
        "assert rc_matplotlib['font.size'] == 31; "
        "rc_matplotlib['font.size'] = 23; from ultraplot.config import rc",
    ],
)
def test_direct_config_import_initializes_once(tmp_path, statement):
    """Direct imports load rc files and later setup preserves user changes."""
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / ".ultraplotrc").write_text(
        "cycle: qual1\nfont.size: 23\nultraplot.check_for_latest_version: False\n"
    )
    result = _run_in_subprocess(
        statement + "\n"
        "import matplotlib as mpl\n"
        "from matplotlib.colors import to_hex\n"
        "assert rc.cycle == 'qual1', rc.cycle\n"
        "import ultraplot.config as config\n"
        "assert 'rc' in dir(config)\n"
        "assert rc['font.size'] == 23, rc['font.size']\n"
        "assert to_hex(mpl.rcParams['axes.prop_cycle'].by_key()['color'][0]) == '#5bbe94'\n"
        "rc['font.size'] = 31\n"
        "rc.cycle = 'colorblind'\n"
        "import ultraplot as uplt\n"
        "uplt.setup(eager=False)\n"
        "uplt.setup(eager=False)\n"
        "assert uplt.rc is rc\n"
        "assert rc['font.size'] == 31, rc['font.size']\n"
        "assert rc.cycle == 'colorblind', rc.cycle\n",
        cwd=tmp_path,
        env={
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "MPLCONFIGDIR": str(tmp_path / "mpl"),
        },
    )
    assert result.returncode == 0, result.stderr


def test_matplotlib_import_before_ultraplot_allows_rc_mutation():
    """
    Import order regression test for issue #568.
    """
    result = _run_in_subprocess(
        "import matplotlib.pyplot as plt\n"
        "import ultraplot as uplt\n"
        "uplt.rc['figure.facecolor'] = 'white'\n"
    )
    assert result.returncode == 0, result.stderr


def test_matplotlib_import_before_ultraplot_allows_custom_fontsize_tokens():
    """
    Ensure patched fontsize validators are active regardless of import order.
    """
    result = _run_in_subprocess(
        "import matplotlib.pyplot as plt\n"
        "import ultraplot as uplt\n"
        "for key in ('axes.titlesize', 'figure.titlesize', 'legend.fontsize', 'xtick.labelsize'):\n"
        "    uplt.rc[key] = 'med-large'\n"
    )
    assert result.returncode == 0, result.stderr
