import json
import unittest
from pathlib import Path

from custom_tasks.customer_support_tool_calls.utils import process_results


DATA_DIR = (
    Path(__file__).parents[1]
    / "custom_tasks"
    / "customer_support_tool_calls"
    / "data"
)
SPLIT_FILES = {
    "development": DATA_DIR / "development.jsonl",
    "regression": DATA_DIR / "regression.jsonl",
}


TRACK_ORDER_DOC = {
    "expected_call": (
        '{"name":"track_order","arguments":{"order_id":"ORD-1042"}}'
    )
}


class ProcessResultsTests(unittest.TestCase):
    def test_exact_call(self):
        response = '{"name":"track_order","arguments":{"order_id":"ORD-1042"}}'
        self.assertEqual(
            process_results(TRACK_ORDER_DOC, [response]),
            {
                "valid_json": 1.0,
                "valid_tool_schema": 1.0,
                "correct_tool": 1.0,
                "correct_arguments": 1.0,
                "exact_tool_call": 1.0,
            },
        )

    def test_json_key_order_and_whitespace_do_not_matter(self):
        response = ' { "arguments": {"order_id": "ORD-1042"}, "name": "track_order" } '
        self.assertEqual(process_results(TRACK_ORDER_DOC, [response])["exact_tool_call"], 1.0)

    def test_invalid_json_fails_every_metric(self):
        scores = process_results(TRACK_ORDER_DOC, ["track_order(ORD-1042)"])
        self.assertEqual(set(scores.values()), {0.0})

    def test_wrong_tool_can_still_have_valid_schema(self):
        response = '{"name":"cancel_order","arguments":{"order_id":"ORD-1042"}}'
        scores = process_results(TRACK_ORDER_DOC, [response])
        self.assertEqual(scores["valid_tool_schema"], 1.0)
        self.assertEqual(scores["correct_tool"], 0.0)
        self.assertEqual(scores["correct_arguments"], 1.0)
        self.assertEqual(scores["exact_tool_call"], 0.0)

    def test_integer_arguments_reject_strings(self):
        doc = {
            "expected_call": (
                '{"name":"create_replacement","arguments":'
                '{"order_id":"ORD-3007","sku":"MUG-BLU","quantity":2}}'
            )
        }
        response = (
            '{"name":"create_replacement","arguments":'
            '{"order_id":"ORD-3007","sku":"MUG-BLU","quantity":"2"}}'
        )
        scores = process_results(doc, [response])
        self.assertEqual(scores["valid_json"], 1.0)
        self.assertEqual(scores["valid_tool_schema"], 0.0)
        self.assertEqual(scores["correct_tool"], 1.0)
        self.assertEqual(scores["correct_arguments"], 0.0)
        self.assertEqual(scores["exact_tool_call"], 0.0)


class DatasetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows_by_split = {
            split: [json.loads(line) for line in path.read_text().splitlines()]
            for split, path in SPLIT_FILES.items()
        }

    def test_split_sizes_are_intentional(self):
        self.assertEqual(
            {split: len(rows) for split, rows in self.rows_by_split.items()},
            {"development": 10, "regression": 5},
        )

    def test_ids_and_messages_do_not_cross_splits(self):
        rows = [row for split in self.rows_by_split.values() for row in split]
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        self.assertEqual(len({row["message"] for row in rows}), len(rows))

    def test_every_reference_is_an_exact_valid_call(self):
        for split, rows in self.rows_by_split.items():
            for row in rows:
                with self.subTest(split=split, id=row["id"]):
                    scores = process_results(row, [row["expected_call"]])
                    self.assertEqual(set(scores.values()), {1.0})

    def test_regressions_record_the_incident_and_failure_mode(self):
        for row in self.rows_by_split["regression"]:
            with self.subTest(id=row["id"]):
                self.assertTrue(row["provenance"].startswith("simulated_production_incident:"))
                self.assertTrue(row["failure_mode"])

if __name__ == "__main__":
    unittest.main()
