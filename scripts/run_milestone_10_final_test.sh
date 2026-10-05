#!/usr/bin/env bash
set -euo pipefail

export HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1}
export HF_HUB_DOWNLOAD_TIMEOUT=${HF_HUB_DOWNLOAD_TIMEOUT:-300}

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RELEASE_ID=${FINAL_EVAL_RELEASE_ID:-}

if [[ -z "$RELEASE_ID" ]]; then
  echo "Refusing to open or run the final holdout." >&2
  echo "Set FINAL_EVAL_RELEASE_ID to the predeclared release identifier." >&2
  exit 2
fi
if [[ ! "$RELEASE_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]]; then
  echo "FINAL_EVAL_RELEASE_ID must use 1-64 letters, digits, dots, underscores, or hyphens." >&2
  exit 2
fi

RESULT_DIR="$PROJECT_DIR/results/milestone-10/final-test/$RELEASE_ID"
MARKER=$(mktemp)
trap 'rm -f "$MARKER"' EXIT

cd "$PROJECT_DIR"

.venv/bin/python scripts/check_clean_tree.py
UV_CACHE_DIR=.cache/uv uv sync --frozen
.venv/bin/python scripts/eval_manifest.py --scope final_test
.venv/bin/python scripts/check_final_holdout.py
.venv/bin/python -m unittest -v tests/test_customer_support_tool_calls.py

mkdir -p "$(dirname "$RESULT_DIR")"
if ! mkdir "$RESULT_DIR"; then
  echo "Refusing to reuse release ID $RELEASE_ID; choose a new declared ID." >&2
  exit 2
fi

touch "$MARKER"
HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
HF_HOME=.cache/huggingface \
TOKENIZERS_PARALLELISM=false \
.venv/bin/lm-eval run \
  --config configs/customer-support-tool-calls-final-test-qwen2.5-0.5b-instruct.yaml \
  --output_path "$RESULT_DIR"

RESULT_FILE=$(find "$RESULT_DIR" -type f -name 'results_*.json' -newer "$MARKER" -print | sort | tail -1)
if [[ -z "$RESULT_FILE" ]]; then
  echo "Final evaluation failed: no new result file was written." >&2
  exit 1
fi

.venv/bin/python scripts/check_final_result.py "$RESULT_FILE" --release-id "$RELEASE_ID"
