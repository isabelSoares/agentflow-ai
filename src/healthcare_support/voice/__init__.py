"""Voice interface adapters and services.

This package provides speech-to-text (STT) and text-to-speech (TTS) adapters
that keep speech-processing concerns separate from healthcare business logic.
"""

from healthcare_support.voice.schemas import (
    SpeechResult,
    TranscriptionResult,
    VoiceConfig,
    VoiceRequest,
)
from healthcare_support.voice.service import VoiceService, build_voice_service
from healthcare_support.voice.stt import FakeSTT, OpenAISpeechToText, STTClient
from healthcare_support.voice.tts import FakeTTS, OpenAITextToSpeech, TTSClient
from healthcare_support.voice.validation import (
    AudioValidationError,
    AudioValidationResult,
    AudioValidator,
)

__all__ = [
    "AudioValidationError",
    "AudioValidationResult",
    "AudioValidator",
    "FakeSTT",
    "FakeTTS",
    "OpenAISpeechToText",
    "OpenAITextToSpeech",
    "SpeechResult",
    "STTClient",
    "TTSClient",
    "TranscriptionResult",
    "VoiceConfig",
    "VoiceRequest",
    "VoiceService",
    "build_voice_service",
]
