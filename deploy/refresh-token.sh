#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
REMOTE="asad@vps.asad.dev"
REMOTE_DIR="/home/asad/projects/finnkino-seatmap"
TOKEN_FILE="$ROOT/.finnkino-token"

if [[ ! -x "$ROOT/.venv/bin/python3" ]]; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"
fi

"$ROOT/.venv/bin/python3" "$ROOT/deploy/fetch_token.py" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"

"$ROOT/deploy/push-token.sh" "$TOKEN_FILE"

if command -v gh >/dev/null 2>&1; then
  gh secret set FINNKINO_TOKEN --repo asadtariq96/finnkino-seatmap < "$TOKEN_FILE" 2>/dev/null || true
fi

echo "Token refreshed on VPS"
