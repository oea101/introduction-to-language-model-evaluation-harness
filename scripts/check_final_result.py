#!/usr/bin/env python3
"""Verify provenance and sample evidence for a final-holdout result."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from custom_tasks.customer_support_tool_calls.utils import process_results  # noqa: E402


TASK_NAME = "customer_support_tool_calls_final_test"
MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
MODEL_REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"
METRICS = (
    "valid_json",
    "valid_tool_schema",
    "correct_tool",
    "correct_arguments",
    "exact_tool_call",
)
FINAL_DATA = (
    PROJECT_DIR / "custom_tasks/customer_support_tool_calls/data/final_test.jsonl"
)
MANIFEST_PATH = (
    PROJECT_DIR
    / "manifests/customer-support-final-test-qwen2.5-0.5b-instruct.json"
)
POLICY_PATH = PROJECT_DIR / "policies/customer-support-final-release.json"
EXPECTED_GENERATION = {
    "do_sample": False,
    "max_gen_toks": 128,
    "until": ["\n\n"],
}


def fail(message: str) -> None:
    print(f"Final-evaluation verification failed: {message}", file=sys.stderr)
    raise SystemExit(1)


parser = argparse.ArgumentParser()
parser.add_argument("result", type=Path, help="Path to an lm_eval results JSON file")
parser.add_argument(
    "--release-id",
    required=True,
    help="Declared final-evaluation release ID",
)
args = parser.parse_args()
if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", args.release_id) is None:
    fail("release ID has an invalid format")

result_path = args.result.expanduser().resolve()
expected_result_dir = (
    PROJECT_DIR / "results/milestone-10/final-test" / args.release_id
).resolve()
if expected_result_dir not in result_path.parents:
    fail(f"result is outside the declared release directory {expected_result_dir}")
result = json.loads(result_path.read_text())
manifest = json.loads(MANIFEST_PATH.read_text())
policy = json.loads(POLICY_PATH.read_text())
if policy.get("decision_rule") != "all_metrics_gte_minimum":
    fail(f"unsupported final decision rule {policy.get('decision_rule')!r}")
if tuple(policy.get("minimum_metrics", {})) != METRICS:
    fail("final policy does not declare every metric in the expected order")
if TASK_NAME not in result.get("results", {}):
    fail(f"result does not contain {TASK_NAME}")

run_config = result.get("config", {})
expected_model_args = {
    "pretrained": MODEL,
    "revision": MODEL_REVISION,
    "dtype": manifest["model"]["dtype"],
}
if run_config.get("model") != manifest["model"]["adapter"]:
    fail(f"model adapter is {run_config.get('model')!r}")
if run_config.get("model_args") != expected_model_args:
    fail(f"model arguments are {run_config.get('model_args')!r}")

expected_run_values = {
    "batch_size": manifest["protocol"]["batch_size"],
    "device": manifest["protocol"]["device"],
    "random_seed": manifest["protocol"]["seeds"][0],
    "numpy_seed": manifest["protocol"]["seeds"][1],
    "torch_seed": manifest["protocol"]["seeds"][2],
    "fewshot_seed": manifest["protocol"]["seeds"][3],
    "use_cache": None,
    "limit": None,
    "gen_kwargs": {},
}
for key, expected in expected_run_values.items():
    if key not in run_config or run_config[key] != expected:
        fail(f"run config {key} is {run_config.get(key)!r}; expected {expected!r}")

for result_key, distribution in (
    ("lm_eval_version", "lm_eval"),
    ("transformers_version", "transformers"),
):
    expected = version(distribution)
    if result.get(result_key) != expected:
        fail(f"{result_key} is {result.get(result_key)!r}; expected {expected!r}")

if result.get("chat_template_sha") != manifest["protocol"]["chat_template_sha"]:
    fail("saved chat template does not match the declared Qwen template")
if result.get("fewshot_as_multiturn") is not False:
    fail("few-shot examples were formatted as multiple chat turns")
if result.get("n-shot", {}).get(TASK_NAME) != manifest["protocol"]["num_fewshot"]:
    fail("saved few-shot count differs from the final protocol")
if "system_instruction" not in result or result["system_instruction"] is not None:
    fail("an undeclared system instruction was applied")

task_config = result.get("configs", {}).get(TASK_NAME, {})
expected_task_values = {
    "task": TASK_NAME,
    "test_split": "test",
    "doc_to_target": "expected_call",
    "num_fewshot": 0,
    "output_type": "generate_until",
    "generation_kwargs": EXPECTED_GENERATION,
    "repeats": 1,
}
for key, expected in expected_task_values.items():
    if key not in task_config or task_config[key] != expected:
        fail(f"task config {key} is {task_config.get(key)!r}; expected {expected!r}")
data_file = task_config.get("dataset_kwargs", {}).get("data_files", {}).get("test")
if data_file != manifest["dataset"]["path"]:
    fail(f"task used dataset {data_file!r}; expected {manifest['dataset']['path']!r}")
metric_names = [metric.get("metric") for metric in task_config.get("metric_list", [])]
if metric_names != list(METRICS):
    fail(f"task metrics are {metric_names!r}; expected {list(METRICS)!r}")
if task_config.get("metadata", {}).get("split") != "final_test":
    fail("task metadata does not identify the final_test split")

effective_samples = result.get("n-samples", {}).get(TASK_NAME, {}).get("effective")
expected_samples = policy["effective_samples"]
if effective_samples != expected_samples:
    fail(
        f"effective sample count is {effective_samples!r}; "
        f"expected {expected_samples}"
    )
if not result.get("task_hashes", {}).get(TASK_NAME):
    fail("result does not record a task hash")

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

if not result_path.name.startswith("results_") or result_path.suffix != ".json":
    fail(f"unexpected result filename {result_path.name}")
timestamp = result_path.stem[len("results_") :]
samples_path = result_path.with_name(f"samples_{TASK_NAME}_{timestamp}.jsonl")
if not samples_path.exists():
    fail(f"sample evidence is missing: {samples_path}")

samples = [json.loads(line) for line in samples_path.read_text().splitlines()]
expected_docs = [
    json.loads(line) for line in FINAL_DATA.read_text().splitlines() if line.strip()
]
if len(samples) != len(expected_docs):
    fail(f"sample log contains {len(samples)} records; expected {len(expected_docs)}")
if {row["doc"]["id"] for row in samples} != {row["id"] for row in expected_docs}:
    fail("sample evidence does not contain the declared final-holdout case IDs")
expected_by_id = {row["id"]: row for row in expected_docs}
for sample in samples:
    if sample["doc"] != expected_by_id[sample["doc"]["id"]]:
        fail(f"saved document differs from final input {sample['doc']['id']}")

sample_hashes = [
    sample["doc_hash"] + sample["prompt_hash"] + sample["target_hash"]
    for sample in samples
]
recomputed_task_hash = hashlib.sha256("".join(sample_hashes).encode()).hexdigest()
if result["task_hashes"][TASK_NAME] != recomputed_task_hash:
    fail("saved task hash does not match the sample evidence")

values = {metric: [] for metric in METRICS}
for sample in samples:
    recomputed = process_results(sample["doc"], sample["filtered_resps"])
    for metric in METRICS:
        if sample.get(metric) != recomputed[metric]:
            fail(f"stored grade differs from recomputed {metric} for {sample['doc']['id']}")
        values[metric].append(recomputed[metric])

aggregate = result["results"][TASK_NAME]
print("| Metric | Final score | Minimum |")
print("|---|---:|---:|")
below_minimum = []
for metric in METRICS:
    actual = aggregate.get(f"{metric},none")
    recomputed_mean = sum(values[metric]) / len(values[metric])
    if actual != recomputed_mean:
        fail(f"aggregate {metric} is {actual!r}; recomputed mean is {recomputed_mean!r}")
    minimum = policy["minimum_metrics"][metric]
    print(f"| {metric} | {actual:.0%} | {minimum:.0%} |")
    if actual < minimum:
        below_minimum.append(f"{metric}={actual:.0%} < {minimum:.0%}")

print(f"Final evidence verified for source commit {head}.")
print(f"Release ID: {args.release_id}")
print(f"Sample evidence: {samples_path}")
if below_minimum:
    fail("release decision is FAIL: " + "; ".join(below_minimum))
print("Final release decision: PASS")
