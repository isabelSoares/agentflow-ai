"""Unit tests for readiness Pydantic models (offline, no external services)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from healthcare_support.readiness.models import (
    CriterionResult,
    CriterionStatus,
    ReadinessReport,
    Verdict,
)


def _result(status: CriterionStatus, remediation: str = "") -> CriterionResult:
    return CriterionResult(
        name="lint",
        category="quality-gates",
        status=status,
        details="some details",
        remediation=remediation if status != CriterionStatus.PASS else "",
    )


def test_pass_result_needs_no_remediation() -> None:
    result = _result(CriterionStatus.PASS)
    assert result.status == CriterionStatus.PASS
    assert result.remediation == ""


@pytest.mark.parametrize("status", [CriterionStatus.FAIL, CriterionStatus.UNABLE_TO_VERIFY])
def test_non_pass_result_requires_remediation(status: CriterionStatus) -> None:
    with pytest.raises(ValidationError):
        _result(status, remediation="")
    ok = _result(status, remediation="run the gate command")
    assert ok.remediation == "run the gate command"


def test_details_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        CriterionResult(
            name="lint",
            category="quality-gates",
            status=CriterionStatus.PASS,
            details="",
        )


def test_verdict_ready_only_when_all_pass() -> None:
    report = ReadinessReport(results=[_result(CriterionStatus.PASS)])
    assert report.verdict == Verdict.READY


@pytest.mark.parametrize("status", [CriterionStatus.FAIL, CriterionStatus.UNABLE_TO_VERIFY])
def test_verdict_not_ready_on_any_non_pass(status: CriterionStatus) -> None:
    report = ReadinessReport(
        results=[_result(CriterionStatus.PASS), _result(status, remediation="fix it")]
    )
    assert report.verdict == Verdict.NOT_READY


def test_report_requires_at_least_one_result() -> None:
    with pytest.raises(ValidationError):
        ReadinessReport(results=[])
