"""Node assembly and routing for the identity-verification workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from healthcare_support.agents.classification_nodes import make_classification_node
from healthcare_support.agents.extraction_nodes import make_extraction_node
from healthcare_support.agents.guardrail_nodes import make_guardrail_nodes
from healthcare_support.agents.identity_nodes import make_identity_nodes
from healthcare_support.agents.llm import LLMExtractor, SupportIntentClassifier
from healthcare_support.agents.node_strategies import (
    WorkflowDependencies,
    build_node_strategies,
)
from healthcare_support.agents.response_nodes import make_response_nodes
from healthcare_support.agents.specialist_nodes import make_specialist_node
from healthcare_support.agents.state import GraphState
from healthcare_support.data.repository import PatientRepository
from healthcare_support.data.support_directory import default_support_directory
from healthcare_support.domain.conversation import ConversationStatus
from healthcare_support.domain.routing import SupportDirectory


def make_nodes(
    repository: PatientRepository,
    extractor: LLMExtractor,
    default_phone_region: str = "DE",
    intent_classifier: SupportIntentClassifier | None = None,
    support_directory: SupportDirectory | None = None,
) -> dict[str, Callable[[GraphState], dict[str, Any]]]:
    """Return the named, dependency-injected nodes used by the verification graph."""
    dependencies = WorkflowDependencies(
        repository=repository,
        extractor=extractor,
        default_phone_region=default_phone_region,
        intent_classifier=intent_classifier,
        support_directory=support_directory or default_support_directory(),
    )
    strategies: dict[str, Callable[[GraphState], dict[str, Any]]] = {}
    strategies.update(make_guardrail_nodes(dependencies))
    strategies["extract"] = make_extraction_node(dependencies)
    strategies.update(make_identity_nodes(dependencies))
    strategies["classify"] = make_classification_node(dependencies)
    strategies["specialist"] = make_specialist_node(dependencies)
    strategies.update(make_response_nodes())
    return build_node_strategies(dependencies, strategies)


def route_after_guardrail(state: GraphState) -> str:
    if state.get("terminated"):
        return "terminated"
    if state.get("reply") is not None:
        return "output_guardrail"
    return "extract"


def route_after_extract(state: GraphState) -> str:
    status = state.get("status")
    if status == ConversationStatus.IDENTIFIED.value:
        return "authenticate"
    if status == ConversationStatus.AUTHENTICATED.value:
        return "specialist"
    if state.get("terminated"):
        return "terminated"
    return "identify"


def route_after_identify(state: GraphState) -> str:
    if state.get("reply") is not None:
        return "output_guardrail"
    if state.get("status") == ConversationStatus.IDENTIFIED.value:
        return "authenticate"
    return "output_guardrail"


def route_after_authenticate(state: GraphState) -> str:
    if state.get("status") == ConversationStatus.AUTHENTICATED.value:
        return "classify"
    return "output_guardrail"


def route_after_classify(state: GraphState) -> str:
    return "output_guardrail"


def route_after_specialist(state: GraphState) -> str:
    return "output_guardrail"


def route_after_output_guardrail(state: GraphState) -> str:
    return "respond"


__all__ = ["make_nodes"]
