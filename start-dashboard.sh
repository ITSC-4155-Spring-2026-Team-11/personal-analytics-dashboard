#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ROOT_DIR="$(pwd)"

pick_python() {
  if [[ -x "$ROOT_DIR/venv/bin/python3" ]]; then
    echo "$ROOT_DIR/venv/bin/python3"
    return 0
  fi
  if [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
    echo "$ROOT_DIR/venv/bin/python"
    return 0
  fi
  if [[ -x "$ROOT_DIR/.venv/bin/python3" ]]; then
    echo "$ROOT_DIR/.venv/bin/python3"
    return 0
  fi
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    echo "$ROOT_DIR/.venv/bin/python"
    return 0
  fi
  return 1
}

PY="$(pick_python || true)"
if [[ -z "${PY:-}" ]]; then
  echo "Creating Python virtual env (.venv)..." >&2
  python3 -m venv .venv
  PY="$ROOT_DIR/.venv/bin/python3"
fi

echo "Installing Python dependencies..." >&2
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

# Build the React frontend if dist/ is missing.
DIST_INDEX="$ROOT_DIR/web/react-version/dist/index.html"
if [[ ! -f "$DIST_INDEX" ]]; then
  echo "Building React frontend (npm run build)..." >&2
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found but frontend dist/ is missing." >&2
    echo "Install Node.js (includes npm) and re-run." >&2
    exit 1
  fi
  pushd "web/react-version" >/dev/null
  npm install
  npm run build
  popd >/dev/null
fi

exec "$PY" launcher/start_dashboard.py
