import ultraplot as uplt, pytest
import importlib
import threading
import time


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


import io
from unittest.mock import patch, MagicMock
from importlib.metadata import PackageNotFoundError
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


def test_rcparams_thread_safety():
    """
    Test that _RcParams is thread-safe when accessed concurrently.
    Each thread works with its own unique key to verify proper isolation.
    Thread-local changes are properly managed with context manager.
    """
    # Create a new _RcParams instance for testing
    from ultraplot.internals.rcsetup import _RcParams

    # Initialize with base keys
    base_keys = {f"base_key_{i}": f"base_value_{i}" for i in range(3)}
    rc_params = _RcParams(base_keys, {k: lambda x: x for k in base_keys})

    # Number of threads and operations per thread
    num_threads = 5
    operations_per_thread = 20

    # Each thread will work with its own unique key
    thread_keys = {}

    def worker(thread_id):
        """Thread function that works with its own unique key using context manager."""
        # Each thread gets its own unique key
        thread_key = f"thread_{thread_id}_key"
        thread_keys[thread_id] = thread_key

        # Use context manager to ensure proper thread-local cleanup
        with rc_params:
            # Initialize the key with a base value
            rc_params[thread_key] = f"initial_{thread_id}"

            # Perform operations
            for i in range(operations_per_thread):
                try:
                    # Read the current value
                    current = rc_params[thread_key]

                    # Update with new value
                    new_value = f"thread_{thread_id}_value_{i}"
                    rc_params[thread_key] = new_value

                    # Verify the update worked
                    assert rc_params[thread_key] == new_value

                    # Also read some base keys to test mixed access
                    if i % 5 == 0:
                        base_key = f"base_key_{i % 3}"
                        base_value = rc_params[base_key]
                        assert isinstance(base_value, str)

                except Exception as e:
                    raise AssertionError(f"Thread {thread_id} failed: {str(e)}")

    # Create and start threads
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Verify each thread's key exists and has the expected final value
    for thread_id in range(num_threads):
        thread_key = thread_keys[thread_id]
        assert thread_key in rc_params, f"Thread {thread_id}'s key was lost"
        final_value = rc_params[thread_key]
        assert final_value == f"thread_{thread_id}_value_{operations_per_thread - 1}"

    # Verify base keys are still intact
    for key, expected_value in base_keys.items():
        assert key in rc_params, f"Base key {key} was lost"
        assert rc_params[key] == expected_value, f"Base key {key} value was corrupted"

    # Verify that thread-local changes are properly merged
    # Create a copy to verify the copy includes thread-local changes
    rc_copy = rc_params.copy()
    assert len(rc_copy) == len(base_keys) + num_threads, "Copy doesn't include all keys"

    # Verify all keys are in the copy
    for key in base_keys:
        assert key in rc_copy, f"Base key {key} missing from copy"
    for thread_id in range(num_threads):
        thread_key = thread_keys[thread_id]
        assert thread_key in rc_copy, f"Thread {thread_id}'s key missing from copy"


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
