#!/usr/bin/env python3
"""Print the latest Milestone 9 regression model comparison as Markdown."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
TASK_NAME = "customer_support_tool_calls_regression"
METRICS = (
    "valid_json",
    "valid_tool_schema",
    "correct_tool",
    "correct_arguments",
    "exact_tool_call",
)
CONDITIONS = {
    "Pythia-70M, plain prompt": (
        PROJECT_DIR
        / "results/milestone-09/customer-support-tool-calls-regression"
        / "EleutherAI__pythia-70m"
    ),
    "Qwen2.5-0.5B-Instruct, plain prompt": (
        PROJECT_DIR
        / "results/milestone-09/model-comparison"
        / "qwen2.5-0.5b-instruct-raw-prompt-regression"
        / "Qwen__Qwen2.5-0.5B-Instruct"
    ),
    "Qwen2.5-0.5B-Instruct, chat template": (
        PROJECT_DIR
        / "results/milestone-09/model-comparison"
        / "qwen2.5-0.5b-instruct-regression"
        / "Qwen__Qwen2.5-0.5B-Instruct"
    ),
}


def latest(directory: Path, pattern: str) -> Path:
    matches = list(directory.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No {pattern} file found under {directory}")
    return max(matches, key=lambda path: path.stat().st_mtime)


def load_condition(directory: Path) -> tuple[dict, dict[str, dict]]:
    result = json.loads(latest(directory, "results_*.json").read_text())
    samples_path = latest(directory, "samples_*.jsonl")
    samples = {
        row["doc"]["id"]: row
        for row in map(json.loads, samples_path.read_text().splitlines())
    }
    return result, samples


loaded = {name: load_condition(path) for name, path in CONDITIONS.items()}
baseline_name = next(iter(CONDITIONS))
baseline_samples = loaded[baseline_name][1]

for condition, (_, samples) in loaded.items():
    if samples.keys() != baseline_samples.keys():
        raise ValueError(f"{condition} evaluated a different set of case IDs")
    for case_id, baseline in baseline_samples.items():
        sample = samples[case_id]
        if sample["doc"] != baseline["doc"] or sample["target"] != baseline["target"]:
            raise ValueError(f"{condition} changed document or target for {case_id}")

print("| Condition | Same plain prompt as baseline | " + " | ".join(METRICS) + " |")
print("|---|:---:|" + "---:|" * len(METRICS))
baseline_prompt_hashes = {
    case_id: sample["prompt_hash"] for case_id, sample in baseline_samples.items()
}
for condition, (result, samples) in loaded.items():
    aggregate = result["results"][TASK_NAME]
    same_prompt = all(
        sample["prompt_hash"] == baseline_prompt_hashes[case_id]
        for case_id, sample in samples.items()
    )
    values = [f'{aggregate[f"{metric},none"]:.0%}' for metric in METRICS]
    print(
        f"| {condition} | {'yes' if same_prompt else 'no'} | "
        + " | ".join(values)
        + " |"
    )

print("\n| Case | " + " | ".join(CONDITIONS) + " |")
print("|---|" + ":---:|" * len(CONDITIONS))
for case_id in baseline_samples:
    outcomes = [
        "pass" if samples[case_id]["exact_tool_call"] == 1.0 else "fail"
        for _, samples in loaded.values()
    ]
    print(f"| {case_id} | " + " | ".join(outcomes) + " |")
