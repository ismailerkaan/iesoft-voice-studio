#!/bin/zsh
# One-time setup on a new Mac (Apple Silicon): Python venv, pinned packages, web UI build, model.
# Usage: scripts/setup.sh            (everything)
#        SKIP_MODEL=1 scripts/setup.sh  (skip the ~3.2 GB model download; it happens on first start)
set -euo pipefail
cd "$(dirname "$0")/.."

fail() { echo "❌ $1" >&2; exit 1; }

[[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || echo "⚠️  Apple Silicon macOS dışında test edilmedi (MPS yerine CPU kullanılır)."

PYTHON="${PYTHON:-$(command -v python3.13 || true)}"
[[ -n "$PYTHON" ]] || fail "Python 3.13 bulunamadı. Kurulum: brew install python@3.13"
command -v node >/dev/null || fail "Node.js bulunamadı (20+ gerekli). Kurulum: brew install node"
command -v ffmpeg >/dev/null || fail "FFmpeg bulunamadı (MP3 için gerekli). Kurulum: brew install ffmpeg"
command -v git >/dev/null || fail "git bulunamadı (Chatterbox GitHub'dan kurulur)."

echo "→ Python sanal ortamı (.venv)"
[[ -d .venv ]] || "$PYTHON" -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
# chatterbox-tts declares resemble-perth@master while the lock pins a Perth commit; pip rejects two
# direct URLs for one package. Install the rest first, then Perth (pinned), then Chatterbox without deps.
LOCK_REST="$(mktemp)"
grep -vE '^(chatterbox-tts|resemble-perth) @' requirements.lock.txt > "$LOCK_REST"
.venv/bin/pip install -r "$LOCK_REST"
rm -f "$LOCK_REST"
.venv/bin/pip install "$(grep -E '^resemble-perth @' requirements.lock.txt)"
.venv/bin/pip install --no-deps "$(grep -E '^chatterbox-tts @' requirements.lock.txt)"
.venv/bin/pip check

echo "→ Web arayüzü (npm ci + build)"
(cd frontend && npm ci --no-fund --no-audit && npm run build)

if [[ -z "${SKIP_MODEL:-}" ]]; then
  echo "→ Chatterbox Multilingual V3 model dosyaları (~3,2 GB)"
  .venv/bin/python scripts/download_model.py
fi

echo "→ Testler"
.venv/bin/python -m unittest discover -s backend/tests -t . 2>&1 | tail -3

echo "✅ Kurulum tamam. Başlatmak için: scripts/launch.sh"
