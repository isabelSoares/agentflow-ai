"""Advanced heuristic guardrail checks for the banking assistant.

The checks are rule-based so they run deterministically without a live LLM or
external service. They are wired into the existing ``GuardrailEvaluator`` via
its heuristic-checker hooks and can never override deterministic blocks.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Any, Literal

from langchain_core.messages import HumanMessage

from healthcare_support.config.context_whitelist import WORKFLOW_MESSAGE_PATTERNS
from healthcare_support.config.safe_replies import DEFAULT_ADVANCED_SAFE_REPLIES
from healthcare_support.config.sensitive_topics import SENSITIVE_TOPIC_PATTERNS
from healthcare_support.config.trusted_banking_info import get_catalog
from healthcare_support.domain.advanced_guardrails import (
    AdvancedGuardrailDecision,
    AdvancedGuardrailInput,
    CheckResult,
    CheckVerdict,
    ConversationContext,
    RedirectionState,
    TrustedBankingCatalog,
)
from healthcare_support.domain.conversation import ConversationStatus, CustomerClassification
from healthcare_support.domain.guardrails import (
    GuardrailDecisionOutcome,
    GuardrailInput,
    GuardrailOutput,
)


class RedirectionStateTracker:
    """In-memory tracker of consecutive off-topic customer turns."""

    def __init__(self, threshold: int = 2) -> None:
        self._threshold = threshold
        self._states: dict[str, RedirectionState] = {}

    def record(self, conversation_id: str, reason_category: str) -> RedirectionState:
        """Update the tracker for a guardrail decision."""
        state = self._states.get(conversation_id)
        if state is None:
            state = RedirectionState(
                conversation_id=conversation_id, redirection_threshold=self._threshold
            )

        new_count = state.consecutive_off_topic_count + 1 if reason_category == "off_topic" else 0

        updated = RedirectionState(
            conversation_id=conversation_id,
            consecutive_off_topic_count=new_count,
            redirection_threshold=self._threshold,
            last_safe_reply=state.last_safe_reply,
        )
        self._states[conversation_id] = updated
        return updated

    def reply_style(self, state: RedirectionState) -> str:
        """Return ``full`` or ``brief`` based on the current state."""
        return "brief" if state.consecutive_off_topic_count >= self._threshold else "full"

    def get_state(self, conversation_id: str) -> RedirectionState:
        return self._states.get(
            conversation_id,
            RedirectionState(
                conversation_id=conversation_id, redirection_threshold=self._threshold
            ),
        )


class _TopicRelevanceClassifier:
    """Detect clearly off-topic or out-of-scope customer messages."""

    _GREETINGS = re.compile(
        r"\b(hello|hi|hey|good\s+(morning|afternoon|evening)|how\s+are\s+you|what's\s+up)\b",
        re.IGNORECASE,
    )
    _THANKS = re.compile(r"\b(thanks|thank\s+you|ok|okay|bye|goodbye)\b", re.IGNORECASE)
    _CLARIFICATION = re.compile(
        r"^(yes|no|yep|nope|sure|not\s+really|i\s+meant|i\s+mean)\b",
        re.IGNORECASE,
    )
    _IDENTIFICATION_RESPONSE = re.compile(
        r"\b(my\s+name\s+is|i\s+am\s+[a-z]|answer\s+is|it\s+is\s+[a-z0-9]|\+\d[\d\s-]{7,20}|"
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
        re.IGNORECASE,
    )
    _BANKING_SCOPE = re.compile(
        r"\b(account|balance|loan|mortgage|insurance|card|credit|debit|transfer|payment|date\s+of\s+birth|dob|"
        r"phone|premium|yacht|fraud|suspicious|transaction|bank|banking|customer\s+support|"
        r"help|open\s+hours|opening\s+hours|branch|deposit|withdraw|savings|checking|"
        r"settings|update\s+my|online\s+banking|mobile\s+app)\b",
        re.IGNORECASE,
    )
    _OFF_TOPIC = re.compile(
        r"\b(movie|film|song|music|recipe|food|weather|football|soccer|basketball|sport|sports|"
        r"game|gaming|python|javascript|code|coding|programming|politics|news|joke|tell\s+me\s+a\s+joke|"
        r"story|book|novel|travel|vacation|hotel|restaurant)\b",
        re.IGNORECASE,
    )
    _OUT_OF_SCOPE_BANKING = re.compile(
        r"\b(investment\s+advice|tax\s+(filing|advice|return)|file\s+my\s+taxes|stock\s+tip|"
        r"crypto|bitcoin|cryptocurrency|forex\s+trading|day\s+trading)\b",
        re.IGNORECASE,
    )

    def classify(self, text: str, context: ConversationContext) -> tuple[CheckVerdict, str | None]:
        lowered = text.strip().casefold()

        if not lowered:
            return CheckVerdict.PASS, None

        # Common conversational interactions are always allowed.
        if (
            self._GREETINGS.search(lowered)
            or self._THANKS.search(lowered)
            or self._CLARIFICATION.search(lowered)
        ):
            return CheckVerdict.PASS, None

        # Verification responses during Greeter collection are allowed.
        if (
            context.current_agent == "greeter"
            and context.status in {ConversationStatus.COLLECTING, ConversationStatus.IDENTIFIED}
            and self._IDENTIFICATION_RESPONSE.search(lowered)
        ):
            return CheckVerdict.PASS, None

        # Clearly out-of-scope or off-topic content. During the Greeter collection
        # phase we allow casual side remarks once we have already started collecting
        # attributes, so the existing identification flow can consume them.
        if self._OFF_TOPIC.search(lowered) or self._OUT_OF_SCOPE_BANKING.search(lowered):
            if (
                context.current_agent == "greeter"
                and context.status == ConversationStatus.COLLECTING
                and context.has_collected_attributes
            ):
                return CheckVerdict.PASS, None
            return CheckVerdict.BLOCK, "off_topic"

        # Banking-related content is allowed; unfamiliar terminology is not a block reason.
        if self._BANKING_SCOPE.search(lowered):
            return CheckVerdict.PASS, None

        # Once the customer is identified or authenticated, let downstream agents
        # (Bouncer/Specialist) decide how to handle ambiguous requests.
        if context.status in {ConversationStatus.IDENTIFIED, ConversationStatus.AUTHENTICATED}:
            return CheckVerdict.PASS, None

        # Allow short workflow responses and ambiguous-but-not-off-topic messages
        # to avoid blocking legitimate customer interactions.
        if len(lowered.split()) <= 5:
            return CheckVerdict.PASS, None

        # Ambiguous content: ask for clarification rather than blocking permanently.
        return CheckVerdict.CLARIFY, "needs_clarification"


class _HarmfulContentClassifier:
    """Detect harmful, manipulative, or prohibited requests."""

    _SENSITIVE_TOPICS = re.compile(
        "|".join(SENSITIVE_TOPIC_PATTERNS),
        re.IGNORECASE,
    )
    _HARM_ACTIONS = (
        r"(hack|steal|scam|exploit|crack|break\s+into|bypass|forge|falsify|phish|skim|"
        r"steal\s+money|launder)"
    )
    _HARMFUL_PATTERNS = re.compile(
        rf"\b((how\s+(to|do\s+I|can\s+I)|teach\s+me\s+(to|how)|show\s+me\s+how|tell\s+me\s+how)\s+"
        rf"{_HARM_ACTIONS})\b|"
        r"\b(build\s+a\s+bomb|create\s+a\s+bomb|make\s+a\s+bomb|make\s+a\s+weapon)\b|"
        r"\b(harm\s+yourself|kill\s+yourself|self[-\s]?harm|suicide)\b|"
        r"\b(racist|sexist|homophobic|slur|hate\s+speech)\b|"
        r"\b(dox|doxx|swat)\b",
        re.IGNORECASE,
    )
    _MANIPULATION = re.compile(
        r"\b(ignore\s+.+\s+instructions|forget\s+.+\s+instructions|disregard\s+.+\s+rules|"
        r"bypass\s+.+\s+guardrail|act\s+as\s+.+\s+manager|you\s+are\s+now\s+.+\s+assistant)\b",
        re.IGNORECASE,
    )

    def classify(self, text: str, context: ConversationContext) -> tuple[CheckVerdict, str | None]:
        lowered = text.strip().casefold()

        # Harmful content and manipulation are evaluated BEFORE the sensitive-topic
        # allowlist (E4/FR-...): a legitimate banking phrase such as "report fraud"
        # must never suppress a harmful determination.
        if self._HARMFUL_PATTERNS.search(lowered) or self._MANIPULATION.search(lowered):
            return CheckVerdict.BLOCK, "harmful_content"

        # Legitimate sensitive banking topics are allowed.
        if self._SENSITIVE_TOPICS.search(lowered):
            return CheckVerdict.PASS, None

        return CheckVerdict.PASS, None


class _ResponseRelevanceValidator:
    """Detect assistant responses that do not address the customer's request."""

    _TOPIC_MARKERS: dict[str, list[str]] = {
        "yacht_insurance": ["yacht", "boat", "marine"],
        "insurance": ["insurance", "policy", "coverage", "claim"],
        "account_assistance": ["account", "balance", "date_of_birth", "phone", "details"],
        "premium_banking": ["premium", "dedicated", "relationship manager"],
        "mortgage": ["mortgage", "mortgages", "rate", "rates", "interest rate"],
        "general_banking": ["bank", "banking", "help", "support"],
    }

    _WORKFLOW_MESSAGES = re.compile(
        "|".join(WORKFLOW_MESSAGE_PATTERNS),
        re.IGNORECASE,
    )

    def validate(
        self,
        response_text: str,
        request_text: str,
        context: ConversationContext,
    ) -> tuple[CheckVerdict, str | None]:
        response_lower = response_text.strip().casefold()
        request_lower = request_text.strip().casefold()

        # Preserve workflow-necessary messages.
        if self._WORKFLOW_MESSAGES.search(response_lower):
            return CheckVerdict.PASS, None

        # Detect strong topic mismatch between request and response.
        request_topics = self._topics_for(request_lower)
        response_topics = self._topics_for(response_lower)

        if request_topics and response_topics and not request_topics.intersection(response_topics):
            # The response introduces a topic not present in the specific request.
            return CheckVerdict.BLOCK, "relevance_failure"

        # Detect contradictions with trusted workflow state.
        if (
            re.search(r"you\s+are\s+(now\s+)?authenticated", response_lower)
            and context.status != ConversationStatus.AUTHENTICATED
        ):
            return CheckVerdict.BLOCK, "relevance_failure"
        if (
            re.search(r"you\s+are\s+(a\s+)?premium\s+customer", response_lower)
            and context.customer_classification != CustomerClassification.PREMIUM
        ):
            return CheckVerdict.BLOCK, "relevance_failure"

        return CheckVerdict.PASS, None

    def _topics_for(self, text: str) -> set[str]:
        topics: set[str] = set()
        for topic, markers in self._TOPIC_MARKERS.items():
            if any(marker in text for marker in markers):
                topics.add(topic)
        return topics


