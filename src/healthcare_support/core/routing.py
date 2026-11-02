"""Deterministic support-routing logic for the Specialist Agent.

This module contains no LLM, framework, repository, or API imports. Routing
decisions are pure functions of the trusted authentication state, trusted
customer classification, validated intent, and approved support directory.
"""

from __future__ import annotations

from healthcare_support.domain.conversation import CustomerClassification
from healthcare_support.domain.routing import (
    IntentClassification,
    RoutingDecision,
    RoutingStatus,
    SupportDepartment,
    SupportDirectory,
    SupportIntent,
)


class RoutingError(Exception):
    """Raised when routing cannot produce a safe decision."""


# Customer-facing fallback messages. These contain no customer data and no
# invented departments or contact details.
_CLARIFICATION_MESSAGE = (
    "I'm not sure I understood your request correctly. Could you tell me whether "
    "you need help with your account, insurance, or another banking service?"
)

_UNSUPPORTED_MESSAGE = (
    "I'm not able to help with that request through this channel. "
    "If you need assistance with a supported banking service, please let me know."
)

_UNINTERPRETABLE_MESSAGE = (
    "I'm sorry, I didn't catch that. Could you rephrase what you need help with?"
)

_UNAUTHENTICATED_MESSAGE = (
    "I'll be happy to help once your identity is verified. "
    "Please provide your name, phone number, or date of birth to get started."
)

_UNAVAILABLE_MESSAGE = (
    "I'm not able to route your request right now because the appropriate "
    "support channel is currently unavailable. Please try again later or contact "
    "your bank directly."
)

_NON_CUSTOMER_MESSAGE = (
    "Thank you for reaching out. Dedicated customer support is only available to "
    "existing customers. If you'd like to learn more about becoming a "
    "customer, please visit our website or your nearest branch."
)


def _build_routed_message(department: SupportDepartment) -> str:
    contact = department.contact
    contact_fragment = f" at {contact}" if contact else ""
    return (
        f"I'll connect you with the {department.display_name}{contact_fragment}. "
        "They'll be able to assist you with your request."
    )


def authentication_gate(
    *,
    is_authenticated: bool,
    customer_classification: CustomerClassification | None,
    intent: SupportIntent,
) -> RoutingDecision | None:
    """Return the authorization decision, or ``None`` when routing may continue."""
    if not is_authenticated or not isinstance(customer_classification, CustomerClassification):
        return RoutingDecision(
            status=RoutingStatus.BLOCKED, intent=intent, message=_UNAUTHENTICATED_MESSAGE
        )
    if customer_classification == CustomerClassification.NON_CUSTOMER:
        return RoutingDecision(
            status=RoutingStatus.FALLBACK, intent=intent, message=_NON_CUSTOMER_MESSAGE
        )
    return None


def specialist_key(intent_classification: IntentClassification) -> str | None:
    """Map supported specialist intents to approved directory lookup keys."""
    if intent_classification.intent == SupportIntent.YACHT_INSURANCE:
        return "yacht_insurance"
    if (
        intent_classification.intent == SupportIntent.OTHER_SPECIALIZED
        and intent_classification.specialization
    ):
        return intent_classification.specialization
    return None


def tier_key(customer_classification: CustomerClassification) -> str | None:
    """Map a trusted customer tier to its approved support destination."""
    if customer_classification == CustomerClassification.PREMIUM:
        return "premium_support"
    if customer_classification == CustomerClassification.REGULAR:
        return "standard_support"
    return None


def route_support_request(
    *,
    is_authenticated: bool,
    customer_classification: CustomerClassification | None,
    intent_classification: IntentClassification,
    support_directory: SupportDirectory,
) -> RoutingDecision:
    """Return a deterministic routing decision for the given inputs.

    Args:
        is_authenticated: Whether the Greeter Agent has authenticated the caller.
        customer_classification: Trusted Bouncer classification, or ``None`` if
            classification has not been performed or is unknown.
        intent_classification: Validated classifier output for the support request.
        support_directory: Approved support destinations.

    Returns:
        A ``RoutingDecision`` with a safe customer-facing message.
    """
    intent = intent_classification.intent

    gate = authentication_gate(
        is_authenticated=is_authenticated,
        customer_classification=customer_classification,
        intent=intent,
    )
    if gate is not None:
        return gate

    # 2. Clarification gate.
    if intent_classification.needs_clarification or intent == SupportIntent.AMBIGUOUS:
        prompt = intent_classification.clarification_prompt or _CLARIFICATION_MESSAGE
        return RoutingDecision(
            status=RoutingStatus.CLARIFICATION_REQUIRED,
            intent=intent,
            message=prompt,
        )

    # 3. Specific specialist routing.
    specialist = specialist_key(intent_classification)

    if specialist is not None:
        specialist_department = support_directory.find_by_specialization(specialist)
        if specialist_department is None or not specialist_department.available:
            return RoutingDecision(
                status=RoutingStatus.FALLBACK,
                intent=intent,
                message=_UNAVAILABLE_MESSAGE,
            )
        return RoutingDecision(
            status=RoutingStatus.ROUTED,
            intent=intent,
            department_key=specialist_department.key,
            department_name=specialist_department.display_name,
            contact=specialist_department.contact,
            message=_build_routed_message(specialist_department),
        )

    # 4. Unsupported / uninterpretable fallback.
    if intent == SupportIntent.UNSUPPORTED:
        return RoutingDecision(
            status=RoutingStatus.FALLBACK,
            intent=intent,
            message=_UNSUPPORTED_MESSAGE,
        )

    if intent == SupportIntent.UNINTERPRETABLE:
        return RoutingDecision(
            status=RoutingStatus.FALLBACK,
            intent=intent,
            message=_UNINTERPRETABLE_MESSAGE,
        )

    # 5. Premium / Regular tier routing for account and general banking requests.
    assert customer_classification is not None
    tier = tier_key(customer_classification)

    if tier is not None:
        department = support_directory.get(tier)
        if department is None or not department.available:
            return RoutingDecision(
                status=RoutingStatus.FALLBACK,
                intent=intent,
                message=_UNAVAILABLE_MESSAGE,
            )
        return RoutingDecision(
            status=RoutingStatus.ROUTED,
            intent=intent,
            department_key=department.key,
            department_name=department.display_name,
            contact=department.contact,
            message=_build_routed_message(department),
        )

    # Defensive fallback for unexpected classification values.
    return RoutingDecision(
        status=RoutingStatus.BLOCKED,
        intent=intent,
        message=_UNAUTHENTICATED_MESSAGE,
    )


__all__ = [
    "route_support_request",
    "authentication_gate",
    "specialist_key",
    "tier_key",
    "RoutingError",
]
