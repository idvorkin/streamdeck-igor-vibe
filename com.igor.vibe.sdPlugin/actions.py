"""
Hot-reloadable action handlers for Stream Deck plugin.
Edit this file and press the Reload button to apply changes.
"""

import subprocess
import time

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
}
