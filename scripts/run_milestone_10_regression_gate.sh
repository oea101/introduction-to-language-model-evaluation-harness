#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RESULT_DIR="$PROJECT_DIR/results/milestone-09/model-comparison/qwen2.5-0.5b-instruct-regression/Qwen__Qwen2.5-0.5B-Instruct"
MARKER=$(mktemp)
trap 'rm -f "$MARKER"' EXIT

cd "$PROJECT_DIR"

.venv/bin/python scripts/check_clean_tree.py
UV_CACHE_DIR=.cache/uv uv sync --frozen
.venv/bin/python scripts/eval_manifest.py
.venv/bin/python -m unittest -v tests/test_customer_support_tool_calls.py

touch "$MARKER"
HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
HF_HOME=.cache/huggingface \
TOKENIZERS_PARALLELISM=false \
.venv/bin/lm-eval run \
  --config configs/customer-support-tool-calls-regression-qwen2.5-0.5b-instruct.yaml

RESULT_FILE=$(find "$RESULT_DIR" -maxdepth 1 -name 'results_*.json' -newer "$MARKER" -print | sort | tail -1)
if [[ -z "$RESULT_FILE" ]]; then
  echo "Regression gate failed: no new result file was written." >&2
  exit 1
fi

.venv/bin/python scripts/check_regression_result.py "$RESULT_FILE"
