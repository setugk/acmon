#!/bin/zsh
# Deploy Acmon's public demo to the NAS (container "acmon-demo", port 5056).
# All demo data lives in the visitor's own browser (localStorage) — DEMO_MODE=1 makes the
# frontend skip the server entirely, so this container needs no data volume at all.
# scp/rsync don't work on UGOS, so files are uploaded via `ssh cat`.

NAS="Setu@10.0.0.10"
SRC="/Users/setugk/Seafile/Projects/Claude Code/acmon"
REMOTE="/volume1/docker/acmon-demo"
SOCK="/tmp/acmon-demo-deploy.sock"

log() { echo "$(date '+%H:%M:%S') $1"; }

log "Connecting to NAS..."
ssh -M -S "$SOCK" -fN "$NAS" || { log "SSH connection failed"; exit 1; }

run() { ssh -S "$SOCK" "$NAS" "$1"; }
upload() {
  ssh -S "$SOCK" "$NAS" "cat > $1" < "$2" && log "  uploaded: $(basename $1)"
}

log "Preparing remote directories..."
run "mkdir -p $REMOTE/templates $REMOTE/static"

log "Uploading source files..."
upload "$REMOTE/app.py"                    "$SRC/app.py"
upload "$REMOTE/db.py"                     "$SRC/db.py"
upload "$REMOTE/Dockerfile"                "$SRC/Dockerfile"
upload "$REMOTE/docker-compose.yml"        "$SRC/docker-compose.demo.yml"
upload "$REMOTE/templates/index.html"      "$SRC/templates/index.html"
upload "$REMOTE/static/manifest.json"      "$SRC/static/manifest.json"
upload "$REMOTE/static/icon-192.png"       "$SRC/static/icon-192.png"
upload "$REMOTE/static/icon-512.png"       "$SRC/static/icon-512.png"

ssh -S "$SOCK" -O exit "$NAS" 2>/dev/null

log "Building and starting container (will prompt for the NAS sudo password)..."
ssh -t "$NAS" "cd $REMOTE && sudo docker compose up -d --build"

log "Done. Acmon demo → http://10.0.0.10:5056"
