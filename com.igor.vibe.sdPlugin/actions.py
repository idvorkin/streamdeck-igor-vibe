"""
Hot-reloadable action handlers for Stream Deck plugin.
Edit this file and press the Reload button to apply changes.
"""

import json
import socket
import subprocess
import time
from pathlib import Path

# Voice cycle state: tracks press count for voice→voice→enter cycle
_voice_cycle_count = 0
_voice_cycle_action = "com.igor.vibe.voicecycle"


def get_config():
    """Load config from config.json."""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            log(f"ERROR: Invalid JSON in config.json: {e}")
            return {}
    return {}


def get_voice_modifier():
    """Get voice modifier key based on machine name."""
    config = get_config()
    voice_config = config.get("voice_modifier", {})
    hostname = socket.gethostname()
    modifier = voice_config.get(hostname, voice_config.get("default", "command"))
    if modifier not in ("command", "control"):
        log(f"WARNING: Invalid modifier '{modifier}', falling back to 'command'")
        return "command"
    return modifier

# App bundle identifiers
TERMINAL_APPS = {
    "com.mitchellh.ghostty",
    "com.googlecode.iterm2",
    "com.apple.Terminal",
}
BROWSER_APPS = {
    "com.microsoft.Edge",
    "com.microsoft.edgemac",
    "com.google.Chrome",
    "org.mozilla.firefox",
    "com.apple.Safari",
}


def log(msg: str):
    """Import log from plugin at runtime."""
    from plugin import log as plugin_log
    plugin_log(msg)


def get_frontmost_app() -> str:
    """Get the bundle identifier of the frontmost application."""
    script = 'tell application "System Events" to get bundle identifier of first process whose frontmost is true'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR getting frontmost app: {result.stderr}")
        return ""
    bundle_id = result.stdout.strip()
    log(f"Frontmost app: {bundle_id}")
    return bundle_id


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
        log("Keys sent successfully")


def send_key_code(key_code: int, modifiers: list[str] | None = None):
    """Send key code with modifiers using AppleScript."""
    modifiers = modifiers or []
    modifier_map = {
        "control": "control down",
        "command": "command down",
        "shift": "shift down",
        "option": "option down",
    }
    modifier_str = ", ".join(modifier_map[m] for m in modifiers if m in modifier_map)

    if modifier_str:
        script = f'tell application "System Events" to key code {key_code} using {{{modifier_str}}}'
    else:
        script = f'tell application "System Events" to key code {key_code}'

    log(f"Sending key code: {script}")
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: osascript failed: {result.stderr}")
    else:
        log("Key code sent successfully")


def do_previous_pane():
    """Previous pane/tab - app-aware. Defaults to terminal behavior for unknown apps."""
    app = get_frontmost_app()
    if app in BROWSER_APPS:
        log(f"ACTION: Previous Tab (Cmd+Shift+[) - browser: {app}")
        send_key_code(33, ["command", "shift"])  # [ key
    elif app in TERMINAL_APPS:
        log(f"ACTION: Previous Pane (Ctrl+A, p) - terminal: {app}")
        send_keys("a", ["control"])
        time.sleep(0.05)
        send_keys("p")
    else:
        log(f"ACTION: Previous Pane (Ctrl+A, p) - unknown app '{app}', using terminal behavior")
        send_keys("a", ["control"])
        time.sleep(0.05)
        send_keys("p")


def do_next_pane():
    """Next pane/tab - app-aware. Defaults to terminal behavior for unknown apps."""
    app = get_frontmost_app()
    if app in BROWSER_APPS:
        log(f"ACTION: Next Tab (Cmd+Shift+]) - browser: {app}")
        send_key_code(30, ["command", "shift"])  # ] key
    elif app in TERMINAL_APPS:
        log(f"ACTION: Next Pane (Ctrl+A, n) - terminal: {app}")
        send_keys("a", ["control"])
        time.sleep(0.05)
        send_keys("n")
    else:
        log(f"ACTION: Next Pane (Ctrl+A, n) - unknown app '{app}', using terminal behavior")
        send_keys("a", ["control"])
        time.sleep(0.05)
        send_keys("n")


