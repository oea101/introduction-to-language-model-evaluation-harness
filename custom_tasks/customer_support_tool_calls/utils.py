import json
from typing import Any


TOOL_ARGUMENT_TYPES: dict[str, dict[str, type]] = {
    "track_order": {"order_id": str},
    "cancel_order": {"order_id": str},
    "create_replacement": {
        "order_id": str,
        "sku": str,
        "quantity": int,
    },
    "issue_refund": {
        "order_id": str,
        "amount_cents": int,
        "reason": str,
    },
    "escalate_to_human": {"reason": str},
}

ALLOWED_ARGUMENT_VALUES: dict[tuple[str, str], set[str]] = {
    ("issue_refund", "reason"): {"damaged_item", "duplicate_charge"},
    ("escalate_to_human", "reason"): {
        "customer_requested_human",
        "suspected_fraud",
    },
}


def _has_expected_type(value: Any, expected_type: type) -> bool:
    if expected_type is int:
        return type(value) is int
    return isinstance(value, expected_type)


def _has_valid_tool_schema(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"name", "arguments"}:
        return False

    name = value["name"]
    arguments = value["arguments"]
    if not isinstance(name, str) or not isinstance(arguments, dict):
        return False

    expected_types = TOOL_ARGUMENT_TYPES.get(name)
    if expected_types is None or set(arguments) != set(expected_types):
        return False

    for argument_name, expected_type in expected_types.items():
        argument_value = arguments[argument_name]
        if not _has_expected_type(argument_value, expected_type):
            return False

        allowed_values = ALLOWED_ARGUMENT_VALUES.get((name, argument_name))
        if allowed_values is not None and argument_value not in allowed_values:
            return False

    return True


def process_results(doc: dict[str, Any], results: list[Any]) -> dict[str, float]:
    expected = json.loads(doc["expected_call"])
    raw_response = results[0]

    try:
        actual = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        return {
            "valid_json": 0.0,
            "valid_tool_schema": 0.0,
            "correct_tool": 0.0,
            "correct_arguments": 0.0,
            "exact_tool_call": 0.0,
        }

    valid_tool_schema = _has_valid_tool_schema(actual)
    correct_tool = isinstance(actual, dict) and actual.get("name") == expected["name"]
    correct_arguments = (
        isinstance(actual, dict)
        and actual.get("arguments") == expected["arguments"]
    )
    exact_tool_call = valid_tool_schema and actual == expected

    return {
        "valid_json": 1.0,
        "valid_tool_schema": float(valid_tool_schema),
        "correct_tool": float(correct_tool),
        "correct_arguments": float(correct_arguments),
        "exact_tool_call": float(exact_tool_call),
    }
