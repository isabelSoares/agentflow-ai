"""FastAPI application factory and lifespan wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from banking_support.agents.graph import build_verification_graph
from banking_support.agents.llm import (
    LLMExtractor,
    OpenAIExtractor,
    OpenAISupportIntentClassifier,
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
    SupportIntentClassifier,
)
from banking_support.config import Settings
from banking_support.data.history_store import HistoryStore
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.repository import CustomerRepository
from banking_support.data.session_access import SessionAccessStore
from banking_support.data.support_directory import default_support_directory
from banking_support.observability.logging import setup_logging
from banking_support.resilience.policy import ExternalCallPolicy
from banking_support.voice.schemas import VoiceConfig
from banking_support.voice.service import build_voice_service
from banking_support.voice.stt import FakeSTT, OpenAISpeechToText, STTClient
from banking_support.voice.tts import FakeTTS, OpenAITextToSpeech, TTSClient


class AppState:
    """Container for application-scoped dependencies."""

    def __init__(self) -> None:
        self.settings: Settings = Settings()
        self.customer_repository: CustomerRepository = InMemoryCustomerRepository()
        self.extractor: LLMExtractor = self._build_extractor(self.settings)
        self.intent_classifier: SupportIntentClassifier = self._build_intent_classifier(
            self.settings
        )
        self.verification_graph = build_verification_graph(
            self.customer_repository,
            self.extractor,
            default_phone_region=self.settings.default_phone_region,
            intent_classifier=self.intent_classifier,
            support_directory=default_support_directory(),
        )
        self.history_store = HistoryStore(
            self.verification_graph,
            max_history_messages=self.settings.max_history_messages,
            redaction_enabled=self.settings.history_redaction_enabled,
        )
        self.session_access_store = SessionAccessStore()
        self.voice_config: VoiceConfig = VoiceConfig.from_settings(self.settings)
        self.stt_client: STTClient = self._build_stt_client(self.settings)
        self.tts_client: TTSClient = self._build_tts_client(self.settings)
        self.voice_service = build_voice_service(
            config=self.voice_config,
            stt_client=self.stt_client,
            tts_client=self.tts_client,
            app_state=self,
        )

    @staticmethod
    def _build_extractor(settings: Settings) -> LLMExtractor:
        if settings.llm_api_key:
            return OpenAIExtractor(
                api_key=settings.llm_api_key,
                model=settings.llm_model,
                base_url=settings.llm_base_url,
                temperature=settings.llm_temperature,
                policy=ExternalCallPolicy(
                    timeout_seconds=settings.provider_timeout_seconds,
                    max_retries=settings.provider_max_retries,
                    backoff_seconds=settings.provider_retry_backoff_seconds,
                ),
            )
        # Safe default for local development / tests without a key.
        return ScriptedFakeExtractor()

    @staticmethod
    def _build_intent_classifier(settings: Settings) -> SupportIntentClassifier:
        if settings.llm_api_key:
            return OpenAISupportIntentClassifier(
                api_key=settings.llm_api_key,
                model=settings.llm_model,
                base_url=settings.llm_base_url,
                temperature=settings.llm_temperature,
                policy=ExternalCallPolicy(
                    timeout_seconds=settings.provider_timeout_seconds,
                    max_retries=settings.provider_max_retries,
                    backoff_seconds=settings.provider_retry_backoff_seconds,
                ),
            )
        # Safe default for local development / tests without a key.
        return ScriptedFakeSupportIntentClassifier()

    @staticmethod
    def _build_stt_client(settings: Settings) -> STTClient:
        if settings.voice_stt_enabled and settings.llm_api_key:
            return OpenAISpeechToText(
                api_key=settings.llm_api_key,
                model=settings.voice_stt_model,
                base_url=settings.llm_base_url,
                policy=ExternalCallPolicy(
                    timeout_seconds=settings.provider_timeout_seconds,
                    max_retries=settings.provider_max_retries,
                    backoff_seconds=settings.provider_retry_backoff_seconds,
                ),
            )
        # Safe default for local development / tests without a key.
        return FakeSTT()

    @staticmethod
    def _build_tts_client(settings: Settings) -> TTSClient:
        if settings.voice_tts_enabled and settings.llm_api_key:
            return OpenAITextToSpeech(
                api_key=settings.llm_api_key,
                model=settings.voice_tts_model,
                voice=settings.voice_tts_voice,
                base_url=settings.llm_base_url,
                output_content_type=settings.voice_output_content_type,
                policy=ExternalCallPolicy(
                    timeout_seconds=settings.provider_timeout_seconds,
                    max_retries=0,
                    backoff_seconds=settings.provider_retry_backoff_seconds,
                    idempotent=False,
                ),
            )
        # Safe default for local development / tests without a key.
        return FakeTTS()


def create_app(app_state: AppState | None = None) -> FastAPI:
    """Application factory."""
    state = app_state if app_state is not None else AppState()
    setup_logging(state.settings.log_level)

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.app_state = state
        yield

    from banking_support.api import routes

    app = FastAPI(
        title="AgentFlow AI — Secure Multi-Agent Customer Support",
        description=(
            "Secure, context-aware multi-agent customer support. The banking flow is the "
            "reference demo adapter; deterministic nodes own every security decision."
        ),
        version="0.1.0",
        lifespan=_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(state.settings.cors_allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Session-Proof"],
        expose_headers=["X-Session-Proof"],
    )
    app.include_router(routes.router)
    return app


__all__ = ["create_app", "AppState"]
