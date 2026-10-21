#!/bin/zsh
# Starts IESOFT Voice Studio (if not already running) and opens it in the browser
# once the model is ready. Used by the `iesoft voice` shell command.
set -euo pipefail

PORT="${PORT:-8765}"
URL="http://127.0.0.1:${PORT}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

model_status() {
  curl -s -m 2 "${URL}/api/status" | python3 -c "import json,sys; print(json.load(sys.stdin)['model']['status'])" 2>/dev/null
}

if [[ -n "$(model_status)" ]]; then
  echo "IESOFT Voice Studio zaten çalışıyor → ${URL}"
  open "${URL}"
  exit 0
fi

if lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Hata: ${PORT} portu başka bir uygulama tarafından kullanılıyor." >&2
  exit 1
fi

# Open the browser in the background once the model has finished loading.
(
  for _ in {1..90}; do
    case "$(model_status)" in
      ready|error) open "${URL}"; exit 0 ;;
    esac
    sleep 2
  done
) &

echo "IESOFT Voice Studio başlatılıyor… Model hazır olunca tarayıcı açılacak (~20 sn)."
echo "Durdurmak için Ctrl + C"
exec "${SCRIPT_DIR}/run_studio.sh"