def do_voice():
    modifier = get_voice_modifier()
    # Key codes: Right Command = 54, Right Control = 62, Right Shift = 60
    modifier_key = 54 if modifier == "command" else 62
    modifier_name = "Command" if modifier == "command" else "Control"
    log(f"ACTION: Voice (Right {modifier_name} + Right Shift)")
    code = f'''
import Quartz
MODIFIER_KEY = {modifier_key}
RIGHT_SHIFT = 60
source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
mod_down = Quartz.CGEventCreateKeyboardEvent(source, MODIFIER_KEY, True)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, mod_down)
shift_down = Quartz.CGEventCreateKeyboardEvent(source, RIGHT_SHIFT, True)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_down)
shift_up = Quartz.CGEventCreateKeyboardEvent(source, RIGHT_SHIFT, False)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_up)
mod_up = Quartz.CGEventCreateKeyboardEvent(source, MODIFIER_KEY, False)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, mod_up)
'''
    result = subprocess.run(
        ["/opt/homebrew/bin/uv", "run", "--with", "pyobjc-framework-Quartz", "python3", "-c", code],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log(f"Right {modifier_name}+Shift sent successfully")


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


def do_edge():
    log("ACTION: Open Microsoft Edge")
    script = 'tell application "Microsoft Edge" to activate'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log("Edge opened")


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


def do_pane(number: int):
    """Switch to tmux pane by number (Ctrl+A, number)."""
    log(f"ACTION: Pane {number} (Ctrl+A, {number})")
    send_keys("a", ["control"])
    time.sleep(0.05)
    send_keys(str(number))


def do_pane1():
    do_pane(1)


def do_pane2():
    do_pane(2)


def do_pane3():
    do_pane(3)


def do_pane4():
    do_pane(4)


def do_pane5():
    do_pane(5)


def do_pane6():
    do_pane(6)


def do_pane7():
    do_pane(7)


def do_pane8():
    do_pane(8)


def do_pane9():
    do_pane(9)


def do_reload():
    """Reload - app-aware. Browser: refresh page. Terminal: hot-reload actions.py."""
    app = get_frontmost_app()
    if app in BROWSER_APPS:
        log(f"ACTION: Refresh Page (Cmd+R) - browser: {app}")
        send_keys("r", ["command"])
    elif app in TERMINAL_APPS:
        log(f"ACTION: Hot-reload actions.py - terminal: {app}")
        from plugin import load_actions
        if load_actions():
            log("Actions reloaded successfully!")
        else:
            log("Failed to reload actions")
    else:
        log(f"ACTION: Reload - no action for app: {app}")


def _update_voice_cycle_icon():
    """Update the voice cycle button icon based on current state."""
    global _voice_cycle_count
    from plugin import update_button_image

    # Icon names: voicecycle1, voicecycle2, voicecycle3 (for enter)
    icon_num = (_voice_cycle_count % 3) + 1
    icon_name = f"voicecycle{icon_num}"
    log(f"Updating voice cycle icon to {icon_name} (count={_voice_cycle_count})")
    update_button_image(_voice_cycle_action, icon_name)


def do_voice_cycle():
    """Smart voice button: voice → voice → enter, then repeat."""
    global _voice_cycle_count

    cycle_pos = _voice_cycle_count % 3

    if cycle_pos < 2:
        # First two presses: trigger voice
        log(f"ACTION: Voice Cycle - voice (press {cycle_pos + 1}/3)")
        do_voice()
    else:
        # Third press: enter
        log(f"ACTION: Voice Cycle - enter (press 3/3)")
        do_enter()

    _voice_cycle_count += 1
    _update_voice_cycle_icon()


def on_any_button_press(action: str):
    """Called before any button action - resets voice cycle if different button pressed."""
    global _voice_cycle_count

    if action != _voice_cycle_action and _voice_cycle_count > 0:
        log(f"Voice cycle reset (interrupted by {action})")
        _voice_cycle_count = 0
        _update_voice_cycle_icon()


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
    "com.igor.vibe.edge": do_edge,
    "com.igor.vibe.fullscreen": do_fullscreen,
    "com.igor.vibe.ctrlc": do_ctrlc,
    "com.igor.vibe.reload": do_reload,
    "com.igor.vibe.pane1": do_pane1,
    "com.igor.vibe.pane2": do_pane2,
    "com.igor.vibe.pane3": do_pane3,
    "com.igor.vibe.pane4": do_pane4,
    "com.igor.vibe.pane5": do_pane5,
    "com.igor.vibe.pane6": do_pane6,
    "com.igor.vibe.pane7": do_pane7,
    "com.igor.vibe.pane8": do_pane8,
    "com.igor.vibe.pane9": do_pane9,
    "com.igor.vibe.voicecycle": do_voice_cycle,
}
