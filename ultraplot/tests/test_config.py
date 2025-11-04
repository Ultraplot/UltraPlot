import importlib
import threading
import time

import pytest

import ultraplot as uplt


def test_wrong_keyword_reset():
    """
    The context should reset after a failed attempt.
    """
    # Use context manager for temporary rc changes
    # Use context manager with direct value setting
    with uplt.rc.context(coastcolor="black"):
        # Set a wrong key
        with pytest.raises(KeyError):
            uplt.rc._get_item_dicts("non_existing_key", "non_existing_value")
        # Confirm we can still plot
        fig, ax = uplt.subplots(proj="cyl")
        ax.format(coastcolor="black")
        fig.canvas.draw()


def test_cycle_in_rc_file(tmp_path):
    """
    Test that loading an rc file correctly overwrites the cycle setting.
    """
    rc = uplt.config.Configurator()
    rc_content = "cycle: colorblind"
    rc_file = tmp_path / "test.rc"
    rc_file.write_text(rc_content)
    rc.load(str(rc_file))
    assert rc["cycle"] == "colorblind"


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


# Helper functions for parameterized thread-safety test
def _setup_ultraplot_rcparams():
    """Create a new _RcParams instance for testing."""
    from ultraplot.internals.rcsetup import _RcParams

    base_keys = {f"base_key_{i}": f"base_value_{i}" for i in range(3)}
    validators = {k: lambda x: x for k in base_keys}
    return _RcParams(base_keys, validators)


def _setup_matplotlib_rcparams():
    """Get the rc_matplotlib wrapper."""
    from ultraplot.config import rc_matplotlib

    return rc_matplotlib


def _ultraplot_thread_keys(thread_id):
    """Generate thread-specific keys for ultraplot (custom keys allowed)."""
    return (
        f"thread_{thread_id}_key",  # key
        f"initial_{thread_id}",  # initial_value
        lambda i: f"thread_{thread_id}_value_{i}",  # value_fn
    )


def _matplotlib_thread_keys(thread_id):
    """Generate thread-specific keys for matplotlib (must use valid keys)."""
    return (
        "font.size",  # key - must be valid matplotlib param
        10 + thread_id * 2,  # initial_value - unique per thread
        lambda i: 10 + thread_id * 2,  # value_fn - same value in loop
    )


def _ultraplot_base_keys_check(rc_params):
    """Return list of base keys to verify for ultraplot."""
    return [(f"base_key_{i % 3}", f"base_value_{i % 3}") for i in range(20)]


def _matplotlib_base_keys_check(rc_matplotlib):
    """Return list of base keys to verify for matplotlib."""
    return [("font.size", rc_matplotlib["font.size"])]


def _ultraplot_global_test(rc_params):
    """Return test key/value for global change test (ultraplot)."""
    return (
        "global_test_key",  # key
        "global_value",  # value
        lambda: None,  # cleanup_fn - no cleanup needed
    )


def _matplotlib_global_test(rc_matplotlib):
    """Return test key/value for global change test (matplotlib)."""
    original_value = rc_matplotlib._rcparams["font.size"]
    return (
        "font.size",  # key
        99,  # value
        lambda: rc_matplotlib.__setitem__("font.size", original_value),  # cleanup_fn
    )


