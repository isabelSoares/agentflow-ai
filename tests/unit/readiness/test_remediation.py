"""US2 tests: every non-pass criterion must carry actionable remediation."""

from __future__ import annotations

import json

from healthcare_support.readiness import checks
from healthcare_support.readiness.models import CriterionResult, CriterionStatus, ReadinessReport
from healthcare_support.readiness.report import render_json, render_text


def test_every_catalog_criterion_has_remediation() -> None:
    catalog = [
        "offline-tests",
        "frontend-tests",
        "lint",
        "format",
        "type-check",
        "coverage-gate",
        "frontend-build",
        "deployment-config",
        "dependency-audit",
        "committed-secrets",
        "no-pii-in-boundary",
    ]
    for name in catalog:
        assert name in checks.REMEDIATION, name
        assert checks.REMEDIATION[name].strip(), name


def test_failed_results_include_remediation_in_both_formats() -> None:
    failing = CriterionResult(
        name="offline-tests",
        category="tests",
        status=CriterionStatus.FAIL,
        details="3 tests failed",
        remediation=checks.REMEDIATION["offline-tests"],
    )
    report = ReadinessReport(results=[failing])
    text = render_text(report)
    payload = json.loads(render_json(report))
    assert checks.REMEDIATION["offline-tests"] in text
    assert payload["results"][0]["remediation"] == checks.REMEDIATION["offline-tests"]
