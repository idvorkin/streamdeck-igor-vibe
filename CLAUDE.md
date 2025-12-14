# Stream Deck Igor Vibe

Stream Deck plugin for Igor's workflow - tmux pane navigation and voice commands.

## Architecture

- **plugin.py**: WebSocket handler that connects to Stream Deck. Runs continuously.
- **actions.py**: Hot-reloadable action handlers. Edit and press Reload to apply.
- **manifest.json**: Plugin metadata and action definitions.
- **keys.py**: CLI tool for testing keystrokes (not used by plugin).

## Actions

| UUID | Function | What it does |
|------|----------|--------------|
| `com.igor.vibe.previouspane` | `do_previous_pane()` | Ctrl+A, p (tmux prev) |
| `com.igor.vibe.nextpane` | `do_next_pane()` | Ctrl+A, n (tmux next) |
| `com.igor.vibe.voice` | `do_voice()` | Right Cmd+Shift (Wispr) |
| `com.igor.vibe.enter` | `do_enter()` | Enter key |
| `com.igor.vibe.tab` | `do_tab()` | Tab key |
| `com.igor.vibe.escape` | `do_escape()` | Escape key |
| `com.igor.vibe.ctrlc` | `do_ctrlc()` | Ctrl+C |
| `com.igor.vibe.ghostty` | `do_ghostty()` | Open Ghostty |
| `com.igor.vibe.iterm` | `do_iterm()` | Open iTerm |
| `com.igor.vibe.fullscreen` | `do_fullscreen()` | Option+Enter |
| `com.igor.vibe.reload` | `do_reload()` | Hot-reload actions.py |

## Development

```bash
just test           # Run tests
just plugin-logs    # Show logs
just watch-logs     # Tail -f logs
just restart        # Restart Stream Deck
just reset          # Full reinstall
```

Logs: `/tmp/igor-vibe-code/plugin.log`

## When to Restart

**No restart (press Reload button):**
- Changes to `actions.py`

**Restart needed (`just restart`):**
- Changes to `plugin.py`
- Changes to `manifest.json` (new actions, UUIDs, icons)
- Plugin crashes

## Adding a New Action

1. Add function to `actions.py`: `def do_myaction(): ...`
2. Add to ACTIONS dict: `"com.igor.vibe.myaction": do_myaction`
3. Add action to `manifest.json` Actions array
4. Create icons: `icons/myaction.png` and `icons/myaction@2x.png` (20x20 and 40x40)
5. Run `just restart`

## Technical Notes

- Voice uses CGEvent (HID level) via pyobjc-framework-Quartz because AppleScript can't trigger Wispr Flow (Karabiner intercepts at lower level)
- Tmux prefix is Ctrl+A (change in `actions.py` if different)
- uv path is `/opt/homebrew/bin/uv` (ARM Mac)

## Installation

Plugin symlink: `~/Library/Application Support/com.elgato.StreamDeck/Plugins/com.igor.vibe.sdPlugin`

## Conventions

See `zz-chop-conventions/` for coding standards (symlinked to chop-conventions repo).
