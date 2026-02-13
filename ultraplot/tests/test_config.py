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


def test_curved_quiver_rc_defaults():
    """
    Sanity check curved_quiver defaults in rc.
    """
    assert uplt.rc["curved_quiver.arrowsize"] == 1.0
    assert uplt.rc["curved_quiver.arrowstyle"] == "-|>"
    assert uplt.rc["curved_quiver.scale"] == 1.0
    assert uplt.rc["curved_quiver.grains"] == 15
    assert uplt.rc["curved_quiver.density"] == 10
    assert uplt.rc["curved_quiver.arrows_at_end"] is True


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


def test_rc_registry_merge_disjoint_tables():
    """
    Registry merge should combine disjoint rc tables.
    """
    from ultraplot.internals.rc.registry import merge_rc_tables

    left = {"a.b": (1, lambda x: x, "left")}
    right = {"c.d": (2, lambda x: x, "right")}
    merged = merge_rc_tables(left, right)
    assert merged["a.b"][0] == 1
    assert merged["c.d"][0] == 2


def test_rc_registry_merge_duplicate_keys_raises():
    """
    Registry merge should fail fast on duplicate keys.
    """
    from ultraplot.internals.rc.registry import merge_rc_tables

    table1 = {"a.b": (1, lambda x: x, "first")}
    table2 = {"a.b": (2, lambda x: x, "second")}
    with pytest.raises(ValueError, match="Duplicate rc keys"):
        merge_rc_tables(table1, table2)


def test_rc_settings_table_matches_rcsetup_table():
    """
    Single settings table should match rcsetup composed table keys.
    """
    from ultraplot.internals import rcsetup
    from ultraplot.internals.rc import build_settings_rc_table

    ns = vars(rcsetup)
    settings_table = build_settings_rc_table(ns)
    assert set(settings_table) == set(rcsetup._rc_ultraplot_table)


def test_rc_validator_aliases_include_common_validators():
    """
    Validator aliases should include common primitive validators.
    """
    from ultraplot.internals import rcsetup
    from ultraplot.internals.rc import build_validator_aliases

    aliases = build_validator_aliases(vars(rcsetup))
    assert aliases["float"] is rcsetup._validate_float
    assert aliases["bool"] is rcsetup._validate_bool
    assert aliases["color"] is rcsetup._validate_color


def test_rc_deprecations_module_matches_rcsetup():
    """
    Deprecation maps should be sourced from rc.deprecations.
    """
    from ultraplot.internals import rcsetup
    from ultraplot.internals.rc.deprecations import get_rc_removed, get_rc_renamed

    assert rcsetup._rc_removed == get_rc_removed()
    assert rcsetup._rc_renamed == get_rc_renamed()


def _run_in_subprocess(code):
    code = (
        "import pathlib\n"
        "import sys\n"
        "sys.path.insert(0, str(pathlib.Path.cwd()))\n" + code
    )
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(pathlib.Path(__file__).resolve().parents[2]),
        env=env,
    )


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
