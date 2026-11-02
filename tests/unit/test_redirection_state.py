"""Unit tests for redirection loop prevention (US1)."""

from __future__ import annotations

import pytest

from healthcare_support.core.advanced_guardrails import AdvancedGuardrailEvaluator
from healthcare_support.domain.conversation import ConversationStatus
from healthcare_support.domain.guardrails import GuardrailInput


@pytest.fixture
def evaluator() -> AdvancedGuardrailEvaluator:
    return AdvancedGuardrailEvaluator()


def _input(content: str, conversation_id: str = "loop-conv") -> GuardrailInput:
    return GuardrailInput(
        content=content,
        content_type="patient_input",
        conversation_id=conversation_id,
        status=ConversationStatus.COLLECTING,
        messages=[],
    )


class TestRedirectionLoopPrevention:
    def test_first_off_topic_full_reply(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_input(_input("Recommend a movie"))
        assert result is not None
        assert hasattr(result, "safe_reply")
        reply = result.safe_reply.lower()
        assert "banking" in reply
        assert "support" in reply
        assert "how can i help you today" in reply

    def test_second_off_topic_brief_reply(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        evaluator.check_input(_input("Recommend a movie"))
        result = evaluator.check_input(_input("Recommend a movie"))
        assert result is not None
        reply = result.safe_reply.lower()
        assert "banking" in reply
        assert "support" in reply
        assert "how can i help you today" not in reply

    def test_allowed_message_resets_loop(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        evaluator.check_input(_input("Recommend a movie"))
        # A banking question resets the counter.
        assert evaluator.check_input(_input("I need help with my account")) is None
        # Next off-topic is full again.
        result = evaluator.check_input(_input("Recommend a movie"))
        assert "how can i help you today" in result.safe_reply.lower()

    def test_different_conversations_have_independent_state(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        evaluator.check_input(_input("Recommend a movie", conversation_id="conv-a"))
        evaluator.check_input(_input("Recommend a movie", conversation_id="conv-a"))
        result_b = evaluator.check_input(_input("Recommend a movie", conversation_id="conv-b"))
        # conv-b should still be on its first off-topic turn.
        assert "how can i help you today" in result_b.safe_reply.lower()
