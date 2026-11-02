"""Patient-facing safe replies for advanced guardrail reason categories."""

from __future__ import annotations

DEFAULT_ADVANCED_SAFE_REPLIES: dict[str, str] = {
    "off_topic": (
        "I'm here to help with banking patient support. "
        "I can assist with questions about accounts, cards, loans, insurance, "
        "and other banking services. How can I help you today?"
    ),
    "off_topic_brief": (
        "I'm only able to help with banking support. Please let me know if you have a banking question."
    ),
    "needs_clarification": (
        "I'm not sure I understood. Could you rephrase your question as a banking support request?"
    ),
    "harmful_content": (
        "I'm not able to help with that request. "
        "If you have a banking question, I'm happy to assist."
    ),
    "relevance_failure": (
        "I don't have a relevant answer for that right now. "
        "Could you let me know how I can help with your banking needs?"
    ),
    "unsupported_claim": (
        "I can't confirm specific product terms here. "
        "For accurate details, I'll connect you with the right specialist."
    ),
    "professionalism_violation": (
        "I'm here to provide professional banking support. How can I help you today?"
    ),
    "heuristic_unavailable": (
        "I'm not able to complete that check right now, but your request will continue. "
        "How else can I help?"
    ),
    "check_unavailable": (
        "I'm not able to complete that request right now. "
        "Please try again later or contact your bank directly for assistance."
    ),
}
