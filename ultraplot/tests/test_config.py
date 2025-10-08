import ultraplot as uplt, pytest
import importlib


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


def test_cycle_in_rc_file(tmp_path, monkeypatch):
    """
    Test that setting the cycle in an rc file does not cause a circular import.
    """
    rc_content = "cycle: colorblind"
    rc_file = tmp_path / ".ultraplotrc"
    rc_file.write_text(rc_content)

    monkeypatch.setattr(uplt.config.Configurator, "user_file", lambda: str(rc_file))

    try:
        # We need to reload ultraplot and its config to trigger the initialization
        # logic that reads the rc file.
        importlib.reload(uplt)
        importlib.reload(uplt.config)
    except ImportError as e:
        pytest.fail(f"Setting 'cycle' in rc file raised an import error: {e}")
    assert uplt.rc["cycle"] == "colorblind"
