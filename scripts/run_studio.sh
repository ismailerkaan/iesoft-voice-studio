#!/bin/zsh
# Starts IESOFT Voice Studio on http://127.0.0.1:8765 (API + built web UI).
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -d frontend/dist ]]; then
  (cd frontend && npm run build)
fi
exec .venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port "${PORT:-8765}"
