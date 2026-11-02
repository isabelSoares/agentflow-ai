"""FastAPI request/response schemas.

The response schema deliberately contains no PII fields.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Header
from pydantic import BaseModel, Field

SESSION_PROOF_HEADER = "X-Session-Proof"


def session_proof_header(
    proof: Annotated[str | None, Header(alias=SESSION_PROOF_HEADER)] = None,
) -> str | None:
    """Extract the session ownership proof from the request headers."""
    return proof


class HealthResponse(BaseModel):
    """Liveness response with no session or patient data."""

    status: Literal["ok"]

    model_config = {"extra": "forbid"}


class MessageRequest(BaseModel):
    """User message payload."""

    text: str = Field(min_length=1, max_length=2000)

    model_config = {"extra": "forbid"}


class ConversationTurnResponse(BaseModel):
    """Assistant reply with sanitized progress flags."""

    conversation_id: str
    reply: str
    identified: bool
    authenticated: bool
    terminated: bool
    classification: str | None = None
    routing_status: str | None = None
    routing_intent: str | None = None
    support_department: str | None = None

    model_config = {"extra": "forbid"}


class VoiceTurnResponse(ConversationTurnResponse):
    """Assistant reply for a voice interaction, with optional spoken audio."""

    audio: str | None = Field(
        default=None,
        description="Base64-encoded spoken version of the approved reply.",
    )
    audio_content_type: str | None = Field(
        default=None,
        description="Media type of the generated audio.",
    )
    audio_failed: bool = Field(
        default=False,
        description="True when TTS was requested but could not be generated.",
    )
