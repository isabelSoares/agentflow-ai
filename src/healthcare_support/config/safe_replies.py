"""Patient-facing safe replies for advanced guardrail reason categories."""

from __future__ import annotations

DEFAULT_ADVANCED_SAFE_REPLIES: dict[str, str] = {
    "off_topic": (
        "I'm here to help with healthcare patient support. "
        "I can assist with questions about appointments, insurance, billing, "
        "prescriptions, and other healthcare services. How can I help you today?"
    ),
    "off_topic_brief": (
        "I'm only able to help with healthcare support. Please let me know if you have a healthcare question."
    ),
    "needs_clarification": (
        "I'm not sure I understood. Could you rephrase your question as a healthcare support request?"
    ),
    "harmful_content": (
        "I'm not able to help with that request. "
        "If you have a healthcare question, I'm happy to assist."
    ),
    "relevance_failure": (
        "I don't have a relevant answer for that right now. "
        "Could you let me know how I can help with your healthcare needs?"
    ),
    "unsupported_claim": (
        "I can't confirm specific coverage, costs, or appointment availability here. "
        "For accurate details, I'll connect you with the right specialist."
    ),
    "professionalism_violation": (
        "I'm here to provide professional healthcare support. How can I help you today?"
    ),
    "heuristic_unavailable": (
        "I'm not able to complete that check right now, but your request will continue. "
        "How else can I help?"
    ),
    "check_unavailable": (
        "I'm not able to complete that request right now. "
        "Please try again later or contact your healthcare provider for assistance."
    ),
}
