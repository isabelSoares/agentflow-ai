"""Unit tests for verdict aggregation and report rendering (offline)."""

from __future__ import annotations

import json

from healthcare_support.readiness.models import (
    CriterionResult,
    CriterionStatus,
    ReadinessReport,
    Verdict,
)
from healthcare_support.readiness.report import compute_verdict, render_json, render_text


def _result(
    name: str,
    category: str,
    status: CriterionStatus,
    remediation: str = "",
) -> CriterionResult:
    return CriterionResult(
        name=name,
        category=category,
        status=status,
        details=f"details for {name}",
        remediation=remediation,
    )


def test_compute_verdict_fail_closed() -> None:
    assert compute_verdict([_result("a", "tests", CriterionStatus.PASS)]) == Verdict.READY
    assert (
        compute_verdict(
            [
                _result("a", "tests", CriterionStatus.PASS),
                _result("b", "security", CriterionStatus.UNABLE_TO_VERIFY, "fix"),
            ]
        )
        == Verdict.NOT_READY
    )
    assert compute_verdict([]) == Verdict.NOT_READY


def test_render_text_groups_and_verdict_line() -> None:
    report = ReadinessReport(
        results=[
            _result("lint", "quality-gates", CriterionStatus.PASS),
            _result("offline-tests", "tests", CriterionStatus.FAIL, "run pytest"),
        ]
    )
    text = render_text(report)
    assert "[tests]" in text and "[quality-gates]" in text
    assert "FAIL" in text and "-> fix: run pytest" in text
    assert text.rstrip().endswith("LAUNCH READINESS: NOT READY")


def test_render_text_ready_verdict_line() -> None:
    report = ReadinessReport(results=[_result("lint", "quality-gates", CriterionStatus.PASS)])
    assert render_text(report).rstrip().endswith("LAUNCH READINESS: READY")


def test_render_json_matches_contract_schema() -> None:
    report = ReadinessReport(
        results=[_result("lint", "quality-gates", CriterionStatus.FAIL, "run ruff")]
    )
    payload = json.loads(render_json(report))
    assert payload["verdict"] == "not_ready"
    assert "run_at" in payload
    assert payload["results"][0]["name"] == "lint"
    assert payload["results"][0]["status"] == "fail"
    assert payload["results"][0]["remediation"] == "run ruff"


def test_render_never_includes_raw_secret_values() -> None:
    secret = "AKIAIOSFODNN7EXAMPLE"
    report = ReadinessReport(
        results=[
            _result("committed-secrets", "security", CriterionStatus.FAIL, "rotate credential")
        ]
    )
    assert secret not in render_text(report)
    assert secret not in render_json(report)
