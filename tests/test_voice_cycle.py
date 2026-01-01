"""Tests for voice cycle smart button feature."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add plugin directory to path
plugin_dir = Path(__file__).parent.parent / "com.igor.vibe.sdPlugin"
sys.path.insert(0, str(plugin_dir))

# Mock plugin module before importing actions
sys.modules["plugin"] = MagicMock()


@patch("actions.do_voice")
@patch("actions.do_enter")
@patch("actions.log")
def test_voice_cycle_first_press_triggers_voice(mock_log, mock_enter, mock_voice):
    """First press of voice cycle should trigger voice."""
    import actions
    actions._voice_cycle_count = 0
    actions.do_voice_cycle()

    mock_voice.assert_called_once()
    mock_enter.assert_not_called()
    assert actions._voice_cycle_count == 1


@patch("actions.do_voice")
@patch("actions.do_enter")
@patch("actions.log")
def test_voice_cycle_second_press_triggers_voice(mock_log, mock_enter, mock_voice):
    """Second press of voice cycle should trigger voice."""
    import actions
    actions._voice_cycle_count = 1
    actions.do_voice_cycle()

    mock_voice.assert_called_once()
    mock_enter.assert_not_called()
    assert actions._voice_cycle_count == 2


@patch("actions.do_voice")
@patch("actions.do_enter")
@patch("actions.log")
def test_voice_cycle_third_press_triggers_enter(mock_log, mock_enter, mock_voice):
    """Third press of voice cycle should trigger enter."""
    import actions
    actions._voice_cycle_count = 2
    actions.do_voice_cycle()

    mock_voice.assert_not_called()
    mock_enter.assert_called_once()
    assert actions._voice_cycle_count == 3


@patch("actions.do_voice")
@patch("actions.do_enter")
@patch("actions.log")
def test_voice_cycle_wraps_after_third_press(mock_log, mock_enter, mock_voice):
    """After third press, cycle should wrap back to voice."""
    import actions
    actions._voice_cycle_count = 3
    actions.do_voice_cycle()

    mock_voice.assert_called_once()
    mock_enter.assert_not_called()


@patch("actions.log")
def test_voice_cycle_resets_on_other_button(mock_log):
    """Pressing another button should reset the voice cycle."""
    import actions
    actions._voice_cycle_count = 2
    actions.on_any_button_press("com.igor.vibe.enter")

    assert actions._voice_cycle_count == 0


@patch("actions.log")
def test_voice_cycle_does_not_reset_on_own_press(mock_log):
    """Pressing voice cycle button should not reset itself."""
    import actions
    actions._voice_cycle_count = 2
    actions.on_any_button_press("com.igor.vibe.voicecycle")

    # Should not reset when pressing itself
    assert actions._voice_cycle_count == 2


@patch("actions.log")
def test_voice_cycle_no_reset_when_already_zero(mock_log):
    """No reset needed when count is already zero."""
    import actions
    actions._voice_cycle_count = 0

    # Get the mock for update_button_image from the mocked plugin module
    mock_update = sys.modules["plugin"].update_button_image
    mock_update.reset_mock()

    actions.on_any_button_press("com.igor.vibe.enter")

    # Should not call update_button_image when nothing to reset
    mock_update.assert_not_called()
