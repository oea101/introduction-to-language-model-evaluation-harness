#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEVICE=${1:-cpu}

cd "$PROJECT_DIR"

HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
HF_HOME=.cache/huggingface \
TOKENIZERS_PARALLELISM=false \
.venv/bin/lm-eval run \
  --config configs/piqa-pythia-14m-5shot.yaml \
  --device "$DEVICE" \
  --show_config
