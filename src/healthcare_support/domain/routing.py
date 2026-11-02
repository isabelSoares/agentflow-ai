"""Routing domain: intents, departments, and deterministic routing decisions.

No patient PII or secret data appears in these models. They represent only
approved support destinations and the untrusted, structured intent produced by
the classifier.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SupportIntent(StrEnum):
    """Normalized support intent values.

    These values are classification vocabulary only. They do not grant access,
    determine membership, or select arbitrary departments.
    """

    APPOINTMENT_ASSISTANCE = "appointment_assistance"
    GENERAL_HEALTHCARE = "general_healthcare"
    INSURANCE = "insurance"
    PREMIUM_HEALTHCARE = "premium_healthcare"
    SPECIALIST_REFERRAL = "specialist_referral"
    OTHER_SPECIALIZED = "other_specialized"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"
    UNINTERPRETABLE = "uninterpretable"


class RoutingStatus(StrEnum):
    """Result status of a deterministic routing decision."""

    ROUTED = "routed"
    CLARIFICATION_REQUIRED = "clarification_required"
    FALLBACK = "fallback"
    BLOCKED = "blocked"


class IntentClassification(BaseModel):
    """Structured output from the support-intent classifier.

    The LLM may suggest an intent and a specialization key, but routing decisions
    are made deterministically by ``core.routing`` using the approved support
    directory.
    """

    model_config = ConfigDict(frozen=True)

    intent: SupportIntent = Field(default=SupportIntent.UNINTERPRETABLE)
    specialization: str | None = None
    needs_clarification: bool = False
    clarification_prompt: str | None = None

    @model_validator(mode="after")
    def _consistent_clarification(self) -> IntentClassification:
        if self.needs_clarification and not self.clarification_prompt:
            raise ValueError("clarification_prompt is required when needs_clarification is true")
        if self.intent == SupportIntent.AMBIGUOUS and not self.needs_clarification:
            raise ValueError("ambiguous intent must set needs_clarification=True")
        return self


class SupportDepartment(BaseModel):
    """Approved support destination."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    contact: str | None = None
    specializations: set[str] = Field(default_factory=set)
    available: bool = True

    @field_validator("specializations", mode="before")
    @classmethod
    def _coerce_specializations(cls, value: object) -> set[str]:
        if value is None:
            return set()
        if isinstance(value, (list, tuple, set)):
            return {str(item) for item in value}
        if isinstance(value, str):
            return {value}
        raise ValueError("specializations must be an iterable of strings")


class SupportDirectory(BaseModel):
    """Validated collection of approved support departments."""

    model_config = ConfigDict(frozen=True)

    departments: dict[str, SupportDepartment] = Field(default_factory=dict)

    @field_validator("departments", mode="before")
    @classmethod
    def _keyed_by_department_key(cls, value: object) -> dict[str, SupportDepartment]:
        if isinstance(value, dict):
            return value
        if isinstance(value, (list, tuple, set)):
            result: dict[str, SupportDepartment] = {}
            for dep in value:
                if not isinstance(dep, SupportDepartment):
                    dep = SupportDepartment.model_validate(dep)
                result[dep.key] = dep
            return result
        raise ValueError("departments must be a mapping or iterable of SupportDepartment")

    def get(self, key: str) -> SupportDepartment | None:
        return self.departments.get(key)

    def find_by_specialization(self, specialization: str | None) -> SupportDepartment | None:
        if specialization is None:
            return None
        for department in self.departments.values():
            if department.available and specialization in department.specializations:
                return department
        return None


class RoutingDecision(BaseModel):
    """Deterministic result shared by the graph and API boundary."""

    model_config = ConfigDict(frozen=True)

    status: RoutingStatus
    intent: SupportIntent
    department_key: str | None = None
    department_name: str | None = None
    contact: str | None = None
    message: str = Field(min_length=1)


__all__ = [
    "SupportIntent",
    "RoutingStatus",
    "IntentClassification",
    "SupportDepartment",
    "SupportDirectory",
    "RoutingDecision",
]
