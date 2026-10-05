#!/usr/bin/env bash
set -euo pipefail

export HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1}
export HF_HUB_DOWNLOAD_TIMEOUT=${HF_HUB_DOWNLOAD_TIMEOUT:-300}

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEVICE=${1:-cpu}

cd "$PROJECT_DIR"

run_config() {
  HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
  HF_HOME=.cache/huggingface \
  TOKENIZERS_PARALLELISM=false \
  .venv/bin/lm-eval run --config "$1" --device "$DEVICE"
}

run_config configs/customer-support-tool-calls-regression-pythia-70m.yaml
run_config configs/customer-support-tool-calls-regression-qwen2.5-0.5b-instruct-raw-prompt.yaml
run_config configs/customer-support-tool-calls-regression-qwen2.5-0.5b-instruct.yaml

.venv/bin/python scripts/compare_milestone_09_models.py
