"""Integration coverage for the actual LangGraph checkpointer boundary."""

from banking_support.agents.graph import build_verification_graph
from banking_support.agents.llm import ExtractionResult, ScriptedFakeExtractor
from banking_support.agents.state import make_initial_state
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.seed import CUSTOMERS
from banking_support.domain.conversation import ExtractionIntent


def test_graph_checkpoint_excludes_raw_input_and_secret_answer() -> None:
    conversation_id = "checkpoint-private"
    graph = build_verification_graph(
        InMemoryCustomerRepository(CUSTOMERS),
        ScriptedFakeExtractor(
            [
                ExtractionResult(
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                    name="Lisa",
                    phone="+14155552671",
                )
            ]
        ),
    )
    config = {"configurable": {"thread_id": conversation_id}}
    graph.update_state(config, make_initial_state(conversation_id))
    graph.invoke(
        {"user_input": "my raw IBAN and secret", "conversation_id": conversation_id}, config
    )

    snapshot = graph.get_state(config)
    values = snapshot.values
    assert "user_input" not in values
    assert "pending_secret_answer" not in values
    assert all(getattr(message, "type", "") != "human" for message in values["messages"])
