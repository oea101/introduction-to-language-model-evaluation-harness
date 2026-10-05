#!/usr/bin/env bash
set -euo pipefail

export HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1}
export HF_HUB_DOWNLOAD_TIMEOUT=${HF_HUB_DOWNLOAD_TIMEOUT:-300}

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
UPSTREAM_DIR="$PROJECT_DIR/upstream/lm-evaluation-harness"
UPSTREAM_URL="https://github.com/EleutherAI/lm-evaluation-harness.git"
UPSTREAM_TAG="v0.4.13"
UPSTREAM_COMMIT="ddd67220430a2470529f25fd5c05a576ca1057a0"

missing=()
for command_name in git uv jq rg; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    missing+=("$command_name")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "Missing course prerequisites: ${missing[*]}" >&2
  echo "Install them, then rerun ./scripts/setup_course.sh." >&2
  exit 1
fi

cd "$PROJECT_DIR"
mkdir -p .cache/uv .cache/huggingface upstream

echo "Creating the locked Python environment..."
UV_CACHE_DIR="$PROJECT_DIR/.cache/uv" uv sync --frozen

if [[ ! -e "$UPSTREAM_DIR" ]]; then
  echo "Cloning lm-evaluation-harness $UPSTREAM_TAG for source study..."
  git clone --quiet --branch "$UPSTREAM_TAG" --depth 1 \
    "$UPSTREAM_URL" "$UPSTREAM_DIR"
elif [[ ! -d "$UPSTREAM_DIR/.git" ]]; then
  echo "$UPSTREAM_DIR exists but is not a Git checkout." >&2
  echo "Move or remove it, then rerun setup." >&2
  exit 1
fi

actual_commit=$(git -C "$UPSTREAM_DIR" rev-parse HEAD)
if [[ "$actual_commit" != "$UPSTREAM_COMMIT" ]]; then
  echo "Unexpected upstream commit: $actual_commit" >&2
  echo "Expected $UPSTREAM_COMMIT ($UPSTREAM_TAG)." >&2
  echo "Remove $UPSTREAM_DIR and rerun setup." >&2
  exit 1
fi

if [[ ! -f course-progress.md ]]; then
  cp COURSE_PROGRESS_TEMPLATE.md course-progress.md
  echo "Created course-progress.md."
fi

HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1} \
HF_HOME="$PROJECT_DIR/.cache/huggingface" \
  ./scripts/preflight_course.sh

echo
echo "Course setup is ready."
echo "Open this folder in Codex and send:"
echo "Start Introduction to the Language Model Evaluation Harness. Teach me interactively, one question at a time."
