"""Pydantic models for launch readiness reports.

The report schema structurally cannot carry secret values or PII
(constitution Principle I): it only has criterion names, statuses,
sanitized details, and remediation text.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Verdict(StrEnum):
    """Overall launch verdict."""

    READY = "ready"
    NOT_READY = "not_ready"


class CriterionStatus(StrEnum):
    """Outcome of a single go/no-go criterion."""

    PASS = "pass"
    FAIL = "fail"
    UNABLE_TO_VERIFY = "unable_to_verify"


class CriterionResult(BaseModel):
    """The outcome for one go/no-go area.

    ``details`` and ``remediation`` MUST NOT contain secret values,
    credentials, or patient PII — only names, paths, and guidance.
    """

    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    status: CriterionStatus
    details: str = Field(min_length=1)
    remediation: str = ""

    @model_validator(mode="after")
    def _remediation_required_when_not_passing(self) -> CriterionResult:
        if self.status != CriterionStatus.PASS and not self.remediation.strip():
            raise ValueError(
                f"criterion {self.name!r} has status {self.status.value!r} "
                "but no remediation guidance"
            )
        return self


class ReadinessReport(BaseModel):
    """The overall output of one readiness check run.

    ``verdict`` is derived deterministically: ``ready`` iff every
    criterion result is ``pass`` (fail-closed).
    """

    run_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    results: list[CriterionResult] = Field(min_length=1)

    @property
    def verdict(self) -> Verdict:
        if all(r.status == CriterionStatus.PASS for r in self.results):
            return Verdict.READY
        return Verdict.NOT_READY