class _UnsupportedClaimDetector:
    """Detect bank-specific claims that are not supported by the trusted catalog."""

    def __init__(self, catalog: TrustedBankingCatalog) -> None:
        self._catalog = catalog

    def detect(self, response_text: str) -> tuple[CheckVerdict, str | None]:
        result = self._catalog.covers_claim(response_text)
        if result.is_high_risk and not result.is_supported:
            return CheckVerdict.BLOCK, "unsupported_claim"
        return CheckVerdict.PASS, None


class _OutputProfessionalismChecker:
    """Detect offensive, unprofessional, or internally-revealing assistant outputs."""

    _OFFENSIVE = re.compile(
        r"\b(stupid|idiot|damn|hell\s+no|shut\s+up|useless|worthless|moron|jerk)\b",
        re.IGNORECASE,
    )
    _INTERNAL_DETAILS = re.compile(
        r"\b(system\s+prompt|internal\s+implementation|guardrail\s+decision|"
        r"reason\s+category|audit\s+metadata)\b|"
        r"(\[contact\s+details\]|\[department\s+name\])",
        re.IGNORECASE,
    )

    def check(self, response_text: str) -> tuple[CheckVerdict, str | None]:
        lowered = response_text.casefold()
        if self._OFFENSIVE.search(lowered) or self._INTERNAL_DETAILS.search(lowered):
            return CheckVerdict.BLOCK, "professionalism_violation"
        return CheckVerdict.PASS, None


