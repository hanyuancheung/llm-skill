#!/usr/bin/env bash
# install.sh — one-shot sanity check for the llm-skill layout.
# Safe to re-run. Never mutates skills or AGENT.md content.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "== llm-skill install check @ $ROOT =="

REQUIRED_FILES=(
  "AGENT.md"
  "AGENTS.md"
  "CLAUDE.md"
  "HERMES.md"
  "README.md"
  "README_zh.md"
  "CHANGELOG.md"
  "scripts/validate.py"
)

missing=0
for f in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "  [missing] $f"
    missing=1
  else
    echo "  [ok]      $f"
  fi
done

if [[ ! -d skills ]]; then
  echo "  [missing] skills/ directory"
  missing=1
else
  echo "  [ok]      skills/"
fi

if [[ $missing -ne 0 ]]; then
  echo
  echo "FAILED: required files are missing. Aborting."
  exit 1
fi

echo
echo "== running scripts/validate.py =="
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/validate.py
else
  echo "python3 not found. Please install Python 3.8+ to run the validator."
  exit 2
fi

echo
echo "Install check passed. Next steps:"
echo "  * Codex users       → AGENTS.md is already in place."
echo "  * Claude Code users → CLAUDE.md is already in place."
echo "  * HERMES users      → HERMES.md is already in place."
echo "  * Add your own skill: cp -r skills/_template skills/<your-skill-name>"
