"""Contract tests for the HTTP chat API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from conftest import proof_headers, start_session
from healthcare_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
)
from healthcare_support.api.app import AppState, create_app
from healthcare_support.api.schemas import ConversationTurnResponse
from healthcare_support.data.seed import PATIENTS
from healthcare_support.domain.routing import IntentClassification, SupportIntent


@pytest.fixture
def client() -> TestClient:
    extractor = ScriptedFakeExtractor(
        [
            ExtractionResult(
                name="Lisa", phone="+14155552671", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
            ),
            ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
        ]
    )
    app_state = AppState()
    app_state.extractor = extractor
    # Rebuild graph with the scripted extractor.
    from healthcare_support.agents.graph import build_verification_graph

    app_state.verification_graph = build_verification_graph(
        app_state.patient_repository,
        extractor,
        default_phone_region=app_state.settings.default_phone_region,
    )
    app_state.history_store = app_state.history_store.__class__(
        app_state.verification_graph,
        max_history_messages=app_state.settings.max_history_messages,
        redaction_enabled=app_state.settings.history_redaction_enabled,
    )
    with TestClient(create_app(app_state=app_state)) as test_client:
        yield test_client


@pytest.fixture
def routed_client() -> TestClient:
    extractor = ScriptedFakeExtractor(
        [
            ExtractionResult(
                name="Lisa", phone="+14155552671", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
            ),
            ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
        ]
    )
    classifier = ScriptedFakeSupportIntentClassifier(
        [IntentClassification(intent=SupportIntent.SPECIALIST_REFERRAL)]
    )
    app_state = AppState()
    app_state.extractor = extractor
    app_state.intent_classifier = classifier
    from healthcare_support.agents.graph import build_verification_graph

    app_state.verification_graph = build_verification_graph(
        app_state.patient_repository,
        extractor,
        default_phone_region=app_state.settings.default_phone_region,
        intent_classifier=classifier,
    )
    app_state.history_store = app_state.history_store.__class__(
        app_state.verification_graph,
        max_history_messages=app_state.settings.max_history_messages,
        redaction_enabled=app_state.settings.history_redaction_enabled,
    )
    with TestClient(create_app(app_state=app_state)) as test_client:
        yield test_client


class TestStartConversation:
    def test_creates_conversation(self, client: TestClient) -> None:
        response = client.post("/conversations")
        assert response.status_code == 201
        body = response.json()
        ConversationTurnResponse.model_validate(body)
        assert body["identified"] is False
        assert body["authenticated"] is False
        assert body["terminated"] is False
        assert "assistant" in body["reply"].lower()

    def test_creation_returns_proof_header_not_in_body(self, client: TestClient) -> None:
        response = client.post("/conversations")
        proof = response.headers.get("X-Session-Proof")
        assert proof
        assert proof not in response.text


class TestSendMessage:
    def test_unknown_conversation_is_denied(self, client: TestClient) -> None:
        response = client.post(
            "/conversations/00000000-0000-0000-0000-000000000000/messages",
            json={"text": "hello"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Session access denied."}

    def test_identifier_only_is_denied(self, client: TestClient) -> None:
        cid, _proof = start_session(client)
        response = client.post(f"/conversations/{cid}/messages", json={"text": "hello"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Session access denied."}

    def test_invalid_body_returns_422(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        response = client.post(f"/conversations/{cid}/messages", json={"text": ""}, headers=headers)
        assert response.status_code == 422

    def test_response_has_no_pii_fields(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        response = client.post(
            f"/conversations/{cid}/messages", json={"text": "I am Lisa"}, headers=headers
        )
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {
            "conversation_id",
            "reply",
            "identified",
            "authenticated",
            "terminated",
            "classification",
            "routing_status",
            "routing_intent",
            "support_department",
        }

    def test_happy_path_via_api(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        r1 = client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        assert r1.json()["identified"] is True
        assert "Which is the name of my dog?" in r1.json()["reply"]
        r2 = client.post(f"/conversations/{cid}/messages", json={"text": "Yoda"}, headers=headers)
        assert r2.json()["authenticated"] is True

    def test_no_sensitive_data_in_pre_auth_response(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        response = client.post(
            f"/conversations/{cid}/messages", json={"text": "I am Lisa"}, headers=headers
        )
        reply = response.json()["reply"]
        for patient in PATIENTS:
            assert patient.phone not in reply
            assert patient.date_of_birth not in reply
            assert patient.secret_answer not in reply
            assert patient.name not in reply

    def test_premium_classification_exposed_after_authentication(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        response = client.post(
            f"/conversations/{cid}/messages", json={"text": "Yoda"}, headers=headers
        )
        body = response.json()
        assert body["authenticated"] is True
        assert body["classification"] == "premium"
        assert "+1999888999" in body["reply"]

    def test_unverified_classification_is_null(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        response = client.post(
            f"/conversations/{cid}/messages", json={"text": "I am Lisa"}, headers=headers
        )
        body = response.json()
        assert body["authenticated"] is False
        assert body["classification"] is None


class TestSpecialistRouting:
    def test_routing_metadata_null_before_authentication(self, routed_client: TestClient) -> None:
        cid, headers = start_session(routed_client)
        response = routed_client.post(
            f"/conversations/{cid}/messages", json={"text": "I am Lisa"}, headers=headers
        )
        body = response.json()
        assert body["authenticated"] is False
        assert body["routing_status"] is None
        assert body["routing_intent"] is None
        assert body["support_department"] is None

    def test_premium_specialist_referral_routes_via_api(self, routed_client: TestClient) -> None:
        cid, headers = start_session(routed_client)
        routed_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        response = routed_client.post(
            f"/conversations/{cid}/messages", json={"text": "Yoda"}, headers=headers
        )
        body = response.json()
        assert body["authenticated"] is True
        assert body["classification"] == "premium"

        route_response = routed_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I need a specialist referral"},
            headers=headers,
        )
        route_body = route_response.json()
        assert route_body["routing_status"] == "routed"
        assert route_body["routing_intent"] == "specialist_referral"
        assert route_body["support_department"] == "Insurance and Billing Department"
        ConversationTurnResponse.model_validate(route_body)

    def test_unauthenticated_request_has_no_routing_metadata(
        self, routed_client: TestClient
    ) -> None:
        cid, headers = start_session(routed_client)
        response = routed_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I need a specialist referral"},
            headers=headers,
        )
        body = response.json()
        assert body["authenticated"] is False
        assert body["routing_status"] is None
        assert body["support_department"] is None


@pytest.fixture
def contextual_client() -> TestClient:
    extractor = ScriptedFakeExtractor(
        [
            ExtractionResult(
                name="Lisa", phone="+14155552671", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
            ),
            ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
            ExtractionResult(intent=ExtractionIntent.CHITCHAT),
            ExtractionResult(intent=ExtractionIntent.CHITCHAT),
        ]
    )
    classifier = ScriptedFakeSupportIntentClassifier(
        [
            IntentClassification(
                intent=SupportIntent.INSURANCE,
                needs_clarification=True,
                clarification_prompt="What type of insurance?",
            ),
            IntentClassification(
                intent=SupportIntent.SPECIALIST_REFERRAL,
                needs_clarification=False,
            ),
        ]
    )
    app_state = AppState()
    app_state.extractor = extractor
    app_state.intent_classifier = classifier
    from healthcare_support.agents.graph import build_verification_graph

    app_state.verification_graph = build_verification_graph(
        app_state.patient_repository,
        extractor,
        default_phone_region=app_state.settings.default_phone_region,
        intent_classifier=classifier,
    )
    app_state.history_store = app_state.history_store.__class__(
        app_state.verification_graph,
        max_history_messages=app_state.settings.max_history_messages,
        redaction_enabled=app_state.settings.history_redaction_enabled,
    )
    with TestClient(create_app(app_state=app_state)) as test_client:
        yield test_client


class TestMultiTurnContext:
    def test_contextual_follow_up_routes_correctly(self, contextual_client: TestClient) -> None:
        cid, headers = start_session(contextual_client)
        contextual_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        contextual_client.post(
            f"/conversations/{cid}/messages", json={"text": "Yoda"}, headers=headers
        )

        r1 = contextual_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I need a specialist referral"},
            headers=headers,
        )
        assert "type of insurance" in r1.json()["reply"].lower()

        r2 = contextual_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "For a specialist referral"},
            headers=headers,
        )
        body = r2.json()
        assert body["routing_intent"] == "specialist_referral"


class TestVerificationAcrossMessages:
    def test_name_then_phone_advances_verification(self, client: TestClient) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(name="Lisa", intent=ExtractionIntent.PROVIDE_IDENTIFICATION),
                ExtractionResult(
                    phone="+14155552671", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
                ),
            ]
        )
        app_state = AppState()
        app_state.extractor = extractor
        from healthcare_support.agents.graph import build_verification_graph

        app_state.verification_graph = build_verification_graph(
            app_state.patient_repository,
            extractor,
            default_phone_region=app_state.settings.default_phone_region,
        )
        app_state.history_store = app_state.history_store.__class__(
            app_state.verification_graph,
            max_history_messages=app_state.settings.max_history_messages,
            redaction_enabled=app_state.settings.history_redaction_enabled,
        )
        with TestClient(create_app(app_state=app_state)) as test_client:
            cid, headers = start_session(test_client)
            r1 = test_client.post(
                f"/conversations/{cid}/messages", json={"text": "I am Lisa"}, headers=headers
            )
            assert r1.json()["identified"] is False
            assert "more information" in r1.json()["reply"].lower()

            r2 = test_client.post(
                f"/conversations/{cid}/messages",
                json={"text": "My phone is +14155552671"},
                headers=headers,
            )
            assert r2.json()["identified"] is True
            assert "Which is the name of my dog?" in r2.json()["reply"]


class TestSessionIsolation:
    def test_separate_sessions_do_not_leak_history(self, client: TestClient) -> None:
        cid1, headers1 = start_session(client)
        cid2, headers2 = start_session(client)

        r1 = client.post(
            f"/conversations/{cid1}/messages", json={"text": "I am Lisa"}, headers=headers1
        )
        r2 = client.post(
            f"/conversations/{cid2}/messages", json={"text": "I am Maria"}, headers=headers2
        )

        assert "Maria" not in r1.json()["reply"]
        assert "Lisa" not in r2.json()["reply"]

    def test_proof_for_one_session_denied_for_another(self, client: TestClient) -> None:
        _cid1, headers1 = start_session(client)
        cid2, _headers2 = start_session(client)
        response = client.post(
            f"/conversations/{cid2}/messages", json={"text": "hello"}, headers=headers1
        )
        assert response.status_code == 401


class TestResetEndpoint:
    def test_reset_clears_history_and_state(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )

        reset = client.post(f"/conversations/{cid}/reset", headers=headers)
        assert reset.status_code == 200
        body = reset.json()
        assert body["identified"] is False
        assert body["authenticated"] is False
        assert body["terminated"] is False
        new_proof = reset.headers.get("X-Session-Proof")
        assert new_proof and new_proof != headers["X-Session-Proof"]

        # The prior proof is rejected; the rotated proof continues the session.
        old = client.post(f"/conversations/{cid}/messages", json={"text": "hello"}, headers=headers)
        assert old.status_code == 401
        follow_up = client.post(
            f"/conversations/{cid}/messages",
            json={"text": "hello"},
            headers=proof_headers(new_proof),
        )
        assert follow_up.json()["identified"] is False

    def test_reset_clears_persisted_history(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        app_state = client.app.state.app_state
        assert app_state.history_store.get_history(cid)

        reset = client.post(f"/conversations/{cid}/reset", headers=headers)
        assert reset.status_code == 200

        assert app_state.history_store.get_history(cid) == []


class TestContextAwareGuardrails:
    def test_short_follow_up_not_blocked(self, contextual_client: TestClient) -> None:
        cid, headers = start_session(contextual_client)
        contextual_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        contextual_client.post(
            f"/conversations/{cid}/messages", json={"text": "Yoda"}, headers=headers
        )

        r1 = contextual_client.post(
            f"/conversations/{cid}/messages", json={"text": "I need insurance"}, headers=headers
        )
        assert "type of insurance" in r1.json()["reply"].lower()

        r2 = contextual_client.post(
            f"/conversations/{cid}/messages",
            json={"text": "For my insurance claim"},
            headers=headers,
        )
        assert r2.json()["routing_intent"] == "specialist_referral"


class FailingHistoryStore:
    """Test double that simulates an unavailable history store."""

    def __init__(self, wrapped: object) -> None:
        self._wrapped = wrapped

    def add_user_message(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError("history store unavailable")

    def add_assistant_message(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError("history store unavailable")

    def __getattr__(self, name: str) -> object:
        return getattr(self._wrapped, name)


class TestHistoryUnavailability:
    def test_history_failure_does_not_bypass_security(self, client: TestClient) -> None:
        # Inject a failing history store to simulate storage unavailability.
        app_state = AppState()
        app_state.history_store = FailingHistoryStore(app_state.history_store)
        from healthcare_support.agents.graph import build_verification_graph

        app_state.verification_graph = build_verification_graph(
            app_state.patient_repository,
            app_state.extractor,
            default_phone_region=app_state.settings.default_phone_region,
        )
        app_state.history_store = FailingHistoryStore(app_state.history_store)

        with TestClient(create_app(app_state=app_state)) as test_client:
            cid, headers = start_session(test_client)
            response = test_client.post(
                f"/conversations/{cid}/messages", json={"text": "I am Lisa"}, headers=headers
            )
            assert response.status_code == 200
            body = response.json()
            assert body["authenticated"] is False
            assert body["terminated"] is False
