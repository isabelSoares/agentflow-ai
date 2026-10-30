"""Contract tests for session ownership enforcement (E3/FR-013..FR-026)."""

from __future__ import annotations

import io
import wave
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from banking_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
)
from banking_support.api.app import AppState, create_app
from banking_support.data.seed import CUSTOMERS
from banking_support.domain.routing import IntentClassification, SupportIntent
from banking_support.voice.service import build_voice_service
from banking_support.voice.stt import FakeSTT
from banking_support.voice.tts import FakeTTS
from conftest import proof_headers, start_session

DENIED = {"detail": "Session access denied."}


def _make_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00" * 320)
    return buffer.getvalue()


@pytest.fixture
def app_state() -> AppState:
    extractor = ScriptedFakeExtractor(
        [
            ExtractionResult(
                name=CUSTOMERS[0].name,
                phone=CUSTOMERS[0].phone,
                intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
            ),
            ExtractionResult(
                secret_answer=CUSTOMERS[0].secret_answer, intent=ExtractionIntent.ANSWER_SECRET
            ),
        ]
    )
    classifier = ScriptedFakeSupportIntentClassifier(
        [IntentClassification(intent=SupportIntent.GENERAL_BANKING)]
    )
    state = AppState()
    state.extractor = extractor
    state.intent_classifier = classifier
    from banking_support.agents.graph import build_verification_graph

    state.verification_graph = build_verification_graph(
        state.customer_repository,
        extractor,
        default_phone_region=state.settings.default_phone_region,
        intent_classifier=classifier,
    )
    state.history_store = state.history_store.__class__(
        state.verification_graph,
        max_history_messages=state.settings.max_history_messages,
        redaction_enabled=state.settings.history_redaction_enabled,
    )
    return state


@pytest.fixture
def client(app_state: AppState) -> TestClient:
    with TestClient(create_app(app_state)) as test_client:
        yield test_client


@pytest.fixture
def voice_client(app_state: AppState) -> TestClient:
    app_state.voice_config = app_state.voice_config.model_copy(
        update={"enabled": True, "stt_enabled": True, "tts_enabled": True}
    )
    app_state.stt_client = FakeSTT(default="I need help with my bank account")
    app_state.tts_client = FakeTTS(audio=b"AUDIO")
    app_state.voice_service = build_voice_service(
        config=app_state.voice_config,
        stt_client=app_state.stt_client,
        tts_client=app_state.tts_client,
        app_state=app_state,
    )
    with TestClient(create_app(app_state)) as test_client:
        yield test_client


class TestCreationIssuesProof:
    def test_create_returns_header_and_not_body(self, client: TestClient) -> None:
        response = client.post("/conversations")
        assert response.status_code == 201
        proof = response.headers.get("X-Session-Proof")
        assert proof
        assert proof not in response.text

    def test_proofs_are_unique_per_session(self, client: TestClient) -> None:
        _cid1, headers1 = start_session(client)
        _cid2, headers2 = start_session(client)
        assert headers1["X-Session-Proof"] != headers2["X-Session-Proof"]


class TestDenials:
    def test_missing_proof_denied(self, client: TestClient) -> None:
        cid, _headers = start_session(client)
        response = client.post(f"/conversations/{cid}/messages", json={"text": "hello"})
        assert response.status_code == 401
        assert response.json() == DENIED

    def test_malformed_proof_denied(self, client: TestClient) -> None:
        cid, _headers = start_session(client)
        response = client.post(
            f"/conversations/{cid}/messages",
            json={"text": "hello"},
            headers=proof_headers("short"),
        )
        assert response.status_code == 401
        assert response.json() == DENIED

    def test_unknown_identifier_denied(self, client: TestClient) -> None:
        response = client.post(
            f"/conversations/{uuid4()}/messages",
            json={"text": "hello"},
            headers=proof_headers("a" * 43),
        )
        assert response.status_code == 401
        assert response.json() == DENIED

    def test_invalid_proof_denied(self, client: TestClient) -> None:
        cid, _headers = start_session(client)
        response = client.post(
            f"/conversations/{cid}/messages",
            json={"text": "hello"},
            headers=proof_headers("b" * 43),
        )
        assert response.status_code == 401
        assert response.json() == DENIED

    def test_cross_session_proof_denied(self, client: TestClient) -> None:
        _cid1, headers1 = start_session(client)
        cid2, _headers2 = start_session(client)
        response = client.post(
            f"/conversations/{cid2}/messages", json={"text": "hello"}, headers=headers1
        )
        assert response.status_code == 401
        assert response.json() == DENIED

    def test_reset_unknown_identifier_denied(self, client: TestClient) -> None:
        response = client.post(f"/conversations/{uuid4()}/reset", headers=proof_headers("a" * 43))
        assert response.status_code == 401
        assert response.json() == DENIED

    def test_denied_request_does_not_modify_state(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        # A denied turn must not advance the session.
        denied = client.post(f"/conversations/{cid}/messages", json={"text": "Yoda"})
        assert denied.status_code == 401
        allowed = client.post(
            f"/conversations/{cid}/messages", json={"text": "Yoda"}, headers=headers
        )
        assert allowed.json()["authenticated"] is True


class TestRotationAndTermination:
    def test_reset_rotates_and_rejects_prior_proof(self, client: TestClient) -> None:
        cid, headers = start_session(client)
        client.post(
            f"/conversations/{cid}/messages",
            json={"text": "I am Lisa, phone +14155552671"},
            headers=headers,
        )
        reset = client.post(f"/conversations/{cid}/reset", headers=headers)
        assert reset.status_code == 200
        new_proof = reset.headers.get("X-Session-Proof")
        assert new_proof and new_proof != headers["X-Session-Proof"]

        prior = client.post(
            f"/conversations/{cid}/messages", json={"text": "hello"}, headers=headers
        )
        assert prior.status_code == 401
        rotated = client.post(
            f"/conversations/{cid}/messages",
            json={"text": "hello"},
            headers=proof_headers(new_proof),
        )
        assert rotated.status_code == 200

    def test_terminated_session_is_denied(self, app_state: AppState) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name=CUSTOMERS[0].name,
                    phone=CUSTOMERS[0].phone,
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="A", intent=ExtractionIntent.ANSWER_SECRET),
                ExtractionResult(secret_answer="B", intent=ExtractionIntent.ANSWER_SECRET),
                ExtractionResult(secret_answer="C", intent=ExtractionIntent.ANSWER_SECRET),
            ]
        )
        from banking_support.agents.graph import build_verification_graph

        app_state.extractor = extractor
        app_state.verification_graph = build_verification_graph(
            app_state.customer_repository,
            extractor,
            default_phone_region=app_state.settings.default_phone_region,
        )
        app_state.history_store = app_state.history_store.__class__(
            app_state.verification_graph,
            max_history_messages=app_state.settings.max_history_messages,
            redaction_enabled=app_state.settings.history_redaction_enabled,
        )
        with TestClient(create_app(app_state)) as test_client:
            cid, headers = start_session(test_client)
            test_client.post(
                f"/conversations/{cid}/messages",
                json={"text": "I am Lisa, phone +14155552671"},
                headers=headers,
            )
            for _ in range(3):
                test_client.post(
                    f"/conversations/{cid}/messages", json={"text": "wrong"}, headers=headers
                )
            response = test_client.post(
                f"/conversations/{cid}/messages", json={"text": "hello"}, headers=headers
            )
            assert response.status_code == 401
            assert response.json() == DENIED


