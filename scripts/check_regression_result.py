#!/usr/bin/env python3
"""Validate a saved lm_eval result and its sample evidence against the baseline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from custom_tasks.customer_support_tool_calls.utils import process_results  # noqa: E402


BASELINE_PATH = (
    PROJECT_DIR
    / "baselines/customer-support-regression-qwen2.5-0.5b-instruct.json"
)


def fail(message: str) -> None:
    print(f"Regression gate failed: {message}", file=sys.stderr)
    raise SystemExit(1)


parser = argparse.ArgumentParser()
parser.add_argument("result", type=Path, help="Path to an lm_eval results JSON file")
args = parser.parse_args()

result_path = args.result.expanduser().resolve()
result = json.loads(result_path.read_text())
baseline = json.loads(BASELINE_PATH.read_text())
task_name = baseline["task"]["name"]

if task_name not in result.get("results", {}):
    fail(f"result does not contain task {task_name}")

model_args = result.get("config", {}).get("model_args", {})
for key in ("pretrained", "revision"):
    if model_args.get(key) != baseline["model"][key]:
        fail(
            f"model {key} is {model_args.get(key)!r}; "
            f"expected {baseline['model'][key]!r}"
        )

for result_key, baseline_key in (
    ("lm_eval_version", "lm_eval_version"),
    ("transformers_version", "transformers_version"),
):
    if result.get(result_key) != baseline["environment"][baseline_key]:
        fail(
            f"{result_key} is {result.get(result_key)!r}; "
            f"expected {baseline['environment'][baseline_key]!r}"
        )

task_hash = result.get("task_hashes", {}).get(task_name)
if task_hash != baseline["task"]["hash"]:
    fail(f"task hash is {task_hash!r}; expected {baseline['task']['hash']!r}")

effective_samples = result.get("n-samples", {}).get(task_name, {}).get("effective")
if effective_samples != baseline["task"]["effective_samples"]:
    fail(
        f"effective sample count is {effective_samples!r}; "
        f"expected {baseline['task']['effective_samples']}"
    )

head = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=PROJECT_DIR,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
recorded_git_hash = result.get("git_hash")
if not recorded_git_hash or not head.startswith(recorded_git_hash):
    fail(f"result git hash {recorded_git_hash!r} does not identify HEAD {head}")

prefix = "results_"
if not result_path.name.startswith(prefix) or result_path.suffix != ".json":
    fail(f"unexpected result filename {result_path.name}")
timestamp = result_path.stem[len(prefix) :]
samples_path = result_path.with_name(f"samples_{task_name}_{timestamp}.jsonl")
if not samples_path.exists():
    fail(f"sample evidence is missing: {samples_path}")

samples = [json.loads(line) for line in samples_path.read_text().splitlines()]
if len(samples) != baseline["task"]["effective_samples"]:
    fail(f"sample log contains {len(samples)} records")

metric_names = tuple(baseline["minimum_metrics"])
recomputed_values = {metric: [] for metric in metric_names}
for sample in samples:
    recomputed = process_results(sample["doc"], sample["filtered_resps"])
    for metric in metric_names:
        if sample.get(metric) != recomputed[metric]:
            fail(f"stored grade differs from recomputed {metric} for {sample['doc']['id']}")
        recomputed_values[metric].append(recomputed[metric])

aggregate = result["results"][task_name]
print("| Metric | Actual | Minimum |")
print("|---|---:|---:|")
for metric, minimum in baseline["minimum_metrics"].items():
    actual = aggregate.get(f"{metric},none")
    recomputed_mean = sum(recomputed_values[metric]) / len(recomputed_values[metric])
    if actual != recomputed_mean:
        fail(
            f"aggregate {metric} is {actual!r}; recomputed mean is {recomputed_mean!r}"
        )
    print(f"| {metric} | {actual:.0%} | {minimum:.0%} |")
    if actual < minimum:
        fail(f"{metric} is {actual:.0%}; minimum is {minimum:.0%}")

print(f"Regression gate passed for source commit {head}.")
print(f"Sample evidence: {samples_path}")
