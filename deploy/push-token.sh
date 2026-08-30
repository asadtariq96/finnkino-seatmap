#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
REMOTE="${VPS_HOST:-asad@vps.asad.dev}"
REMOTE_DIR="${VPS_DIR:-/home/asad/projects/finnkino-seatmap}"
TOKEN_FILE="${1:-$ROOT/.finnkino-token}"

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "Token file not found: $TOKEN_FILE" >&2
  exit 1
fi

scp -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$TOKEN_FILE" "$REMOTE:$REMOTE_DIR/.finnkino-token"
ssh -i "$SSH_KEY" "$REMOTE" "chmod 600 $REMOTE_DIR/.finnkino-token"
echo "Token pushed to $REMOTE (app hot-reloads within ~5 min)"
