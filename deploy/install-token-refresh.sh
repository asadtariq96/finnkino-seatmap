#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$ROOT/deploy/com.asad.finnkino-token-refresh.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.asad.finnkino-token-refresh.plist"
LABEL="com.asad.finnkino-token-refresh"

sed "s|__ROOT__|$ROOT|g" "$PLIST_SRC" > "$PLIST_DST"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/$LABEL"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed $LABEL (every 6h + logs at /tmp/finnkino-token-refresh.log)"
