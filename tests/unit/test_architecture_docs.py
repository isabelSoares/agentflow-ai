"""Documentation contract tests for the Mermaid architecture diagrams."""

from __future__ import annotations

import re
from pathlib import Path

from banking_support.agents.llm import (
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
)
from banking_support.agents.nodes import make_nodes
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.support_directory import default_support_directory

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
ARCHITECTURE_DOC = ROOT / "docs" / "architecture.md"

LEGACY_IMAGE = "lang-" + "graph.png"
LEGACY_GENERATOR = "generate_" + "architecture_diagram"

GRAPH_NODE_IDS = [
    "guardrail",
    "extract",
    "identify",
    "authenticate",
    "classify",
    "specialist",
    "output_guardrail",
    "respond",
]

OVERVIEW_ONLY_EXCLUDED_NODE_IDS = [
    "extract",
    "identify",
    "authenticate",
    "classify",
    "specialist",
    "output_guardrail",
    "respond",
]


def _read(path: Path) -> str:
    assert path.exists(), f"expected documentation artifact at {path}"
    return path.read_text(encoding="utf-8")


def _mermaid_blocks(path: Path) -> list[str]:
    text = _read(path)
    return re.findall(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)


def _section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    assert match is not None, f"missing section {heading}"
    return match.group(1)


def _node_is_defined(block: str, node_id: str) -> bool:
    return re.search(rf"^\s*{re.escape(node_id)}\s*[\[\(\{{]", block, re.MULTILINE) is not None


def _row_for(table: str, node_id: str) -> str:
    pattern = re.compile(
        rf"^\|\s*`?{re.escape(node_id)}`?\s*\|.*$",
        re.MULTILINE,
    )
    match = pattern.search(table)
    assert match is not None, f"missing consistency row for {node_id}"
    return match.group(0)


def test_readme_has_architecture_sections_and_doc_link() -> None:
    readme = _read(README)

    assert re.search(r"^## Architecture\s*$", readme, re.MULTILINE)
    assert re.search(r"^### Architecture Overview\s*$", readme, re.MULTILINE)
    assert re.search(r"^### Multi-Agent Workflow\s*$", readme, re.MULTILINE)
    assert "docs/architecture.md" in readme
    assert "#maintenance-and-preview" in readme


def test_legacy_generated_diagram_is_removed_and_unreferenced() -> None:
    assert not (ROOT / LEGACY_IMAGE).exists()
    assert not (ROOT / "scripts" / f"{LEGACY_GENERATOR}.py").exists()

    current_docs = f"{_read(README)}\n{_read(ARCHITECTURE_DOC)}"
    assert LEGACY_IMAGE not in current_docs
    assert LEGACY_GENERATOR not in current_docs


def test_overview_diagram_contract() -> None:
    blocks = _mermaid_blocks(README)
    assert len(blocks) == 2, "README must contain exactly two authoritative Mermaid blocks"

    overview = blocks[0]
    assert overview.lstrip().startswith("flowchart")
    assert overview.count("subgraph") >= 5

    required_labels = [
        "FastAPI",
        "LangGraph",
        "Greeter",
        "Bouncer",
        "Specialist",
        "Input Guardrail",
        "Output Guardrail",
        "LLM",
        "Deterministic",
        "Conversation history",
        "Session",
        "STT",
        "TTS",
        "optional",
    ]
    lowered = overview.lower()
    for label in required_labels:
        assert label.lower() in lowered, f"overview is missing required label: {label}"

    assert "-.->" in overview, "optional or external paths must use dashed edges"
    for status in ("collecting", "identified", "authenticated"):
        assert status not in lowered, f"overview must not contain workflow status {status}"
    for node_id in OVERVIEW_ONLY_EXCLUDED_NODE_IDS:
        assert not _node_is_defined(overview, node_id), (
            f"overview must not define turn-level node {node_id}"
        )


def test_workflow_diagram_contract() -> None:
    blocks = _mermaid_blocks(README)
    assert len(blocks) == 2
    workflow = blocks[1]
    assert workflow.lstrip().startswith("flowchart")

    for node_id in GRAPH_NODE_IDS:
        assert _node_is_defined(workflow, node_id), f"workflow is missing node {node_id}"

    assert not _node_is_defined(workflow, "terminated"), (
        "declared terminated node must not be drawn as an executing node"
    )
    assert "session_gate" in workflow
    assert "deny_401" in workflow

    for outcome in ("OK", "BLOCKED", "CLARIFY", "FAILED", "TERMINATED"):
        assert outcome in workflow, f"workflow is missing outcome label {outcome}"

    assert (
        re.search(
            r"identify\s*-->\s*(?:\|[^|]*\|\s*)?authenticate\b",
            workflow,
        )
        is None
    ), "identify must not transition to authenticate on the same turn"
    assert (
        re.search(
            r"classify\s*-->\s*(?:\|[^|]*\|\s*)?specialist\b",
            workflow,
        )
        is None
    ), "classify must not transition to specialist on the same turn"

    respond_sources = set(
        re.findall(
            r"^\s*(\w+)\s*-->\s*(?:\|[^|]*\|\s*)?respond\b",
            workflow,
            re.MULTILINE,
        )
    )
    assert respond_sources, "workflow must show paths into respond"
    assert respond_sources <= {"output_guardrail", "safe_replace"}, (
        f"all responses must pass through output_guardrail, found {respond_sources}"
    )

    assert "output_guardrail" in workflow
    assert "respond" in workflow
    assert workflow.index("session_gate") < workflow.index("guardrail")
    assert "next authorized turn" in workflow


def test_consistency_table_covers_all_graph_nodes() -> None:
    architecture = _read(ARCHITECTURE_DOC)
    table = _section(architecture, "## Workflow Consistency")

    node_map = make_nodes(
        InMemoryCustomerRepository(),
        ScriptedFakeExtractor(),
        intent_classifier=ScriptedFakeSupportIntentClassifier(),
        support_directory=default_support_directory(),
    )
    for node_id in node_map:
        _row_for(table, node_id)

    terminated_row = _row_for(table, "terminated")
    assert "unreachable" in terminated_row.lower()
    assert "no" in terminated_row.lower()

    assert "identify -> authenticate" in architecture
    assert "classify -> specialist" in architecture
    assert "declared" in architecture.lower()


def test_maintenance_and_documentation_contract() -> None:
    architecture = _read(ARCHITECTURE_DOC)
    readme = _read(README)

    assert re.search(r"^## Purpose\s*$", architecture, re.MULTILINE)
    assert re.search(r"^## Links\s*$", architecture, re.MULTILINE)
    assert re.search(r"^## Maintenance and Preview\s*$", architecture, re.MULTILINE)
    for required in (
        "README.md",
        "graph.py",
        "nodes.py",
        "invoker.py",
        "GitHub",
        "VS Code",
        "uv run pytest tests/unit/test_architecture_docs.py -q",
        "consistency table",
    ):
        assert required in architecture, f"maintenance section is missing: {required}"

    assert "#maintenance-and-preview" in readme
    assert _mermaid_blocks(ARCHITECTURE_DOC) == [], (
        "the detailed document must not duplicate the authoritative Mermaid source"
    )
