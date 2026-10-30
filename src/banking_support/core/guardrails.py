"""Deterministic guardrail business logic for the banking assistant.

The ``GuardrailEvaluator`` is a pure, stateless service that enforces
authentication, authorization, banking policy, input safety, output safety,
and privacy rules. It performs no I/O and uses the LLM only through an
optional heuristic wrapper that cannot override deterministic decisions.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from banking_support.domain.conversation import (
    ConversationStatus,
    CustomerClassification,
)
from banking_support.domain.guardrails import (
    BankingPolicyRule,
    GuardrailDecisionOutcome,
    GuardrailInput,
    GuardrailOutput,
    SensitiveDataCategory,
)


class GuardrailEvaluator:
    """Evaluate customer inputs and assistant outputs against security rules."""

    # Deterministic manipulation patterns (constitution Principle II).
    _MANIPULATION_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"ignore\b.*?\b(instructions|rules)\b", re.IGNORECASE),
        re.compile(r"forget\b.*?\b(instructions|rules)\b", re.IGNORECASE),
        re.compile(r"disregard\b.*?\b(instructions|rules)\b", re.IGNORECASE),
        re.compile(r"you\s+are\s+(now|actually)\s+(an?|the)\s+\w+", re.IGNORECASE),
        re.compile(r"you\s+must\s+(now|instead)\s+", re.IGNORECASE),
        re.compile(r"bypass\s+(the\s+)?(rules|guardrails|security)", re.IGNORECASE),
        re.compile(r"act\s+as\s+(an?|the)\s+\w+", re.IGNORECASE),
    ]

    _INTERNAL_DISCLOSURE_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"\b(system\s+)?prompt\b", re.IGNORECASE),
        re.compile(r"\b(api\s+key|apikey|secret\s+key|password|credentials?)\b", re.IGNORECASE),
        re.compile(
            r"\b(internal\s+implementation|source\s+code|system\s+instructions)\b", re.IGNORECASE
        ),
        re.compile(
            r"\b(reveal|show|tell\s+me)\s+(my|the)\s+(secret\s+answer|password|pin)\b",
            re.IGNORECASE,
        ),
    ]

    _PROHIBITED_COMMITMENT_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"\b(approved?|guaranteed|confirmed|completed|executed)\b", re.IGNORECASE),
        re.compile(
            r"\b(your\s+(loan|insurance|credit\s+card)\s+(is\s+)?approved)\b", re.IGNORECASE
        ),
        re.compile(r"\b(guaranteed\s+(rate|return|approval|eligibility))\b", re.IGNORECASE),
        re.compile(r"\b(transfer\s+(completed|sent|executed))\b", re.IGNORECASE),
    ]

    _SENSITIVE_PATTERNS: dict[SensitiveDataCategory, re.Pattern[str]] = {
        SensitiveDataCategory.IBAN: re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}"),
        SensitiveDataCategory.PHONE_NUMBER: re.compile(r"(?:\+|00)\d[\d\s\-/]{7,20}"),
        SensitiveDataCategory.CREDENTIAL: re.compile(
            r"\b(sk-[a-zA-Z0-9]{20,}|api[_-]?key\s*[:=]\s*\S+)", re.IGNORECASE
        ),
    }

    def __init__(
        self,
        policy_rules: dict[str, BankingPolicyRule] | None = None,
        heuristic_input_checker: Callable[[GuardrailInput], bool | str | GuardrailOutput | None]
        | None = None,
        heuristic_output_checker: Callable[[GuardrailInput], bool | str | GuardrailOutput | None]
        | None = None,
        safe_replies: dict[str, str] | None = None,
    ) -> None:
        """Initialize the evaluator with trusted policy rules and optional checkers."""
        self._policy_rules = policy_rules or {}
        self._heuristic_input_checker = heuristic_input_checker
        self._heuristic_output_checker = heuristic_output_checker
        self._safe_replies = safe_replies or {}

    def evaluate(self, input_: GuardrailInput) -> GuardrailOutput:
        """Return a guardrails decision for the given input.

        Deterministic checks run first and cannot be overridden by heuristic
        checks. Heuristic checks degrade gracefully on failure.
        """
        try:
            if input_.content_type == "customer_input":
                return self._evaluate_input(input_)
            return self._evaluate_output(input_)
        except Exception:
            # Deterministic mandatory checks must fail closed (US6).
            return self._blocked(
                input_,
                reason="check_unavailable",
                reply_key="unavailable",
            )

    def _evaluate_input(self, input_: GuardrailInput) -> GuardrailOutput:
        # 1. Input safety (US1) - deterministic.
        result = self._check_input_safety(input_)
        if result is not None:
            return result

        # 2. Authentication and authorization (US2) + banking policy (US3).
        # When support_intent is available we can enforce full auth/authz/policy.
        # Otherwise we only block obvious pre-authentication data requests.
        if input_.support_intent is not None:
            result = self._check_authentication(input_)
            if result is not None:
                return result

            result = self._check_authorization(input_)
            if result is not None:
                return result

            result = self._check_banking_policy(input_)
            if result is not None:
                return result
        else:
            result = self._check_obvious_data_request(input_)
            if result is not None:
                return result

        # 3. Optional heuristic input safety check (US1/US6).
        if self._heuristic_input_checker is not None:
            try:
                heuristic_result = self._heuristic_input_checker(input_)
                block_output = self._interpret_heuristic_result(
                    input_,
                    heuristic_result,
                    default_reason="prompt_injection",
                    default_reply_key="manipulation",
                )
                if block_output is not None:
                    return block_output
            except Exception:
                return self._allowed(input_, audit_reason="heuristic_degraded")

        return self._allowed(input_)

    def _evaluate_output(self, input_: GuardrailInput) -> GuardrailOutput:
        # 1. Output safety / privacy (US4).
        result = self._check_output_safety(input_)
        if result is not None:
            return result

        # 2. Optional heuristic output check (US4/US6).
        if self._heuristic_output_checker is not None:
            try:
                heuristic_result = self._heuristic_output_checker(input_)
                block_output = self._interpret_heuristic_result(
                    input_,
                    heuristic_result,
                    default_reason="privacy_violation",
                    default_reply_key="privacy",
                )
                if block_output is not None:
                    return block_output
            except Exception:
                return self._allowed(input_, audit_reason="heuristic_degraded")

        return self._allowed(input_)

    def _check_input_safety(self, input_: GuardrailInput) -> GuardrailOutput | None:
        text = input_.content.strip()
        if not text:
            return self._blocked(input_, reason="empty_input", reply_key="manipulation")

        lowered = text.casefold()
        for pattern in self._MANIPULATION_PATTERNS:
            if pattern.search(lowered):
                return self._blocked(
                    input_,
                    reason="prompt_injection",
                    reply_key="manipulation",
                )

        for pattern in self._INTERNAL_DISCLOSURE_PATTERNS:
            if pattern.search(lowered):
                return self._blocked(
                    input_,
                    reason="internal_disclosure",
                    reply_key="internal_disclosure",
                )

        return None

    def _check_obvious_data_request(self, input_: GuardrailInput) -> GuardrailOutput | None:
        # Only apply at the entry guardrail before intent extraction.
        if input_.content_type != "customer_input" or input_.support_intent is not None:
            return None

        # Authenticated customers may proceed; non-customer/unauthenticated are
        # blocked only when they ask for personalized data.
        if input_.status == ConversationStatus.AUTHENTICATED:
            classification = input_.customer_classification
            if classification is None or not isinstance(classification, CustomerClassification):
                classification = None
            if classification == CustomerClassification.NON_CUSTOMER:
                return self._blocked(
                    input_,
                    reason="unauthenticated",
                    reply_key="non_customer",
                )
            return None

        lowered = input_.content.casefold()
        data_request_phrases = [
            r"\b(what\s+is\s+my\s+(balance|iban|phone|number|details))\b",
            r"\b(show\s+me\s+my\s+(balance|iban|phone|number|details))\b",
            r"\b(tell\s+me\s+my\s+(balance|iban|phone|number|details))\b",
            r"\b(reveal\s+my\s+(balance|iban|phone|number|details))\b",
            r"\b(give\s+me\s+my\s+(balance|iban|phone|number|details))\b",
        ]
        for phrase in data_request_phrases:
            if re.search(phrase, lowered):
                return self._blocked(
                    input_,
                    reason="unauthenticated",
                    reply_key="data_request_refusal",
                )

        return None

    def _check_authentication(self, input_: GuardrailInput) -> GuardrailOutput | None:
        classification = input_.customer_classification
        if classification is not None and not isinstance(classification, CustomerClassification):
            classification = None

        if input_.status != ConversationStatus.AUTHENTICATED or classification is None:
            return self._blocked(
                input_,
                reason="unauthenticated",
                reply_key="data_request_refusal",
            )

        if classification == CustomerClassification.NON_CUSTOMER:
            return self._blocked(
                input_,
                reason="unauthenticated",
                reply_key="non_customer",
            )

        return None

    def _check_authorization(self, input_: GuardrailInput) -> GuardrailOutput | None:
        classification = input_.customer_classification
        if classification is None or not isinstance(classification, CustomerClassification):
            return None

        action_type = self._action_type_from_intent(input_.support_intent)
        if action_type is None:
            return None

        rule = self._policy_rules.get(action_type)
        if rule is not None and classification not in rule.allowed_tiers:
            return self._blocked(
                input_,
                reason="premium_restriction",
                reply_key="premium_restriction",
            )

        return None

    def _check_banking_policy(self, input_: GuardrailInput) -> GuardrailOutput | None:
        action_type = self._action_type_from_intent(input_.support_intent)
        if action_type is None:
            return None

        rule = self._policy_rules.get(action_type)
        content = input_.content.casefold()

        # Prohibited commitments and execution language are always blocked,
        # regardless of policy existence.
        if self._has_prohibited_commitment(content) or self._has_execution_language(content):
            return self._blocked(
                input_,
                reason="prohibited_financial_action",
                reply_key="prohibited_action",
            )

        if rule is None:
            return None

        return None

    def _check_output_safety(self, input_: GuardrailInput) -> GuardrailOutput | None:
        content = input_.content

        # Detect unauthorized financial commitments in output.
        if self._has_prohibited_commitment(content.casefold()):
            return self._blocked(
                input_,
                reason="unauthorized_commitment",
                reply_key="prohibited_action",
            )

        # Detect internal disclosures.
        for pattern in self._INTERNAL_DISCLOSURE_PATTERNS:
            if pattern.search(content):
                return self._blocked(
                    input_,
                    reason="internal_disclosure",
                    reply_key="internal_disclosure",
                )

        # Detect exposure of known customer-sensitive values.
        leaked_values = self._find_leaked_sensitive_values(input_)
        if leaked_values:
            sanitized = self._sanitize_known_values(content, leaked_values)
            # Only block if the customer did not explicitly request the data.
            if not self._customer_requested_sensitive_data(input_):
                return self._blocked(
                    input_,
                    reason="privacy_violation",
                    reply_key="privacy",
                    sanitized_content=sanitized,
                )
            return GuardrailOutput(
                outcome=GuardrailDecisionOutcome.ALLOWED,
                reason_category="allowed",
                sanitized_content=sanitized,
            )

        return None

    def _action_type_from_intent(self, intent: Any | None) -> str | None:
        from banking_support.domain.routing import SupportIntent

        if intent is None:
            return "general_inquiry"

        mapping = {
            SupportIntent.ACCOUNT_ASSISTANCE: "balance_inquiry",
            SupportIntent.GENERAL_BANKING: "general_inquiry",
            SupportIntent.INSURANCE: "insurance_request",
            SupportIntent.PREMIUM_BANKING: "premium_banking",
            SupportIntent.YACHT_INSURANCE: "insurance_request",
            SupportIntent.OTHER_SPECIALIZED: "general_inquiry",
            SupportIntent.AMBIGUOUS: "general_inquiry",
            SupportIntent.UNSUPPORTED: "general_inquiry",
            SupportIntent.UNINTERPRETABLE: "general_inquiry",
        }
        return mapping.get(intent)

    def _has_prohibited_commitment(self, content: str) -> bool:
        return any(pattern.search(content) for pattern in self._PROHIBITED_COMMITMENT_PATTERNS)

    def _has_execution_language(self, content: str) -> bool:
        execution_terms = [
            r"\b(execute|process|make|send|transfer|withdraw|deposit)\b.*\b(now|immediately|today)\b",
            r"\b(approve\s+(my|the|this))\b",
            r"\b(complete\s+.*?(transfer|modification|application))\b",
            r"\b(process\s+.*?(transfer|application|modification|payment))\b",
        ]
        return any(re.search(term, content, re.IGNORECASE) for term in execution_terms)

    def _find_leaked_sensitive_values(self, input_: GuardrailInput) -> list[str]:
        """Return sensitive values from the input that appear in the content."""
        leaked: list[str] = []
        for value in input_.sensitive_values:
            if value and value in input_.content:
                leaked.append(value)
        # Also flag IBANs and credentials that are not known values (defense in depth).
        for category, pattern in self._SENSITIVE_PATTERNS.items():
            if category in {SensitiveDataCategory.IBAN, SensitiveDataCategory.CREDENTIAL}:
                for match in pattern.finditer(input_.content):
                    value = match.group(0)
                    if value not in input_.sensitive_values:
                        leaked.append(value)
        return leaked

    def _sanitize_known_values(self, content: str, values: list[str]) -> str:
        sanitized = content
        for value in values:
            sanitized = sanitized.replace(value, "[REDACTED]")
        return sanitized

    def _sanitize_content(self, content: str) -> str:
        sanitized = content
        for category, pattern in self._SENSITIVE_PATTERNS.items():
            if category == SensitiveDataCategory.CREDENTIAL:
                sanitized = pattern.sub("[REDACTED]", sanitized)
            else:
                sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized

    def _customer_requested_sensitive_data(self, input_: GuardrailInput) -> bool:
        # Heuristic: if the most recent customer message explicitly asks for
        # account/IBAN/phone/balance, treat the output as an authorized disclosure.
        for message in reversed(input_.messages):
            if message.type == "human":
                text = str(message.content).casefold()
                request_phrases = [
                    "what is my iban",
                    "tell me my iban",
                    "show me my iban",
                    "what is my phone",
                    "tell me my phone",
                    "what is my balance",
                    "show me my balance",
                    "what is my account",
                ]
                return any(phrase in text for phrase in request_phrases)
        return False

    def _interpret_heuristic_result(
        self,
        input_: GuardrailInput,
        result: bool | str | GuardrailOutput | None,
        *,
        default_reason: str,
        default_reply_key: str,
    ) -> GuardrailOutput | None:
        """Convert a heuristic checker result into a guardrail decision.

        Supports legacy ``bool`` returns, reason-category strings, and full
        ``GuardrailOutput`` objects returned by advanced guardrails.
        """
        if result is None or result is False:
            return None
        if result is True:
            return self._blocked(
                input_,
                reason=default_reason,
                reply_key=default_reply_key,
            )
        if isinstance(result, str):
            return self._blocked(
                input_,
                reason=result,
                reply_key=result if result in self._safe_replies else "unavailable",
            )
        if isinstance(result, GuardrailOutput):
            return result
        return None

    def _blocked(
        self,
        input_: GuardrailInput,
        *,
        reason: str,
        reply_key: str,
        sanitized_content: str | None = None,
    ) -> GuardrailOutput:
        safe_reply = self._safe_replies.get(reply_key, self._safe_replies.get("unavailable"))
        if safe_reply is None:
            safe_reply = "I'm not able to help with that request."
        return GuardrailOutput(
            outcome=GuardrailDecisionOutcome.BLOCKED,
            reason_category=reason,
            safe_reply=safe_reply,
            sanitized_content=sanitized_content,
            audit_metadata={"content_type": input_.content_type},
        )

    def _allowed(
        self,
        input_: GuardrailInput,
        *,
        audit_reason: str = "allowed",
    ) -> GuardrailOutput:
        return GuardrailOutput(
            outcome=GuardrailDecisionOutcome.ALLOWED,
            reason_category=audit_reason,
            audit_metadata={"content_type": input_.content_type},
        )


__all__ = ["GuardrailEvaluator"]
