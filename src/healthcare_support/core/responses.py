"""Fixed, non-disclosing response templates used by the verification flow.

No template in this module contains placeholders for customer record data, so
pre-authentication replies cannot leak PII by construction.
"""

from __future__ import annotations

GREETING = (
    "Hello! I'm your banking support assistant. "
    "To get started, could you please tell me your name, phone number, or IBAN?"
)

NON_DISCLOSING_IDENTIFICATION_REPLY = (
    "I need a bit more information because I wasn't able to verify you. "
    "Please provide another detail, such as your name, phone number, or full IBAN."
)

ASK_MORE_ATTRIBUTES = NON_DISCLOSING_IDENTIFICATION_REPLY

ASK_DISAMBIGUATION = NON_DISCLOSING_IDENTIFICATION_REPLY

IDENTIFICATION_FAILURE = NON_DISCLOSING_IDENTIFICATION_REPLY

SECRET_QUESTION_PREFIX = (
    "Thank you. To complete verification, please answer your security question: "
)

WRONG_SECRET_ANSWER = "That answer doesn't match our records. Please try again."

TERMINATION_GENERIC = (
    "I'm sorry, I wasn't able to complete the verification. "
    "Please contact your bank for assistance."
)

TERMINATION_NON_CLIENT = (
    "Thank you for reaching out. It seems that you are not currently a client. "
    "I recommend that you contact your bank's support department directly for assistance."
)

DATA_REQUEST_REFUSAL = "I'm not able to share that information until your identity is verified."

MANIPULATION_RE_PROMPT = (
    "I'm here to help with banking support. "
    "Please provide your name, phone number, or IBAN so I can verify you."
)

EMPTY_RE_PROMPT = "I didn't catch that. Please provide your name, phone number, or IBAN."

CLOSED_CONVERSATION = (
    "This verification session has ended. If you need further assistance, "
    "please start a new conversation."
)

AUTHENTICATED_CONFIRMATION = "Thank you, your identity has been verified. How can I help you today?"

PREMIUM_ROUTING = (
    "Thank you for reaching out regarding your account issue. As a premium client, "
    "we value your experience and are here to assist you. For immediate support, "
    "please contact our dedicated support department at +1999888999."
)

REGULAR_ROUTING = (
    "I'm sorry to hear that you're having trouble with your account. Since you're a "
    "regular client, I recommend that you call our support department at +1112112112 "
    "for assistance."
)

NON_CUSTOMER_RESPONSE = (
    "Thank you for reaching out. Dedicated customer support is only available to "
    "existing customers. If you'd like to learn more about becoming a "
    "customer, please visit our website or your nearest branch."
)

PREMIUM_RESTRICTION_MESSAGE = (
    "That service is available exclusively to premium customers. "
    "For assistance with other options, please let me know what you need help with."
)

PROHIBITED_ACTION_MESSAGE = (
    "I'm not able to process or approve that request. "
    "If you'd like information about our services, I can route your inquiry to the appropriate team."
)

INTERNAL_DISCLOSURE_REFUSAL = (
    "I'm not able to share internal details or configuration information. "
    "How can I help you with your banking needs today?"
)

PRIVACY_VIOLATION_MESSAGE = (
    "I'm not able to share that information. "
    "If you need help with your account, please let me know what you're looking for."
)

UNAVAILABLE_GUARDIAL_MESSAGE = (
    "I'm not able to complete that request right now. "
    "Please try again later or contact your bank directly for assistance."
)
