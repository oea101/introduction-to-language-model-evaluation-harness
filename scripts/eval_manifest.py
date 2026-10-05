#!/usr/bin/env python3
"""Create or verify a customer-support evaluation-input manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_DIR = Path(__file__).resolve().parents[1]
QWEN_CHAT_TEMPLATE_SHA = (
    "cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f"
)
EVALUATIONS = {
    "regression": {
        "evaluation": "customer_support_tool_calls_regression",
        "manifest": Path(
            "manifests/customer-support-regression-qwen2.5-0.5b-instruct.json"
        ),
        "config": Path(
            "configs/customer-support-tool-calls-regression-qwen2.5-0.5b-instruct.yaml"
        ),
        "task": Path(
            "custom_tasks/customer_support_tool_calls/"
            "customer_support_tool_calls_regression.yaml"
        ),
        "data": Path(
            "custom_tasks/customer_support_tool_calls/data/regression.jsonl"
        ),
        "usage": "routine_regression",
        "policy": Path(
            "baselines/customer-support-regression-qwen2.5-0.5b-instruct.json"
        ),
    },
    "final_test": {
        "evaluation": "customer_support_tool_calls_final_test",
        "manifest": Path(
            "manifests/customer-support-final-test-qwen2.5-0.5b-instruct.json"
        ),
        "config": Path(
            "configs/customer-support-tool-calls-final-test-qwen2.5-0.5b-instruct.yaml"
        ),
        "task": Path(
            "custom_tasks/customer_support_tool_calls/"
            "customer_support_tool_calls_final_test.yaml"
        ),
        "data": Path(
            "custom_tasks/customer_support_tool_calls/data/final_test.jsonl"
        ),
        "usage": "release_only",
        "policy": Path("policies/customer-support-final-release.json"),
    },
}
COMMON_INPUT_PATHS = (
    Path("pyproject.toml"),
    Path("uv.lock"),
    Path(
        "custom_tasks/customer_support_tool_calls/"
        "_customer_support_tool_calls_template_yaml"
    ),
    Path("custom_tasks/customer_support_tool_calls/utils.py"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(scope: str) -> dict[str, Any]:
    evaluation = EVALUATIONS[scope]
    config_path = evaluation["config"]
    data_path = evaluation["data"]
    input_paths = COMMON_INPUT_PATHS + (
        config_path,
        evaluation["task"],
        data_path,
        evaluation["policy"],
    )
    absolute_config = PROJECT_DIR / config_path
    config = yaml.safe_load(absolute_config.read_text())
    dataset = [
        json.loads(line)
        for line in (PROJECT_DIR / data_path).read_text().splitlines()
        if line.strip()
    ]
    model_args = config["model_args"]

    return {
        "schema_version": 1,
        "evaluation": evaluation["evaluation"],
        "files": {
            path.as_posix(): {"sha256": sha256(PROJECT_DIR / path)}
            for path in input_paths
        },
        "dataset": {
            "path": data_path.as_posix(),
            "records": len(dataset),
            "ids": [row["id"] for row in dataset],
        },
        "model": {
            "adapter": config["model"],
            "pretrained": model_args["pretrained"],
            "revision": model_args["revision"],
            "dtype": model_args["dtype"],
        },
        "protocol": {
            "task": config["tasks"][0],
            "num_fewshot": config["num_fewshot"],
            "apply_chat_template": config["apply_chat_template"],
            "fewshot_as_multiturn": config["fewshot_as_multiturn"],
            "chat_template_sha": QWEN_CHAT_TEMPLATE_SHA,
            "device": config["device"],
            "batch_size": config["batch_size"],
            "seeds": config["seed"],
        },
        "policy": {
            "usage": evaluation["usage"],
            "path": evaluation["policy"].as_posix(),
        },
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


parser = argparse.ArgumentParser()
parser.add_argument(
    "--scope",
    choices=tuple(EVALUATIONS),
    default="regression",
    help="Manifest to create or verify (default: regression).",
)
parser.add_argument(
    "--write",
    action="store_true",
    help="Replace the committed manifest with hashes from the current files.",
)
args = parser.parse_args()

evaluation = EVALUATIONS[args.scope]
manifest_path = PROJECT_DIR / evaluation["manifest"]
actual = build_manifest(args.scope)
if args.write:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(serialized(actual))
    print(f"Wrote {manifest_path.relative_to(PROJECT_DIR)}")
    raise SystemExit(0)

if not manifest_path.exists():
    scope_arg = "" if args.scope == "regression" else f" --scope {args.scope}"
    sys.exit(
        "Manifest is missing. Review the inputs, then run "
        f"`.venv/bin/python scripts/eval_manifest.py{scope_arg} --write`."
    )

expected = json.loads(manifest_path.read_text())
if actual != expected:
    print("Evaluation manifest mismatch.", file=sys.stderr)
    expected_files = expected.get("files", {})
    actual_files = actual.get("files", {})
    for path in sorted(set(expected_files) | set(actual_files)):
        expected_hash = expected_files.get(path, {}).get("sha256", "missing")
        actual_hash = actual_files.get(path, {}).get("sha256", "missing")
        if expected_hash != actual_hash:
            print(
                f"  {path}: expected {expected_hash}, actual {actual_hash}",
                file=sys.stderr,
            )
    if actual.get("model") != expected.get("model"):
        print("  model configuration changed", file=sys.stderr)
    if actual.get("protocol") != expected.get("protocol"):
        print("  evaluation protocol changed", file=sys.stderr)
    if actual.get("dataset") != expected.get("dataset"):
        print("  dataset membership changed", file=sys.stderr)
    sys.exit("Review the change and regenerate the manifest deliberately.")

print(f"Evaluation manifest verified: {manifest_path.relative_to(PROJECT_DIR)}")
