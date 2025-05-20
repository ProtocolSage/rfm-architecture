#!/usr/bin/env bash
set -euo pipefail

# ---------- System packages ----------
sudo apt-get update -y
sudo apt-get install -y build-essential git curl jq

# ---------- Python ----------
PY_VERSION="3.11"
python${PY_VERSION} -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ---------- Node (if applicable) ----------
if [ -f package.json ]; then
  corepack enable               # ensures pnpm/yarn availability
  pnpm install --frozen-lockfile
fi

# ---------- Validation ----------
if command -v pytest >/dev/null 2>&1; then
  pytest -q || true             # run Python tests if present
fi
if [ -f package.json ] && jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
  pnpm run lint || true         # run JS/TS linter if defined
fi