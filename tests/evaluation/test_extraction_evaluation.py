"""Offline tests for the synthetic structured-extraction evaluation."""

from __future__ import annotations

from pathlib import Path

from healthcare_support.evaluation import evaluate_extraction


def test_golden_dataset_is_versioned_and_meets_baseline() -> None:
    dataset = Path(__file__).with_name("golden_extraction.json")
    result = evaluate_extraction(dataset)

    assert result["version"] == "1.0"
    assert result["cases"] == 5
    assert result["field_accuracy"] >= 0.95
    assert result["failures"] == []
