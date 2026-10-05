#!/usr/bin/env bash
set -euo pipefail

export HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1}
export HF_HUB_DOWNLOAD_TIMEOUT=${HF_HUB_DOWNLOAD_TIMEOUT:-300}

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
EXPECTED_UPSTREAM_COMMIT="ddd67220430a2470529f25fd5c05a576ca1057a0"

cd "$PROJECT_DIR"

for command_name in git uv jq rg; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
done

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run ./scripts/setup_course.sh first." >&2
  exit 1
fi

if [[ ! -d upstream/lm-evaluation-harness/.git ]]; then
  echo "Missing pinned upstream source. Run ./scripts/setup_course.sh first." >&2
  exit 1
fi

actual_commit=$(git -C upstream/lm-evaluation-harness rev-parse HEAD)
if [[ "$actual_commit" != "$EXPECTED_UPSTREAM_COMMIT" ]]; then
  echo "Upstream source is at $actual_commit; expected $EXPECTED_UPSTREAM_COMMIT." >&2
  exit 1
fi

.venv/bin/python - <<'PY'
from importlib.metadata import version

actual = version("lm_eval")
assert actual == "0.4.13", f"lm_eval is {actual}; expected 0.4.13"
print(f"lm_eval version: {actual}")
PY

.venv/bin/python -m unittest -v tests/test_customer_support_tool_calls.py
.venv/bin/python scripts/eval_manifest.py

HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
HF_HOME=${HF_HOME:-$PROJECT_DIR/.cache/huggingface} \
  .venv/bin/python - <<'PY'
from lm_eval.tasks import TaskManager

names = [
    "course_piqa",
    "customer_support_tool_calls_dev",
    "customer_support_tool_calls_regression",
]
manager = TaskManager(include_path="custom_tasks", include_defaults=False)
loaded = manager.load(names)["tasks"]

for name in names:
    task = loaded[name]
    if name == "course_piqa":
        count = len(task.validation_docs())
    else:
        docs = task.test_docs()
        count = len(docs)
        first = docs[0]
        assert callable(task.config.process_results)
        assert task.doc_to_target(first) == first["expected_call"]
    print(f"Loaded {name}: {count} documents")
PY

echo "Course preflight passed. No model inference or final-test task was run."
