"""Deterministic, fail-closed verdict aggregation and report rendering.

Rendering emits only criterion names, statuses, sanitized details, and
remediation text — never raw command output, secret values, or PII
(constitution Principles I and II).
"""

from __future__ import annotations

import json

from healthcare_support.readiness.models import (
    CriterionResult,
    CriterionStatus,
    ReadinessReport,
    Verdict,
)

_CATEGORY_ORDER = ("tests", "quality-gates", "deployment", "security")

_STATUS_LABEL = {
    CriterionStatus.PASS: "PASS",
    CriterionStatus.FAIL: "FAIL",
    CriterionStatus.UNABLE_TO_VERIFY: "UNABLE TO VERIFY",
}


def compute_verdict(results: list[CriterionResult]) -> Verdict:
    """Return READY only if every criterion passed; otherwise NOT_READY."""
    if results and all(r.status == CriterionStatus.PASS for r in results):
        return Verdict.READY
    return Verdict.NOT_READY


def render_text(report: ReadinessReport) -> str:
    """Render a human-readable report grouped by category."""
    lines: list[str] = []
    ordered = sorted(
        report.results,
        key=lambda r: (
            _CATEGORY_ORDER.index(r.category)
            if r.category in _CATEGORY_ORDER
            else len(_CATEGORY_ORDER),
            r.name,
        ),
    )
    current_category: str | None = None
    for result in ordered:
        if result.category != current_category:
            current_category = result.category
            lines.append("")
            lines.append(f"[{current_category}]")
        lines.append(f"  {_STATUS_LABEL[result.status]:<18} {result.name}: {result.details}")
        if result.status != CriterionStatus.PASS:
            lines.append(f"    -> fix: {result.remediation}")
    lines.append("")
    verdict_label = (
        "LAUNCH READINESS: READY"
        if report.verdict == Verdict.READY
        else "LAUNCH READINESS: NOT READY"
    )
    lines.append(verdict_label)
    return "\n".join(lines)


def render_json(report: ReadinessReport) -> str:
    """Render the report as JSON matching contracts/cli-schema.md."""
    payload = {
        "verdict": report.verdict.value,
        "run_at": report.run_at.isoformat(),
        "results": [r.model_dump(mode="json") for r in report.results],
    }
    return json.dumps(payload, indent=2)