class AdvancedGuardrailEvaluator:
    """Composes advanced heuristic checks and exposes them as guardrail callables."""

    def __init__(
        self,
        catalog: TrustedBankingCatalog | None = None,
        safe_replies: dict[str, str] | None = None,
        redirection_tracker: RedirectionStateTracker | None = None,
    ) -> None:
        self._catalog = catalog or get_catalog("default")
        self._safe_replies = safe_replies or DEFAULT_ADVANCED_SAFE_REPLIES
        self._redirection = redirection_tracker or RedirectionStateTracker()
        self._topic_classifier = _TopicRelevanceClassifier()
        self._harm_classifier = _HarmfulContentClassifier()
        self._relevance_validator = _ResponseRelevanceValidator()
        self._claim_detector = _UnsupportedClaimDetector(self._catalog)
        self._professionalism_checker = _OutputProfessionalismChecker()

    # ------------------------------------------------------------------
    # Public API matching the heuristic-checker contract
    # ------------------------------------------------------------------

    def check_input(self, input_: GuardrailInput) -> str | GuardrailOutput | None:
        """Return a block reason/GuardrailOutput, or None/False if allowed."""
        context = _build_context(input_)
        results: list[CheckResult] = []
        degraded = False

        verdict, reason = self._run_check(
            "input_harm", lambda: self._harm_classifier.classify(input_.content, context)
        )
        results.append(
            CheckResult(check_name="input_harm", verdict=verdict, reason_category=reason)
        )
        # The input_harm check is mandatory: if it cannot run, fail closed rather
        # than degrading to an allow (E4/FR-...).
        if verdict == CheckVerdict.UNAVAILABLE:
            return self._to_guardrail_output(input_, "check_unavailable", results)
        if verdict == CheckVerdict.BLOCK and reason:
            return self._to_guardrail_output(input_, reason, results)

        verdict, reason = self._run_check(
            "topic_relevance", lambda: self._topic_classifier.classify(input_.content, context)
        )
        if verdict == CheckVerdict.UNAVAILABLE:
            degraded = True
        results.append(
            CheckResult(check_name="topic_relevance", verdict=verdict, reason_category=reason)
        )
        if verdict in {CheckVerdict.BLOCK, CheckVerdict.CLARIFY} and reason:
            return self._to_guardrail_output(input_, reason, results)

        if degraded:
            return self._to_guardrail_output(input_, "heuristic_unavailable", results, allowed=True)

        # Allowed input resets the redirection loop counter.
        self._redirection.record(input_.conversation_id, "allowed")
        return None

    def check_output(self, input_: GuardrailInput) -> str | GuardrailOutput | None:
        """Return a block reason/GuardrailOutput, or None/False if allowed."""
        context = _build_context(input_)
        results: list[CheckResult] = []
        degraded = False

        verdict, reason = self._run_check(
            "output_professionalism", lambda: self._professionalism_checker.check(input_.content)
        )
        if verdict == CheckVerdict.UNAVAILABLE:
            degraded = True
        results.append(
            CheckResult(
                check_name="output_professionalism", verdict=verdict, reason_category=reason
            )
        )
        if verdict == CheckVerdict.BLOCK and reason:
            return self._to_guardrail_output(input_, reason, results)

        verdict, reason = self._run_check(
            "unsupported_claim", lambda: self._claim_detector.detect(input_.content)
        )
        if verdict == CheckVerdict.UNAVAILABLE:
            degraded = True
        results.append(
            CheckResult(check_name="unsupported_claim", verdict=verdict, reason_category=reason)
        )
        if verdict == CheckVerdict.BLOCK and reason:
            return self._to_guardrail_output(input_, reason, results)

        request_text = _last_human_text(input_.messages)
        if request_text:
            verdict, reason = self._run_check(
                "response_relevance",
                lambda: self._relevance_validator.validate(input_.content, request_text, context),
            )
            if verdict == CheckVerdict.UNAVAILABLE:
                degraded = True
            results.append(
                CheckResult(
                    check_name="response_relevance", verdict=verdict, reason_category=reason
                )
            )
            if verdict == CheckVerdict.BLOCK and reason:
                return self._to_guardrail_output(input_, reason, results)

        if degraded:
            return self._to_guardrail_output(input_, "heuristic_unavailable", results, allowed=True)

        return None

    # ------------------------------------------------------------------
    # Detailed decision API for observability/testing
    # ------------------------------------------------------------------

    def evaluate(self, input_: AdvancedGuardrailInput) -> AdvancedGuardrailDecision:
        """Run all relevant checks and return a composite decision record."""
        if input_.guardrail_input.content_type == "customer_input":
            output = self.check_input(input_.guardrail_input)
        else:
            output = self.check_output(input_.guardrail_input)

        if isinstance(output, GuardrailOutput):
            raw_results = output.audit_metadata.get("check_results", [])
            check_results = [CheckResult.model_validate(r) for r in raw_results]
            return AdvancedGuardrailDecision(
                input=input_,
                outcome=output.outcome,
                reason_category=output.reason_category,
                safe_reply=output.safe_reply,
                check_results=check_results,
                audit_metadata=output.audit_metadata,
            )

        return AdvancedGuardrailDecision(
            input=input_,
            outcome=GuardrailDecisionOutcome.ALLOWED,
            reason_category="allowed",
            safe_reply=None,
            check_results=[],
            audit_metadata={"content_type": input_.guardrail_input.content_type},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_guardrail_output(
        self,
        input_: GuardrailInput,
        reason: str,
        check_results: Sequence[CheckResult],
        *,
        allowed: bool = False,
    ) -> GuardrailOutput:
        safe_reply = None if allowed else self._safe_reply_for(input_.conversation_id, reason)
        audit_metadata: dict[str, Any] = {
            "content_type": input_.content_type,
            "check_results": [r.model_dump() for r in check_results],
        }
        return GuardrailOutput(
            outcome=GuardrailDecisionOutcome.ALLOWED
            if allowed
            else GuardrailDecisionOutcome.BLOCKED,
            reason_category=reason,
            safe_reply=safe_reply,
            audit_metadata=audit_metadata,
        )

    def _run_check(
        self,
        check_name: str,
        check: Callable[[], tuple[CheckVerdict, str | None]],
    ) -> tuple[CheckVerdict, str | None]:
        """Run a single check and degrade safely on unexpected failure."""
        try:
            return check()
        except Exception:
            return CheckVerdict.UNAVAILABLE, "heuristic_unavailable"

    def _safe_reply_for(self, conversation_id: str, reason: str) -> str:
        if reason == "off_topic":
            state = self._redirection.record(conversation_id, reason)
            style = self._redirection.reply_style(state)
            key = "off_topic_brief" if style == "brief" else "off_topic"
            return self._safe_replies.get(key, self._safe_replies["off_topic"])
        return self._safe_replies.get(
            reason,
            self._safe_replies.get(
                "heuristic_unavailable", "I'm not able to help with that request."
            ),
        )


def _build_context(input_: GuardrailInput) -> ConversationContext:
    """Derive trusted conversation context from a GuardrailInput."""
    current_agent = _infer_agent(input_)
    return ConversationContext(
        current_agent=current_agent,
        status=input_.status,
        customer_classification=input_.customer_classification,
        support_intent=input_.support_intent,
        recent_messages=input_.messages,
        has_collected_attributes=input_.has_collected_attributes,
    )


def _infer_agent(input_: GuardrailInput) -> Literal["greeter", "bouncer", "specialist"]:
    """Infer the current agent step from trusted workflow state."""
    status = input_.status
    if status == ConversationStatus.COLLECTING:
        return "greeter"
    if status == ConversationStatus.IDENTIFIED:
        return "greeter"  # secret-answer collection is still Greeter
    if status == ConversationStatus.AUTHENTICATED:
        if input_.support_intent is not None:
            return "specialist"
        return "bouncer"
    return "greeter"


def _last_human_text(messages: Sequence[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def make_advanced_guardrail_checkers(
    catalog: TrustedBankingCatalog | None = None,
    safe_replies: dict[str, str] | None = None,
    redirection_tracker: RedirectionStateTracker | None = None,
) -> tuple[
    Callable[[GuardrailInput], str | GuardrailOutput | None],
    Callable[[GuardrailInput], str | GuardrailOutput | None],
]:
    """Return input and output heuristic checkers for ``GuardrailEvaluator``."""
    evaluator = AdvancedGuardrailEvaluator(
        catalog=catalog,
        safe_replies=safe_replies,
        redirection_tracker=redirection_tracker,
    )
    return evaluator.check_input, evaluator.check_output


__all__ = [
    "AdvancedGuardrailEvaluator",
    "RedirectionStateTracker",
    "make_advanced_guardrail_checkers",
]
