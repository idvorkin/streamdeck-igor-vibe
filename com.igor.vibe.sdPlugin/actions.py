"""
Hot-reloadable action handlers for Stream Deck plugin.
Edit this file and press the Reload button to apply changes.
"""

import subprocess
import time

def log(msg: str):
    """Import log from plugin at runtime."""
    from plugin import log as plugin_log
    plugin_log(msg)


def send_keys(keys: str, modifiers: list[str] | None = None):
    """Send key combination using AppleScript."""
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

    log(f"Sending keys: {script}")
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: osascript failed: {result.stderr}")
    else:
        log(f"Keys sent successfully")


def do_previous_pane():
    log("ACTION: Previous Pane (Ctrl+A, p)")
    send_keys("a", ["control"])
    time.sleep(0.05)  # Allow tmux to process prefix
    send_keys("p")


def do_next_pane():
    log("ACTION: Next Pane (Ctrl+A, n)")
    send_keys("a", ["control"])
    time.sleep(0.05)  # Allow tmux to process prefix
    send_keys("n")


def do_voice():
    log("ACTION: Voice (Right Command + Right Shift)")
    code = '''
import Quartz
RIGHT_COMMAND = 54
RIGHT_SHIFT = 60
source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
cmd_down = Quartz.CGEventCreateKeyboardEvent(source, RIGHT_COMMAND, True)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_down)
shift_down = Quartz.CGEventCreateKeyboardEvent(source, RIGHT_SHIFT, True)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_down)
shift_up = Quartz.CGEventCreateKeyboardEvent(source, RIGHT_SHIFT, False)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_up)
cmd_up = Quartz.CGEventCreateKeyboardEvent(source, RIGHT_COMMAND, False)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_up)
'''
    result = subprocess.run(
        ["/opt/homebrew/bin/uv", "run", "--with", "pyobjc-framework-Quartz", "python3", "-c", code],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log("Right Cmd+Shift sent successfully")


def do_enter():
    log("ACTION: Enter")
    send_keys("\r")


def do_tab():
    log("ACTION: Tab")
    send_keys("\t")


def do_escape():
    log("ACTION: Escape")
    script = 'tell application "System Events" to key code 53'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log("Escape sent successfully")


def do_ghostty():
    log("ACTION: Open Ghostty")
    script = 'tell application "Ghostty" to activate'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log("Ghostty opened")


def do_iterm():
    log("ACTION: Open iTerm")
    script = 'tell application "iTerm" to activate'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log("iTerm opened")


def do_fullscreen():
    log("ACTION: Toggle Fullscreen (Option+Enter)")
    script = 'tell application "System Events" to key code 36 using {option down}'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log("Fullscreen toggled")


def do_ctrlc():
    log("ACTION: Ctrl+C")
    send_keys("c", ["control"])


# Map action UUIDs to functions
ACTIONS = {
    "com.igor.vibe.previouspane": do_previous_pane,
    "com.igor.vibe.nextpane": do_next_pane,
    "com.igor.vibe.voice": do_voice,
    "com.igor.vibe.enter": do_enter,
    "com.igor.vibe.tab": do_tab,
    "com.igor.vibe.escape": do_escape,
    "com.igor.vibe.ghostty": do_ghostty,
    "com.igor.vibe.iterm": do_iterm,
    "com.igor.vibe.fullscreen": do_fullscreen,
    "com.igor.vibe.ctrlc": do_ctrlc,
}
