#!/usr/bin/env bash
set -euo pipefail

export HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1}
export HF_HUB_DOWNLOAD_TIMEOUT=${HF_HUB_DOWNLOAD_TIMEOUT:-300}

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEMP_DIR=$(mktemp -d)
CLONE_DIR="$TEMP_DIR/introduction-to-language-model-evaluation-harness"
SHARED_UV_CACHE=${UV_CACHE_DIR:-$PROJECT_DIR/.cache/uv}
trap 'rm -rf "$TEMP_DIR"' EXIT

UV_SYNC_ARGS=(--frozen)
if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  BOOTSTRAP_PYTHON=$(
    "$PROJECT_DIR/.venv/bin/python" -c 'import sys; print(sys._base_executable)'
  )
  UV_SYNC_ARGS+=(--python "$BOOTSTRAP_PYTHON")
fi

git clone --quiet --local --no-hardlinks "$PROJECT_DIR" "$CLONE_DIR"
cd "$CLONE_DIR"

UV_CACHE_DIR="$SHARED_UV_CACHE" uv sync "${UV_SYNC_ARGS[@]}"
.venv/bin/python scripts/eval_manifest.py
.venv/bin/python -m unittest -v tests/test_customer_support_tool_calls.py

HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
HF_HOME="$PROJECT_DIR/.cache/huggingface" .venv/bin/python - <<'PY'
from lm_eval.tasks import TaskManager

names = [
    "customer_support_tool_calls_dev",
    "customer_support_tool_calls_regression",
]
manager = TaskManager(include_path="custom_tasks", include_defaults=False)
tasks = manager.load(names)["tasks"]
for name in names:
    task = tasks[name]
    docs = task.test_docs()
    first = docs[0]
    assert callable(task.config.process_results)
    assert task.doc_to_target(first) == first["expected_call"]
    print(f"Loaded {name}: {len(docs)} documents")
PY

if [[ -n $(git status --porcelain --untracked-files=all) ]]; then
  echo "Clean-checkout verification changed tracked or untracked source files." >&2
  git status --short
  exit 1
fi

echo "Clean checkout verified at commit $(git rev-parse HEAD)."
echo "Final-test data was not loaded or evaluated by this routine check."
