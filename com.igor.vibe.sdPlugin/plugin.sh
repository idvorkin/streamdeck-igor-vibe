#!/bin/bash
# Stream Deck plugin launcher
# Runs the Python plugin with uv to handle dependencies

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Run with uv to auto-install websockets dependency
exec /opt/homebrew/bin/uv run --with websockets python3 plugin.py "$@"
