"""
Hot-reloadable action handlers for Stream Deck plugin.
Edit this file and press the Reload button to apply changes.
"""

import json
import socket
import subprocess
import time
from pathlib import Path

try:
    import Quartz
except ImportError:
    Quartz = None  # type: ignore[assignment]

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


# macOS virtual key codes
_KEY_CODES = {
    "a": 0, "b": 11, "c": 8, "d": 2, "e": 14, "f": 3, "g": 5, "h": 4,
    "i": 34, "j": 38, "k": 40, "l": 37, "m": 46, "n": 45, "o": 31, "p": 35,
    "q": 12, "r": 15, "s": 1, "t": 17, "u": 32, "v": 9, "w": 13, "x": 7,
    "y": 16, "z": 6,
    "1": 18, "2": 19, "3": 20, "4": 21, "5": 23, "6": 22, "7": 26, "8": 28,
    "9": 25, "0": 29,
    "\r": 36, "\t": 48,
    "escape": 53, "[": 33, "]": 30,
}

# CGEvent modifier flags
_MODIFIER_FLAGS = {
    "control": 0x40000,   # kCGEventFlagMaskControl
    "command": 0x100000,  # kCGEventFlagMaskCommand
    "shift": 0x20000,     # kCGEventFlagMaskShift
    "option": 0x80000,    # kCGEventFlagMaskAlternate
}


def send_keys_hid(keys: str, modifiers: list[str] | None = None):
    """Send key combination using CGEvent (HID level) - bypasses Karabiner."""
    modifiers = modifiers or []
    key_code = _KEY_CODES.get(keys)
    if key_code is None:
        log(f"ERROR: Unknown key '{keys}' for HID send")
        return

    flag_mask = 0
    for m in modifiers:
        if m in _MODIFIER_FLAGS:
            flag_mask |= _MODIFIER_FLAGS[m]
        else:
            log(f"WARNING: Unknown modifier '{m}' in send_keys_hid")

    log(f"Sending HID keys: {keys} modifiers={modifiers}")
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
    event_down = Quartz.CGEventCreateKeyboardEvent(source, key_code, True)
    event_up = Quartz.CGEventCreateKeyboardEvent(source, key_code, False)
    if flag_mask:
        Quartz.CGEventSetFlags(event_down, flag_mask)
        Quartz.CGEventSetFlags(event_up, flag_mask)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
    log("HID keys sent successfully")


def _send_tmux_prefix_then(key: str):
    """Send tmux prefix (Ctrl+A) followed by a key."""
    send_keys_hid("a", ["control"])
    time.sleep(0.05)
    send_keys_hid(key)


def do_previous_pane():
    """Previous pane/tab - app-aware. Defaults to terminal behavior for unknown apps."""
    app = get_frontmost_app()
    if app in BROWSER_APPS:
        log(f"ACTION: Previous Tab (Cmd+Shift+[) - browser: {app}")
        send_keys_hid("[", ["command", "shift"])
    elif app in TERMINAL_APPS:
        log(f"ACTION: Previous Pane (Ctrl+A, p) - terminal: {app}")
        _send_tmux_prefix_then("p")
    else:
        log(f"ACTION: Previous Pane (Ctrl+A, p) - unknown app '{app}', using terminal behavior")
        _send_tmux_prefix_then("p")


def do_next_pane():
    """Next pane/tab - app-aware. Defaults to terminal behavior for unknown apps."""
    app = get_frontmost_app()
    if app in BROWSER_APPS:
        log(f"ACTION: Next Tab (Cmd+Shift+]) - browser: {app}")
        send_keys_hid("]", ["command", "shift"])
    elif app in TERMINAL_APPS:
        log(f"ACTION: Next Pane (Ctrl+A, n) - terminal: {app}")
        _send_tmux_prefix_then("n")
    else:
        log(f"ACTION: Next Pane (Ctrl+A, n) - unknown app '{app}', using terminal behavior")
        _send_tmux_prefix_then("n")


def do_voice():
    modifier = get_voice_modifier()
    # Key codes: Right Command = 54, Right Control = 62, Right Shift = 60
    modifier_key = 54 if modifier == "command" else 62
    modifier_name = "Command" if modifier == "command" else "Control"
    log(f"ACTION: Voice (Right {modifier_name} + Right Shift)")
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
    mod_down = Quartz.CGEventCreateKeyboardEvent(source, modifier_key, True)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, mod_down)
    shift_down = Quartz.CGEventCreateKeyboardEvent(source, 60, True)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_down)
    shift_up = Quartz.CGEventCreateKeyboardEvent(source, 60, False)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_up)
    mod_up = Quartz.CGEventCreateKeyboardEvent(source, modifier_key, False)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, mod_up)
    log(f"Right {modifier_name}+Shift sent successfully")


def do_enter():
    log("ACTION: Enter")
    send_keys_hid("\r")


def do_tab():
    log("ACTION: Tab")
    send_keys_hid("\t")


def do_escape():
    log("ACTION: Escape")
    send_keys_hid("escape")


def _open_app(name: str):
    """Open/activate an application using AppleScript."""
    log(f"ACTION: Open {name}")
    script = f'tell application "{name}" to activate'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERROR: {result.stderr}")
    else:
        log(f"{name} opened")


def do_ghostty():
    _open_app("Ghostty")


def do_iterm():
    _open_app("iTerm")


def do_edge():
    _open_app("Microsoft Edge")


def do_fullscreen():
    log("ACTION: Toggle Fullscreen (Option+Enter)")
    send_keys_hid("\r", ["option"])


def do_ctrlc():
    log("ACTION: Ctrl+C")
    send_keys_hid("c", ["control"])


def do_pane(number: int):
    """Switch to tmux pane by number (Ctrl+A, number)."""
    log(f"ACTION: Pane {number} (Ctrl+A, {number})")
    _send_tmux_prefix_then(str(number))


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
        send_keys_hid("r", ["command"])
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
