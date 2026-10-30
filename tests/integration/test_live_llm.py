"""Live LLM integration tests — run only in CI pull requests with a real key.

These tests exercise the real ChatOpenAI client against the configured provider.
They are gated by the `live_llm` pytest marker and skipped when GROQ_API_KEY is absent.
The total number of LLM calls per run must stay within the configured budget.
"""

from __future__ import annotations

import pytest

from banking_support.agents.llm import (
    ExtractionResult,
    IntentClassification,
    OpenAIExtractor,
    OpenAISupportIntentClassifier,
)
from banking_support.config import Settings

pytestmark = pytest.mark.live_llm

MAX_LLM_CALLS = 20


def _live_settings() -> Settings | None:
    """Return settings only when a real API key is available."""
    try:
        settings = Settings(_env_file=None)
    except Exception:  # pragma: no cover
        return None
    if settings.llm_api_key:
        return settings
    return None


@pytest.fixture(scope="module")
def settings() -> Settings:
    live = _live_settings()
    if live is None:
        pytest.skip("GROQ_API_KEY is not configured")
    return live


class TestCallBudget:
    """Ensure the live-LLM test suite stays within the call budget."""

    def test_call_budget_is_defined(self) -> None:
        assert MAX_LLM_CALLS > 0


class TestOpenAIExtractorLive:
    def test_extracts_name_and_phone(self, settings: Settings) -> None:
        extractor = OpenAIExtractor(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
        )
        result = extractor.extract("My name is Lisa and my phone is +14155552671")
        assert isinstance(result, ExtractionResult)
        assert result.name is not None
        assert "lisa" in result.name.lower()
        assert result.phone == "+14155552671"

    def test_extracts_iban(self, settings: Settings) -> None:
        extractor = OpenAIExtractor(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
        )
        result = extractor.extract("My IBAN is DE89370400440532013000")
        assert isinstance(result, ExtractionResult)
        assert result.iban == "DE89370400440532013000"


class TestOpenAISupportIntentClassifierLive:
    def test_classifies_account_assistance(self, settings: Settings) -> None:
        classifier = OpenAISupportIntentClassifier(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
        )
        result = classifier.classify("I need help with my account")
        assert isinstance(result, IntentClassification)
        assert result.intent.value in {
            "account_assistance",
            "general_banking",
        }

    def test_classifies_yacht_insurance(self, settings: Settings) -> None:
        classifier = OpenAISupportIntentClassifier(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
        )
        result = classifier.classify("I want yacht insurance")
        assert isinstance(result, IntentClassification)
        assert result.intent.value in {
            "yacht_insurance",
            "insurance",
            "other_specialized",
        }


class TestLiveAuthenticationJourney:
    """End-to-end identity + authentication journey with the real provider.

    Verifies E2 (deterministic authentication despite loose extraction) and
    E3 (identifier-only access is denied) against the live model.
    """

    def test_identity_and_authentication_journey(self, settings: Settings) -> None:
        from fastapi.testclient import TestClient

        from banking_support.api.app import AppState, create_app

        state = AppState()
        assert isinstance(state.extractor, OpenAIExtractor)
        assert isinstance(state.intent_classifier, OpenAISupportIntentClassifier)

        with TestClient(create_app(state)) as client:
            created = client.post("/conversations")
            assert created.status_code == 201
            conversation_id = created.json()["conversation_id"]
            proof = created.headers.get("X-Session-Proof")
            assert proof
            assert proof not in created.text
            headers = {"X-Session-Proof": proof}

            identified = client.post(
                f"/conversations/{conversation_id}/messages",
                json={"text": "My name is Lisa and my phone number is +14155552671"},
                headers=headers,
            )
            assert identified.status_code == 200
            assert identified.json()["identified"] is True
            assert proof not in identified.text

            authenticated = client.post(
                f"/conversations/{conversation_id}/messages",
                json={"text": "It is Yoda"},
                headers=headers,
            )
            assert authenticated.status_code == 200
            assert authenticated.json()["authenticated"] is True
            assert proof not in authenticated.text

            denied = client.post(
                f"/conversations/{conversation_id}/messages",
                json={"text": "hello"},
            )
            assert denied.status_code == 401
            assert denied.json() == {"detail": "Session access denied."}

            history = state.history_store.get_history(conversation_id)
            serialized = " ".join(str(entry) for entry in history)
            assert proof not in serialized


class TestCallBudgetEnforcement:
    """Runtime guard against accidental budget overruns."""

    def test_total_live_calls_within_budget(self) -> None:
        # This test counts how many live-LLM tests exist in this module.
        # It is a coarse guard; the real enforcement is keeping the test count small.
        import inspect
        import sys

        live_module = sys.modules[__name__]
        live_test_count = sum(
            1
            for _name, obj in inspect.getmembers(live_module, inspect.isclass)
            if obj.__module__ == __name__
            for _method_name, _method in inspect.getmembers(obj, inspect.isfunction)
            if _method_name.startswith("test_")
        )
        # Each live test is expected to make at most one LLM call.
        assert live_test_count <= MAX_LLM_CALLS, (
            f"Live-LLM test count ({live_test_count}) exceeds budget ({MAX_LLM_CALLS}). "
            "Reduce tests or raise the budget explicitly."
        )
