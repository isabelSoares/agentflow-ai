"""Checkpoint state must not retain current-turn secrets or raw user input."""

from langchain_core.messages import HumanMessage

from healthcare_support.agents.state import checkpoint_safe_state


def test_checkpoint_projection_removes_transient_values_and_human_messages() -> None:
    state = {
        "user_input": "my secret answer",
        "pending_secret_answer": "Yoda",
        "messages": [HumanMessage(content="my IBAN"), {"role": "assistant", "content": "Hi"}],
        "status": "collecting",
    }

    safe = checkpoint_safe_state(state)

    assert "user_input" not in safe
    assert "pending_secret_answer" not in safe
    assert all(getattr(message, "type", "") != "human" for message in safe["messages"])
    assert safe["status"] == "collecting"
