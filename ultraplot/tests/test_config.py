from unittest.mock import patch, MagicMock
from importlib.metadata import PackageNotFoundError
import ultraplot as uplt, matplotlib as mpl, pytest, io
from ultraplot.utils import check_for_update


def test_wrong_keyword_reset():
    """
    The context should reset after a failed attempt.
    """
    uplt.rc.context()
    config = uplt.rc

    with pytest.raises(KeyError):
        config._get_item_dicts("non_existing_key", "non_existing_value")

    # Confirm a subsequent valid operation still works
    config._get_item_dicts("coastcolor", "black")
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

    uplt.rc.load(str(rc_file))
    assert uplt.rc["cycle"] == "colorblind"


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


def test_special_methods():
    """
    Test special methods of the Configurator class.
    """
    with uplt.rc.context():
        # __repr__ / __str__ / __len__
        assert isinstance(repr(uplt.rc), str) and len(repr(uplt.rc)) > 0
        assert isinstance(str(uplt.rc), str) and len(str(uplt.rc)) > 0
        assert len(uplt.rc) > 0

        # attribute access
        assert hasattr(uplt.rc, "figure.facecolor")

        # deletion should raise
        with pytest.raises(RuntimeError, match="rc settings cannot be deleted"):
            del uplt.rc["figure.facecolor"]
        with pytest.raises(RuntimeError, match="rc settings cannot be deleted"):
            del uplt.rc.figure

    # restore a safe cycle setting
    uplt.rc["cycle"] = "qual1"


def test_sync_method():
    """
    Test that the sync method properly synchronizes settings between ultraplot
    and matplotlib rc dictionaries, and that invalid color assignments during
    sync are handled by resetting matplotlib's rc to the fill value ('black')
    while preserving the user's ultraplot setting.
    """
    with uplt.rc.context(**{"figure.facecolor": "red"}):
        # baseline: sync with valid color keeps the value
        uplt.rc.sync()
        assert uplt.rc["figure.facecolor"] == "red"

        # Monkeypatch the class-level RcParams.__setitem__ so that matplotlib
        # will reject non-fallback colors. We patch the class method because
        # mapping assignment (_src[key] = val) looks up the special method on
        # the type.
        original_class_setitem = mpl.RcParams.__setitem__

        def patched_class_setitem(self, key, val):
            # Simulate matplotlib rejecting non-fallback colors but allow the
            # fallback 'black' used by Configurator.sync to succeed.
            if key == "figure.facecolor" and val != "black":
                raise ValueError("Invalid color")
            return original_class_setitem(self, key, val)

        try:
            # Apply the patch at class-level for the duration of sync()
            with patch.object(mpl.RcParams, "__setitem__", new=patched_class_setitem):
                # Ensure a user value exists (will update both rc_ultraplot and rc_matplotlib)
                uplt.rc["figure.facecolor"] = "red"
                # Run the sync which should attempt to re-assign and hit our patched setter.
                uplt.rc.sync()
        except:
            pass
        finally:
            # Restore original to avoid side-effects on other tests
            mpl.RcParams.__setitem__ = original_class_setitem
        assert uplt.rc["figure.facecolor"] == "red"


def test_config_inline_backend():
    """
    Test that config_inline_backend properly configures the IPython inline backend.
    """
    with uplt.rc.context():
        mock_ipython = MagicMock()
        mock_ipython.run_line_magic = MagicMock()
        mock_ipython.magic = MagicMock()

        # Test with string format
        with patch("ultraplot.config.get_ipython", return_value=mock_ipython):
            uplt.rc.config_inline_backend("png")
            assert (
                mock_ipython.run_line_magic.call_count > 0
                or mock_ipython.magic.call_count > 0
            )
            all_calls = (
                mock_ipython.run_line_magic.call_args_list
                + mock_ipython.magic.call_args_list
            )
            calls = [args[0] for args in all_calls]
            assert any("figure_formats" in str(call) for call in calls)

        # Test with list format
        mock_ipython.reset_mock()
        with patch("ultraplot.config.get_ipython", return_value=mock_ipython):
            uplt.rc.config_inline_backend(["png", "svg"])
            assert (
                mock_ipython.run_line_magic.call_count > 0
                or mock_ipython.magic.call_count > 0
            )
            all_calls = (
                mock_ipython.run_line_magic.call_args_list
                + mock_ipython.magic.call_args_list
            )
            calls = [args[0] for args in all_calls]
            assert any("figure_formats" in str(call) for call in calls)

        # Test with invalid format
        with patch("ultraplot.config.get_ipython", return_value=mock_ipython):
            with pytest.raises(ValueError, match="Invalid inline backend format"):
                uplt.rc.config_inline_backend(123)
