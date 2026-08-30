#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
REMOTE="asad@vps.asad.dev"
REMOTE_DIR="/home/asad/projects/finnkino-seatmap"
PM2="/home/asad/.nvm/versions/node/v22.12.0/bin/pm2"

rsync -az --delete \
  -e "ssh -i $SSH_KEY" \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude 'research/' \
  --exclude 'sketches/' \
  --exclude '.DS_Store' \
  "$ROOT/" "$REMOTE:$REMOTE_DIR/"

ssh -i "$SSH_KEY" "$REMOTE" bash -s <<'REMOTE'
set -euo pipefail
cd /home/asad/projects/finnkino-seatmap
python3 -m venv .venv
.venv/bin/pip install -q -U pip
.venv/bin/pip install -q -r requirements.txt
export PATH="/home/asad/.nvm/versions/node/v22.12.0/bin:$PATH"
if pm2 describe finnkino >/dev/null 2>&1; then
  pm2 reload deploy/ecosystem.config.cjs --update-env
else
  pm2 start deploy/ecosystem.config.cjs
fi
pm2 save
REMOTE

if ! ssh -i "$SSH_KEY" "$REMOTE" 'grep -q "finnkino.asad.dev" /etc/caddy/Caddyfile'; then
  ssh -i "$SSH_KEY" "$REMOTE" "sudo tee -a /etc/caddy/Caddyfile > /dev/null" < "$ROOT/deploy/Caddyfile.snippet"
  ssh -i "$SSH_KEY" "$REMOTE" 'sudo systemctl reload caddy'
fi

echo "Deployed to https://finnkino.asad.dev"
