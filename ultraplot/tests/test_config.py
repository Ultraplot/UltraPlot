import importlib
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
<<<<<<< HEAD


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
