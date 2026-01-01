#!/usr/bin/env python3
"""
Stream Deck plugin for Igor's vibe commands.
Handles WebSocket communication with Stream Deck and sends keystrokes.
Supports hot-reloading of actions.py via the Reload button.
"""

import asyncio
import base64
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

import websockets

# Log file for debugging
LOG_DIR = Path("/tmp/igor-vibe-code")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "plugin.log"

# Actions module - will be hot-reloaded
actions_module = None

# Global state for smart buttons
# Stored in sys module to survive the __main__ vs plugin module import split
if not hasattr(sys, "_plugin_state"):
    sys._plugin_state = {
        "websocket": None,
        "contexts": {}  # action UUID -> context
    }
_state = sys._plugin_state


def log(msg: str):
    """Write a timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    print(line, end="", file=sys.stderr)


def load_actions():
    """Load or reload the actions module."""
    global actions_module
    try:
        if actions_module is None:
            import actions
            actions_module = actions
        else:
            actions_module = importlib.reload(actions_module)
        log(f"Actions loaded: {list(actions_module.ACTIONS.keys())}")
        return True
    except Exception as e:
        log(f"ERROR loading actions: {e}")
        return False


def get_action_handler(action: str):
    """Get handler for an action, supporting hot-reload."""
    if actions_module and hasattr(actions_module, 'ACTIONS'):
        return actions_module.ACTIONS.get(action)
    return None


async def set_button_image(action: str, image_path: str):
    """Update a button's image. image_path is relative to icons folder."""
    ws = _state["websocket"]
    contexts = _state["contexts"]

    if not ws or action not in contexts:
        log(f"Cannot set image: ws={ws is not None}, context={action in contexts}")
        return

    # Load and encode image
    icons_dir = Path(__file__).parent / "icons"
    full_path = icons_dir / f"{image_path}@2x.png"
    if not full_path.exists():
        full_path = icons_dir / f"{image_path}.png"

    if not full_path.exists():
        log(f"Image not found: {full_path}")
        return

    with open(full_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    msg = {
        "event": "setImage",
        "context": contexts[action],
        "payload": {
            "image": f"data:image/png;base64,{image_data}",
            "target": 0  # 0 = both hardware and software
        }
    }
    await ws.send(json.dumps(msg))
    log(f"Set image: {image_path}")


def notify_button_press(action: str):
    """Notify actions module that a button was pressed (for cycle reset)."""
    if actions_module and hasattr(actions_module, 'on_any_button_press'):
        actions_module.on_any_button_press(action)


def update_button_image(action: str, image_path: str):
    """Sync wrapper for set_button_image - schedules the update."""
    ws = _state["websocket"]
    if ws:
        async def safe_set_image():
            try:
                await set_button_image(action, image_path)
            except Exception as e:
                log(f"ERROR in set_button_image: {e}")
        asyncio.create_task(safe_set_image())


async def handle_stream_deck(port: int, plugin_uuid: str, register_event: str):
    """Connect to Stream Deck and handle events."""
    uri = f"ws://127.0.0.1:{port}"
    log(f"Connecting to Stream Deck at {uri}")

    async with websockets.connect(uri) as ws:
        _state["websocket"] = ws

        # Register with Stream Deck
        register_msg = {"event": register_event, "uuid": plugin_uuid}
        await ws.send(json.dumps(register_msg))
        log(f"Registered with Stream Deck")

        # Handle incoming events
        async for message in ws:
            try:
                data = json.loads(message)
                event = data.get("event")
                action = data.get("action")
                context = data.get("context")

                log(f"EVENT: {event} | ACTION: {action}")

                # Store button context for image updates
                if context and action:
                    _state["contexts"][action] = context

                if event == "keyDown":
                    # Notify for cycle reset before handling
                    notify_button_press(action)

                    handler = get_action_handler(action)
                    if handler:
                        handler()
                    else:
                        log(f"Unknown action: {action}")

            except Exception as e:
                log(f"ERROR: {e}")


def main():
    # Clear log on startup
    LOG_FILE.write_text(f"=== Plugin started at {datetime.now()} ===\n")
    log(f"Args: {sys.argv}")

    # Add plugin directory to path for imports
    plugin_dir = Path(__file__).parent
    sys.path.insert(0, str(plugin_dir))

    # Load actions
    load_actions()

    # Stream Deck passes arguments: -port PORT -pluginUUID UUID -registerEvent EVENT -info INFO
    args = sys.argv[1:]
    params = {}

    i = 0
    while i < len(args):
        if args[i].startswith("-"):
            key = args[i][1:]
            if i + 1 < len(args):
                params[key] = args[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1

    port = int(params.get("port", 0))
    plugin_uuid = params.get("pluginUUID", "")
    register_event = params.get("registerEvent", "")

    log(f"Port: {port}, UUID: {plugin_uuid}, Event: {register_event}")

    if not all([port, plugin_uuid, register_event]):
        log("ERROR: Missing required Stream Deck parameters")
        sys.exit(1)

    asyncio.run(handle_stream_deck(port, plugin_uuid, register_event))


if __name__ == "__main__":
    main()