@pytest.mark.parametrize(
    "rc_type,setup_fn,thread_keys_fn,base_keys_fn,global_test_fn",
    [
        (
            "ultraplot",
            _setup_ultraplot_rcparams,
            _ultraplot_thread_keys,
            _ultraplot_base_keys_check,
            _ultraplot_global_test,
        ),
        (
            "matplotlib",
            _setup_matplotlib_rcparams,
            _matplotlib_thread_keys,
            _matplotlib_base_keys_check,
            _matplotlib_global_test,
        ),
    ],
)
def test_rcparams_thread_safety(
    rc_type, setup_fn, thread_keys_fn, base_keys_fn, global_test_fn
):
    """
    Test that rcParams (both _RcParams and rc_matplotlib) are thread-safe with thread-local isolation.

    This parameterized test verifies thread-safety for both ultraplot's _RcParams and matplotlib's
    rc_matplotlib wrapper. The key difference is that _RcParams allows custom keys while rc_matplotlib
    must use valid matplotlib parameter keys.

    Thread-local changes inside context managers are isolated and don't persist.
    Changes outside context managers are global and persistent.

    Parameters
    ----------
    rc_type : str
        Either "ultraplot" or "matplotlib" to identify which rcParams is being tested
    setup_data : callable
        Function that returns the rc_params object to test
    thread_keys_fn : callable
        Function that takes thread_id and returns (key, initial_value, value_fn)
        - For ultraplot: custom keys like "thread_0_key"
        - For matplotlib: valid keys like "font.size"
    base_keys_check_fn : callable
        Function that returns list of (key, expected_value) tuples to verify
    global_test_fn : callable
        Function that returns (key, value, cleanup_fn) for testing global changes
    """
    # Setup rc_params object
    rc_params = setup_fn()

    # Store original values for base keys (before any modifications)
    if rc_type == "matplotlib":
        original_values = {key: rc_params[key] for key, _ in base_keys_fn(rc_params)}
    else:
        original_values = {f"base_key_{i}": f"base_value_{i}" for i in range(3)}

    # Number of threads and operations per thread
    num_threads = 5
    operations_per_thread = 20

    # Track successful thread completions
    thread_success = {}

    def worker(thread_id):
        """Thread function that makes thread-local changes that don't persist."""
        thread_key, initial_value, value_fn = thread_keys_fn(thread_id)

        try:
            # Use context manager for thread-local changes
            with rc_params:
                # Initialize the key with a base value (thread-local)
                rc_params[thread_key] = initial_value

                # Perform operations
                for i in range(operations_per_thread):
                    # Update with new value (thread-local)
                    new_value = value_fn(i)
                    rc_params[thread_key] = new_value

                    # Verify the update worked within this thread
                    assert rc_params[thread_key] == new_value

                    # Also read some base keys to test mixed access
                    if i % 5 == 0:
                        base_key, expected_value = base_keys_fn(rc_params)[0]
                        base_value = rc_params[base_key]
                        assert isinstance(base_value, (str, int, float, list))
                        if rc_type == "ultraplot":
                            assert base_value == expected_value

                    # Small delay for matplotlib to increase chance of race conditions
                    if rc_type == "matplotlib":
                        time.sleep(0.001)

            # After exiting context, thread-local changes should be gone
            if rc_type == "ultraplot":
                # For ultraplot, custom keys should not exist
                assert (
                    thread_key not in rc_params
                ), f"Thread {thread_id}'s key persisted (should be thread-local only)"
            else:
                # For matplotlib, value should revert to original
                assert (
                    rc_params[thread_key] == original_values[thread_key]
                ), f"Thread {thread_id}'s change persisted (should be thread-local only)"

            thread_success[thread_id] = True

        except Exception as e:
            thread_success[thread_id] = False
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

    # Verify all threads completed successfully
    for thread_id in range(num_threads):
        assert thread_success.get(
            thread_id, False
        ), f"Thread {thread_id} did not complete successfully"

    # Verify base keys are still intact and unchanged
    for key, expected_value in base_keys.items():
        assert key in rc_params, f"Base key {key} was lost"
        assert rc_params[key] == expected_value, f"Base key {key} value was corrupted"

    # Verify that ONLY base keys exist (no thread keys should persist)
    assert len(rc_params) == len(
        base_keys
    ), f"Expected {len(base_keys)} keys, found {len(rc_params)}"

    # Test that global changes (outside context) DO persist
    test_key = "global_test_key"
    rc_params[test_key] = "global_value"
    assert test_key in rc_params
    assert rc_params[test_key] == "global_value"


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
            with uplt.rc.context(cycle=cycle):
                pass
    else:
        with uplt.rc.context(cycle=cycle):
            pass


def test_rc_check_key():
    """
    Test the _check_key method in _RcParams
    """
    from ultraplot.internals.rcsetup import _RcParams

    # Create a test instance
    rc_params = _RcParams({"test_key": "test_value"}, {"test_key": lambda x: x})

    # Test valid key
    key, value = rc_params._check_key("test_key", "new_value")
    assert key == "test_key"
    assert value == "new_value"

    # Test new key (should be registered with default validator)
    key, value = rc_params._check_key("new_key", "new_value")
    assert key == "new_key"
    assert value == "new_value"
    assert "new_key" in rc_params._validate


def test_rc_repr():
    """
    Test the __repr__ method in _RcParams
    """
    from ultraplot.internals.rcsetup import _RcParams

    # Create a test instance
    rc_params = _RcParams({"test_key": "test_value"}, {"test_key": lambda x: x})

    # Test __repr__
    repr_str = repr(rc_params)
    assert "RcParams" in repr_str
    assert "test_key" in repr_str


def test_rc_validators():
    """
    Test validators in _RcParams
    """
    from ultraplot.internals.rcsetup import _RcParams

    # Create a test instance with various validators
    validators = {
        "int_val": lambda x: int(x),
        "float_val": lambda x: float(x),
        "str_val": lambda x: str(x),
    }
    rc_params = _RcParams(
        {"int_val": 1, "float_val": 1.0, "str_val": "test"}, validators
    )

    # Test valid values
    rc_params["int_val"] = 2
    assert rc_params["int_val"] == 2

    rc_params["float_val"] = 2.5
    assert rc_params["float_val"] == 2.5

    rc_params["str_val"] = "new_value"
    assert rc_params["str_val"] == "new_value"

    # Test invalid values
    with pytest.raises(ValueError):
        rc_params["int_val"] = "not_an_int"

    with pytest.raises(ValueError):
        rc_params["float_val"] = "not_a_float"
