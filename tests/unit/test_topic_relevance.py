"""Unit tests for topic relevance classification (US1)."""

from __future__ import annotations

import pytest

from banking_support.core.advanced_guardrails import AdvancedGuardrailEvaluator
from banking_support.domain.conversation import ConversationStatus, CustomerClassification
from banking_support.domain.guardrails import GuardrailInput
from banking_support.domain.routing import SupportIntent


@pytest.fixture
def evaluator() -> AdvancedGuardrailEvaluator:
    return AdvancedGuardrailEvaluator()


def _input(
    content: str,
    *,
    status: ConversationStatus = ConversationStatus.COLLECTING,
    classification: CustomerClassification | None = None,
    intent: SupportIntent | None = None,
) -> GuardrailInput:
    return GuardrailInput(
        content=content,
        content_type="customer_input",
        conversation_id="us1-conv",
        status=status,
        customer_classification=classification,
        support_intent=intent,
        messages=[],
    )


class TestLegitimateBankingAllowed:
    @pytest.mark.parametrize(
        "text",
        [
            "I need help with my account",
            "Can you explain mortgage rates?",
            "What are your opening hours?",
            "How do I update my API settings?",
            "I want to open a savings account",
            "Can I get a credit card?",
            "I need to transfer money",
        ],
    )
    def test_legitimate_banking_requests_allowed(
        self, evaluator: AdvancedGuardrailEvaluator, text: str
    ) -> None:
        result = evaluator.check_input(_input(text, status=ConversationStatus.AUTHENTICATED))
        assert result is None or getattr(result, "outcome", None) != "blocked"

    def test_unfamiliar_terminology_allowed(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_input(
            _input("What is a fiduciary deposit account?", status=ConversationStatus.AUTHENTICATED)
        )
        assert result is None


class TestOffTopicRedirected:
    @pytest.mark.parametrize(
        "text",
        [
            "Recommend a movie",
            "Tell me a joke",
            "What is the weather today?",
            "How do I learn Python?",
            "Who won the football match?",
            "Give me a recipe for pasta",
        ],
    )
    def test_off_topic_requests_redirected(
        self, evaluator: AdvancedGuardrailEvaluator, text: str
    ) -> None:
        result = evaluator.check_input(_input(text))
        assert result is not None
        if hasattr(result, "reason_category"):
            assert result.reason_category == "off_topic"
        else:
            assert result == "off_topic"


class TestGreetingsAndConversationalAllowed:
    @pytest.mark.parametrize(
        "text",
        [
            "Hello, how are you?",
            "Hi there",
            "Good morning",
            "Thanks for your help",
            "ok",
        ],
    )
    def test_greetings_allowed(self, evaluator: AdvancedGuardrailEvaluator, text: str) -> None:
        result = evaluator.check_input(_input(text))
        assert result is None or getattr(result, "outcome", None) != "blocked"


class TestOutOfScopeBankingRedirected:
    @pytest.mark.parametrize(
        "text",
        [
            "Give me investment advice",
            "Help me file my taxes",
            "What is the best cryptocurrency to buy?",
        ],
    )
    def test_out_of_scope_redirected(
        self, evaluator: AdvancedGuardrailEvaluator, text: str
    ) -> None:
        result = evaluator.check_input(_input(text))
        assert result is not None
        reason = getattr(result, "reason_category", result)
        assert reason == "off_topic"


class TestVerificationAndPremiumAllowed:
    def test_verification_data_allowed(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_input(
            _input(
                "My name is Alice Smith and my phone is +491234567890",
                status=ConversationStatus.COLLECTING,
            )
        )
        assert result is None

    def test_premium_insurance_allowed(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_input(
            _input(
                "I need specialized yacht insurance",
                status=ConversationStatus.AUTHENTICATED,
                classification=CustomerClassification.PREMIUM,
                intent=SupportIntent.YACHT_INSURANCE,
            )
        )
        assert result is None

    def test_clarification_answer_allowed(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_input(
            _input(
                "Yes, I meant my savings account",
                status=ConversationStatus.AUTHENTICATED,
                classification=CustomerClassification.REGULAR,
                intent=SupportIntent.AMBIGUOUS,
            )
        )
        assert result is None or getattr(result, "reason_category", None) != "off_topic"
