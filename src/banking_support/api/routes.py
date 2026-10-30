"""FastAPI routes for the chat API."""

from __future__ import annotations

from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)

from banking_support.agents.state import make_initial_state
from banking_support.api import schemas
from banking_support.api.invoker import (
    ensure_session_access,
    get_app_state,
    invoke_graph,
    reset_conversation,
)
from banking_support.api.schemas import SESSION_PROOF_HEADER
from banking_support.core import responses
from banking_support.domain.conversation import ConversationStatus
from banking_support.voice.schemas import VoiceConfig, VoiceRequest
from banking_support.voice.validation import AudioValidationError, AudioValidator

router = APIRouter()


@router.get("/health", response_model=schemas.HealthResponse)
def health() -> schemas.HealthResponse:
    """Report service liveness without requiring session proof."""
    return schemas.HealthResponse(status="ok")


@router.post("/conversations", status_code=201, response_model=schemas.ConversationTurnResponse)
def start_conversation(request: Request, response: Response) -> schemas.ConversationTurnResponse:
    """Start a new verification conversation and issue an ownership proof."""
    conversation_id = str(uuid4())
    app_state = get_app_state(request)
    graph = app_state.verification_graph
    config = {"configurable": {"thread_id": conversation_id}}
    graph.update_state(config, make_initial_state(conversation_id))
    proof = app_state.session_access_store.create(conversation_id)
    response.headers[SESSION_PROOF_HEADER] = proof
    return schemas.ConversationTurnResponse(
        conversation_id=conversation_id,
        reply=responses.GREETING,
        identified=False,
        authenticated=False,
        terminated=False,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=schemas.ConversationTurnResponse,
)
def send_message(
    conversation_id: str,
    payload: schemas.MessageRequest,
    request: Request,
    proof: str | None = Depends(schemas.session_proof_header),
) -> schemas.ConversationTurnResponse:
    """Send a user message and receive the assistant reply."""
    app_state = get_app_state(request)
    result = invoke_graph(app_state, conversation_id, payload.text, proof)
    status = result.get("status")
    return schemas.ConversationTurnResponse(
        conversation_id=conversation_id,
        reply=result.get("reply") or "",
        identified=status
        in (ConversationStatus.IDENTIFIED.value, ConversationStatus.AUTHENTICATED.value),
        authenticated=status == ConversationStatus.AUTHENTICATED.value,
        terminated=bool(result.get("terminated")),
        classification=result.get("customer_classification"),
        routing_status=result.get("routing_status"),
        routing_intent=result.get("support_intent"),
        support_department=result.get("support_department"),
    )


@router.post(
    "/conversations/{conversation_id}/reset",
    response_model=schemas.ConversationTurnResponse,
)
def reset_session(
    conversation_id: str,
    request: Request,
    response: Response,
    proof: str | None = Depends(schemas.session_proof_header),
) -> schemas.ConversationTurnResponse:
    """Explicitly reset a conversation, clearing history and trusted state."""
    app_state = get_app_state(request)
    result, new_proof = reset_conversation(app_state, conversation_id, proof)
    response.headers[SESSION_PROOF_HEADER] = new_proof
    return schemas.ConversationTurnResponse(
        conversation_id=conversation_id,
        reply=result.get("reply") or responses.GREETING,
        identified=False,
        authenticated=False,
        terminated=False,
        classification=None,
        routing_status=None,
        routing_intent=None,
        support_department=None,
    )


@router.post(
    "/conversations/{conversation_id}/voice/messages",
    response_model=schemas.VoiceTurnResponse,
)
async def send_voice_message(
    conversation_id: str,
    request: Request,
    audio: UploadFile = File(...),  # noqa: B008
    enable_tts: bool = Form(False),  # noqa: B008
    proof: str | None = Depends(schemas.session_proof_header),
) -> schemas.VoiceTurnResponse:
    """Send a voice recording and receive the assistant reply with optional speech."""
    app_state = get_app_state(request)

    # Session access is checked before voice availability and audio validation so
    # a denied caller learns nothing from the voice path.
    ensure_session_access(app_state, conversation_id, proof)

    voice_config: VoiceConfig = app_state.voice_config

    if not voice_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice processing is not enabled.",
        )

    content_type = audio.content_type or "application/octet-stream"
    audio_bytes = await audio.read()

    try:
        AudioValidator(voice_config).validate_or_raise(audio_bytes, content_type)
    except AudioValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.customer_message,
        ) from exc

    voice_request = VoiceRequest(
        conversation_id=conversation_id,
        content_type=content_type,
        enable_tts=enable_tts,
    )

    response_data = app_state.voice_service.handle_voice_request(
        voice_request,
        audio_bytes,
        proof,
    )
    return schemas.VoiceTurnResponse(**response_data)
