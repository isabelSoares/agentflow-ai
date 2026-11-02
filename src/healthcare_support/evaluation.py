"""Offline evaluation helpers for synthetic structured extraction cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIELDS = ("intent", "name", "phone", "date_of_birth", "secret_answer")


def evaluate_extraction(path: Path) -> dict[str, Any]:
    """Compare synthetic predictions with expected structured fields."""
    dataset = json.loads(path.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    comparisons = [
        (field, case["expected"].get(field), case["prediction"].get(field))
        for case in cases
        for field in FIELDS
    ]
    correct = sum(expected == actual for _, expected, actual in comparisons)
    failures = [
        {"case": case["id"], "category": case["category"], "field": field}
        for case in cases
        for field in FIELDS
        if case["expected"].get(field) != case["prediction"].get(field)
    ]
    return {
        "version": dataset["version"],
        "cases": len(cases),
        "field_accuracy": correct / len(comparisons) if comparisons else 1.0,
        "failures": failures,
    }
