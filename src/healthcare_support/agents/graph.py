"""LangGraph builder for the identity-verification workflow."""

from __future__ import annotations

from typing import Any, cast

from langgraph.checkpoint.base import CheckpointMetadata
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from healthcare_support.agents import nodes
from healthcare_support.agents.llm import LLMExtractor, SupportIntentClassifier
from healthcare_support.agents.state import GraphState, checkpoint_safe_state
from healthcare_support.data.repository import CustomerRepository
from healthcare_support.domain.routing import SupportDirectory


def build_verification_graph(
    repository: CustomerRepository,
    extractor: LLMExtractor,
    default_phone_region: str = "DE",
    intent_classifier: SupportIntentClassifier | None = None,
    support_directory: SupportDirectory | None = None,
) -> Any:
    """Compile the verification graph with an in-memory checkpointer."""
    node_map = nodes.make_nodes(
        repository,
        extractor,
        default_phone_region=default_phone_region,
        intent_classifier=intent_classifier,
        support_directory=support_directory,
    )

    builder = StateGraph(GraphState)
    builder.add_node("guardrail", node_map["guardrail"])  # type: ignore[call-overload]
    builder.add_node("extract", node_map["extract"])  # type: ignore[call-overload]
    builder.add_node("identify", node_map["identify"])  # type: ignore[call-overload]
    builder.add_node("authenticate", node_map["authenticate"])  # type: ignore[call-overload]
    builder.add_node("classify", node_map["classify"])  # type: ignore[call-overload]
    builder.add_node("specialist", node_map["specialist"])  # type: ignore[call-overload]
    builder.add_node("output_guardrail", node_map["output_guardrail"])  # type: ignore[call-overload]
    builder.add_node("respond", node_map["respond"])  # type: ignore[call-overload]
    builder.add_node("terminated", node_map["terminated"])  # type: ignore[call-overload]

    builder.add_edge(START, "guardrail")
    builder.add_conditional_edges("guardrail", nodes.route_after_guardrail)
    builder.add_conditional_edges("extract", nodes.route_after_extract)
    builder.add_conditional_edges("identify", nodes.route_after_identify)
    builder.add_conditional_edges("authenticate", nodes.route_after_authenticate)
    builder.add_conditional_edges("classify", nodes.route_after_classify)
    builder.add_conditional_edges("specialist", nodes.route_after_specialist)
    builder.add_conditional_edges("output_guardrail", nodes.route_after_output_guardrail)
    builder.add_edge("respond", END)
    builder.add_edge("terminated", "output_guardrail")

    class CheckpointSafeSaver(InMemorySaver):
        def put(self, config: Any, checkpoint: Any, metadata: Any, new_versions: Any) -> Any:
            values = checkpoint.get("channel_values", {})
            checkpoint = {**checkpoint, "channel_values": checkpoint_safe_state(values)}
            safe_metadata = {
                key: value
                for key, value in metadata.items()
                if key not in {"user_input", "pending_secret_answer"}
            }
            return super().put(
                config, checkpoint, cast(CheckpointMetadata, safe_metadata), new_versions
            )

        async def aput(self, config: Any, checkpoint: Any, metadata: Any, new_versions: Any) -> Any:
            values = checkpoint.get("channel_values", {})
            checkpoint = {**checkpoint, "channel_values": checkpoint_safe_state(values)}
            safe_metadata = {
                key: value
                for key, value in metadata.items()
                if key not in {"user_input", "pending_secret_answer"}
            }
            return await super().aput(
                config, checkpoint, cast(CheckpointMetadata, safe_metadata), new_versions
            )

        def put_writes(self, config: Any, writes: Any, task_id: str, task_path: str = "") -> None:
            safe_writes = [
                (key, value)
                for key, value in writes
                if key not in {"user_input", "pending_secret_answer"}
            ]
            super().put_writes(config, safe_writes, task_id, task_path)

    return builder.compile(checkpointer=CheckpointSafeSaver())


__all__ = ["build_verification_graph"]
