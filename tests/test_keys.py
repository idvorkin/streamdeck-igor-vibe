"""Tests for keys.py CLI."""

from unittest.mock import patch

from typer.testing import CliRunner

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from keys import app, send_keys


runner = CliRunner()


def test_help_shows_all_commands():
    """CLI should show help with all commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "previous-pane" in result.output
    assert "next-pane" in result.output
    assert "voice" in result.output
    assert "custom" in result.output


@patch("keys.subprocess.run")
def test_previous_pane_sends_control_p(mock_run):
    """previous-pane should send Control+P."""
    result = runner.invoke(app, ["previous-pane"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "osascript"
    assert "keystroke" in call_args[2]
    assert '"p"' in call_args[2]
    assert "control down" in call_args[2]


@patch("keys.subprocess.run")
def test_next_pane_sends_control_a(mock_run):
    """next-pane should send Control+A."""
    result = runner.invoke(app, ["next-pane"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "keystroke" in call_args[2]
    assert '"a"' in call_args[2]
    assert "control down" in call_args[2]


@patch("keys.subprocess.run")
def test_voice_sends_command_shift_space(mock_run):
    """voice should send Command+Shift+Space."""
    result = runner.invoke(app, ["voice"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "keystroke" in call_args[2]
    assert '" "' in call_args[2]
    assert "command down" in call_args[2]
    assert "shift down" in call_args[2]


@patch("keys.subprocess.run")
def test_custom_with_modifiers(mock_run):
    """custom should send specified key with modifiers."""
    result = runner.invoke(app, ["custom", "x", "--control", "--shift"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert '"x"' in call_args[2]
    assert "control down" in call_args[2]
    assert "shift down" in call_args[2]


@patch("keys.subprocess.run")
def test_custom_without_modifiers(mock_run):
    """custom without modifiers should send just the key."""
    result = runner.invoke(app, ["custom", "z"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert '"z"' in call_args[2]
    # No modifiers means no "using" clause with "down"
    assert "using" not in call_args[2]


def test_send_keys_builds_correct_applescript():
    """send_keys should build correct AppleScript command."""
    with patch("keys.subprocess.run") as mock_run:
        send_keys("a", ["control", "command"])
        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert 'tell application "System Events"' in script
        assert 'keystroke "a"' in script
        assert "control down" in script
        assert "command down" in script
