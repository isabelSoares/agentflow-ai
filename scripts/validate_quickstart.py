"""Simulate the quickstart scenarios using a scripted extractor (no API key needed).

This records the outcomes of quickstart.md scenarios S1–S7 against the real
LangGraph orchestration logic. It does not exercise the HTTP layer; the contract
and integration test suites already cover that.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from banking_support.agents.graph import build_verification_graph
from banking_support.agents.llm import ExtractionIntent, ExtractionResult, ScriptedFakeExtractor
from banking_support.agents.state import make_initial_state
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.seed import CUSTOMERS


def run(conversation_id: str, extractor: ScriptedFakeExtractor, turns: list[str]) -> None:
    repository = InMemoryCustomerRepository(CUSTOMERS)
    graph = build_verification_graph(repository, extractor, default_phone_region="DE")
    config = {"configurable": {"thread_id": conversation_id}}
    graph.update_state(config, make_initial_state(conversation_id))
    for i, text in enumerate(turns, 1):
        result = graph.invoke(
            {"messages": [HumanMessage(content=text)], "conversation_id": conversation_id},
            config,
        )
        status = result["status"]
        identified = status == "identified"
        authenticated = status == "authenticated"
        print(
            f"  T{i}: status={status} "
            f"identified={identified} "
            f"authenticated={authenticated} "
            f"terminated={result['terminated']} | {result['reply'][:70]}..."
        )


def main() -> None:
    print("S1 Happy path")
    run(
        "s1",
        ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
            ]
        ),
        ["Hi, I am Lisa, my phone is +14155552671", "It is Yoda"],
    )

    print("\nS2 Multi-turn out-of-order")
    run(
        "s2",
        ScriptedFakeExtractor(
            [
                ExtractionResult(name="Lisa", intent=ExtractionIntent.PROVIDE_IDENTIFICATION),
                ExtractionResult(intent=ExtractionIntent.CHITCHAT),
                ExtractionResult(
                    iban="DE89370400440532013000", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
                ),
                ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
            ]
        ),
        ["I am Lisa", "Nice weather", "My IBAN is DE89370400440532013000", "Yoda"],
    )

    print("\nS3 Single attribute")
    run(
        "s3",
        ScriptedFakeExtractor(
            [
                ExtractionResult(name="Lisa", intent=ExtractionIntent.PROVIDE_IDENTIFICATION),
            ]
        ),
        ["I am Lisa"],
    )

    print("\nS4 Wrong secret lockout")
    run(
        "s4",
        ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Vader", intent=ExtractionIntent.ANSWER_SECRET),
                ExtractionResult(secret_answer="Luke", intent=ExtractionIntent.ANSWER_SECRET),
                ExtractionResult(secret_answer="Han", intent=ExtractionIntent.ANSWER_SECRET),
            ]
        ),
        ["I am Lisa, phone +14155552671", "Vader", "Luke", "Han"],
    )

    print("\nS5 Failed identification")
    run(
        "s5",
        ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Bob", phone="+14155550001", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
                ),
                ExtractionResult(
                    name="Bob", phone="+14155550002", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
                ),
                ExtractionResult(
                    name="Bob", phone="+14155550003", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
                ),
            ]
        ),
        ["My name is Bob and phone is +14155550001"] * 3,
    )

    print("\nS6 Data request pre-auth")
    run(
        "s6",
        ScriptedFakeExtractor(
            [
                ExtractionResult(intent=ExtractionIntent.REQUEST_DATA),
            ]
        ),
        ["What is my phone number?"],
    )

    print("\nS7 Fresh conversation")
    run(
        "s7",
        ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
            ]
        ),
        ["My name is Lisa and phone is +14155552671"],
    )

    print("\nS8 E2 conflicting label with valid answer")
    run(
        "s8",
        ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.REQUEST_DATA),
            ]
        ),
        ["Hi, I am Lisa, my phone is +14155552671", "It is Yoda"],
    )


if __name__ == "__main__":
    main()