class TestUnauthorizedAccessMatrix:
    """SC-004: at least ten unauthorized-access shapes all yield zero access."""

    def test_zero_unauthorized_accesses(self, client: TestClient, voice_client: TestClient) -> None:
        cid, headers = start_session(client)
        other_cid, _other_headers = start_session(client)
        voice_cid, _voice_headers = start_session(voice_client)

        valid_shaped = "a" * 43
        message_probes: list[tuple[str, str, dict[str, str] | None]] = [
            ("missing_proof", cid, None),
            ("short_proof", cid, proof_headers("short")),
            ("non_hex_proof", cid, proof_headers("z" * 64)),
            ("unknown_identifier", str(uuid4()), proof_headers(valid_shaped)),
            ("unknown_identifier_no_proof", str(uuid4()), None),
            ("invalid_proof", cid, proof_headers(valid_shaped)),
            ("cross_session_proof", other_cid, headers),
        ]
        for name, target, hdrs in message_probes:
            response = client.post(
                f"/conversations/{target}/messages",
                json={"text": "who am I"},
                headers=hdrs,
            )
            assert response.status_code == 401, name
            assert response.json() == DENIED, name

        reset_probes: list[tuple[str, str, dict[str, str] | None]] = [
            ("reset_missing", cid, None),
            ("reset_unknown_identifier", str(uuid4()), proof_headers(valid_shaped)),
            ("reset_invalid_proof", cid, proof_headers(valid_shaped)),
            ("reset_cross_session", other_cid, headers),
        ]
        for name, target, hdrs in reset_probes:
            response = client.post(f"/conversations/{target}/reset", headers=hdrs)
            assert response.status_code == 401, name
            assert response.json() == DENIED, name

        voice_probes: list[tuple[str, dict[str, str] | None]] = [
            ("voice_missing_proof", None),
            ("voice_invalid_proof", proof_headers(valid_shaped)),
        ]
        for name, hdrs in voice_probes:
            response = voice_client.post(
                f"/conversations/{voice_cid}/voice/messages",
                files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
                headers=hdrs,
            )
            assert response.status_code == 401, name
            assert response.json() == DENIED, name

        assert len(message_probes) + len(reset_probes) + len(voice_probes) >= 10


class TestVoiceAccess:
    def test_voice_without_proof_denied_before_enabled_check(
        self, voice_client: TestClient
    ) -> None:
        cid, _headers = start_session(voice_client)
        response = voice_client.post(
            f"/conversations/{cid}/voice/messages",
            files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        )
        assert response.status_code == 401
        assert response.json() == DENIED

    def test_voice_with_proof_allowed(self, voice_client: TestClient) -> None:
        cid, headers = start_session(voice_client)
        response = voice_client.post(
            f"/conversations/{cid}/voice/messages",
            files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
            headers=headers,
        )
        assert response.status_code == 200

    def test_voice_disabled_without_proof_still_denies(self, app_state: AppState) -> None:
        # Voice is disabled by default; session denial must win over 503.
        with TestClient(create_app(app_state)) as test_client:
            cid, _headers = start_session(test_client)
            response = test_client.post(
                f"/conversations/{cid}/voice/messages",
                files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
            )
            assert response.status_code == 401
