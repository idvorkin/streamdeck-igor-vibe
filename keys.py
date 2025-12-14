#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "typer",
#     "rich",
# ]
# ///
"""
Stream Deck key sender for Igor's vibe commands.
Sends keyboard shortcuts on macOS using osascript.
"""

import subprocess

import typer
from rich.console import Console
from rich.panel import Panel
from typing_extensions import Annotated

app = typer.Typer(
    help="Stream Deck key sender for pane navigation and voice",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


def send_keys(keys: str, modifiers: list[str] | None = None):
    """
    Send key combination using AppleScript.

    Args:
        keys: The key to press (e.g., "a", "p")
        modifiers: List of modifiers like "control", "command", "shift", "option"
    """
    modifiers = modifiers or []

    modifier_map = {
        "control": "control down",
        "command": "command down",
        "shift": "shift down",
        "option": "option down",
    }

    modifier_str = ", ".join(modifier_map[m] for m in modifiers if m in modifier_map)

    if modifier_str:
        script = f'tell application "System Events" to keystroke "{keys}" using {{{modifier_str}}}'
    else:
        script = f'tell application "System Events" to keystroke "{keys}"'

    subprocess.run(["osascript", "-e", script], check=True)


@app.command(help="Switch to previous pane")
def previous_pane():
    """Send Control+P for previous pane."""
    send_keys("p", ["control"])
    console.print(Panel("Control+P", title="Previous Pane"))


@app.command(help="Switch to next pane")
def next_pane():
    """Send Control+A for next pane."""
    send_keys("a", ["control"])
    console.print(Panel("Control+A", title="Next Pane"))


@app.command(help="Activate voice input")
def voice():
    """Send Command+Shift+Space for voice activation."""
    send_keys(" ", ["command", "shift"])
    console.print(Panel("Command+Shift+Space", title="Voice"))


@app.command(help="Send a custom key combination")
def custom(
    key: Annotated[str, typer.Argument(help="Key to press")],
    control: Annotated[bool, typer.Option("--control", "-c", help="Add Control modifier")] = False,
    command: Annotated[bool, typer.Option("--command", "-m", help="Add Command modifier")] = False,
    shift: Annotated[bool, typer.Option("--shift", "-s", help="Add Shift modifier")] = False,
    option: Annotated[bool, typer.Option("--option", "-o", help="Add Option modifier")] = False,
):
    """Send a custom key combination with optional modifiers."""
    modifiers = []
    if control:
        modifiers.append("control")
    if command:
        modifiers.append("command")
    if shift:
        modifiers.append("shift")
    if option:
        modifiers.append("option")

    send_keys(key, modifiers)
    mod_str = "+".join(m.title() for m in modifiers)
    if mod_str:
        console.print(Panel(f"{mod_str}+{key}", title="Custom"))
    else:
        console.print(Panel(key, title="Custom"))


if __name__ == "__main__":
    app()
