#!/usr/bin/env python3
"""Validate the final holdout contract at the explicit release gate."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from custom_tasks.customer_support_tool_calls.utils import process_results  # noqa: E402


DATA_DIR = PROJECT_DIR / "custom_tasks/customer_support_tool_calls/data"


def read_rows(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (DATA_DIR / name).read_text().splitlines()
        if line.strip()
    ]


development = read_rows("development.jsonl")
regression = read_rows("regression.jsonl")
final_test = read_rows("final_test.jsonl")

if len(final_test) != 10:
    raise SystemExit(f"Final holdout must contain 10 cases; found {len(final_test)}.")
if len({row["id"] for row in final_test}) != len(final_test):
    raise SystemExit("Final holdout contains duplicate case IDs.")
if len({row["message"] for row in final_test}) != len(final_test):
    raise SystemExit("Final holdout contains duplicate customer messages.")

earlier = development + regression
earlier_ids = {row["id"] for row in earlier}
earlier_messages = {row["message"] for row in earlier}
if earlier_ids & {row["id"] for row in final_test}:
    raise SystemExit("Final holdout reuses an earlier case ID.")
if earlier_messages & {row["message"] for row in final_test}:
    raise SystemExit("Final holdout reuses an earlier customer message.")

expected_categories = {
    "tracking": 2,
    "cancellation": 2,
    "replacement": 2,
    "refund": 2,
    "escalation": 2,
}
actual_categories = dict(Counter(row["category"] for row in final_test))
if actual_categories != expected_categories:
    raise SystemExit(
        f"Final holdout category balance is {actual_categories}; "
        f"expected {expected_categories}."
    )

for row in final_test:
    scores = process_results(row, [row["expected_call"]])
    if set(scores.values()) != {1.0}:
        raise SystemExit(f"Invalid expected call for final case {row['id']}.")

print("Final holdout contract verified for 10 release-only cases.")
