#!/usr/bin/env bash
# Setup 1 (Easy) — run promptfoo + garak against the chat endpoint.
#
# Usage:  ./setups/1_easy/run.sh
# Prereqs: npm i (promptfoo), pip install garak, and a filled-in .env at repo root.

set -euo pipefail

# Resolve repo root (two levels up from this script).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Load .env so TARGET_CHAT_URL / TARGET_CHAT_API_KEY are available to both tools.
if [[ -f .env ]]; then
  set -a; source .env; set +a
else
  echo "!! No .env found. Copy .env.example to .env and fill it in." >&2
  exit 1
fi

STAMP="$(date -u +%Y-%m-%d_%H%M%S)"
OUT="reports/${STAMP}_chat_easy"
mkdir -p "$OUT"

echo "==> [1/2] promptfoo red-team scan"
npx promptfoo redteam run \
  -c setups/1_easy/promptfooconfig.yaml \
  -o "$OUT/promptfoo_results.json" || echo "!! promptfoo run returned non-zero"

echo "==> [2/2] garak probe scan"
garak \
  --model_type rest \
  -G setups/1_easy/garak_rest.json \
  --probes promptinject,encoding,leakreplay \
  --report_prefix "$OUT/garak" || echo "!! garak run returned non-zero"

echo "==> Done. Results in $OUT"
echo "    View promptfoo report with: npx promptfoo redteam report"
