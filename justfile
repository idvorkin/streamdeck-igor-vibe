# Run tests
test:
    uv run --with pytest --with typer --with rich pytest tests/ -v

# Run a specific command
run cmd:
    ./keys.py {{cmd}}

# Restart Stream Deck to reload plugins
restart:
    osascript -e 'quit app "Elgato Stream Deck"' || true
    sleep 2
    open -a "Elgato Stream Deck"

# Check Stream Deck logs for plugin errors
logs:
    tail -50 ~/Library/Logs/ElgatoStreamDeck/StreamDeck.log | grep -i "igor"

# View plugin debug logs
plugin-logs:
    cat /tmp/igor-vibe-code/plugin.log 2>/dev/null || echo "No logs yet"

# Watch plugin logs in real-time
watch-logs:
    tail -f /tmp/igor-vibe-code/plugin.log

# Reset plugin (remove, restart Stream Deck, re-link)
reset:
    rm -f ~/Library/Application\ Support/com.elgato.StreamDeck/Plugins/com.igor.vibe.sdPlugin
    osascript -e 'quit app "Elgato Stream Deck"' || true
    sleep 2
    ln -sf "$(pwd)/com.igor.vibe.sdPlugin" ~/Library/Application\ Support/com.elgato.StreamDeck/Plugins/
    open -a "Elgato Stream Deck"
