import pytest
import ultraplot as uplt


def test_handler_override():
    """
    Test that a handler can be overridden and is executed when the setting is changed.
    """
    # Get the original handler to restore it later
    original_handler = uplt.rc._setting_handlers.get("cycle")

    # Define a dummy handler
    _handler_was_called = False

    def dummy_handler(value):
        nonlocal _handler_was_called
        _handler_was_called = True
        return {}

    # Register the dummy handler, overriding the original one
    uplt.rc.register_handler("cycle", dummy_handler)

    try:
        # Change the setting to trigger the handler
        uplt.rc["cycle"] = "colorblind"

        # Assert that our dummy handler was called
        assert _handler_was_called, "Dummy handler was not called."

    finally:
        # Restore the original handler
        if original_handler:
            uplt.rc.register_handler("cycle", original_handler)
        else:
            del uplt.rc._setting_handlers["cycle"]
