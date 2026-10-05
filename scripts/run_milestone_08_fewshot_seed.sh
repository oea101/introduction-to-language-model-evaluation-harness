#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
FEWSHOT_SEED=${1:?Usage: $0 FEWSHOT_SEED [DEVICE]}
DEVICE=${2:-cpu}

cd "$PROJECT_DIR"

HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
HF_HOME=.cache/huggingface \
TOKENIZERS_PARALLELISM=false \
.venv/bin/lm-eval run \
  --config configs/piqa-pythia-14m-5shot.yaml \
  --seed "0,1234,1234,$FEWSHOT_SEED" \
  --device "$DEVICE" \
  --output_path "results/milestone-08/five-shot-seed-$FEWSHOT_SEED"
