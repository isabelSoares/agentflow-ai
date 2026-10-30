"""Documentation contract tests for the project-level system diagram."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
SYSTEM_DIAGRAM = ROOT / "docs" / "system-diagram.md"
ARCHITECTURE_DOC = ROOT / "docs" / "architecture.md"

REQUIRED_COMPONENT_IDS = [
    "customer",
    "text_channel",
    "voice_channel",
    "request_handler",
    "session_gate",
    "workflow",
    "greeter",
    "bouncer",
    "specialist",
    "input_guard",
    "output_guard",
    "matching",
    "secret",
    "classification",
    "routing",
    "proof",
    "history",
    "session_store",
    "llm",
    "speech",
    "config",
    "response",
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


def _subgraph_block(block: str, name: str) -> str:
    pattern = re.compile(
        rf"^\s*subgraph\s+{re.escape(name)}\[[^\]]*\]\s*$(.*?)^\s*end\s*$",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(block)
    assert match is not None, f"missing subgraph {name}"
    return match.group(1)


def _node_is_defined(block: str, node_id: str) -> bool:
    return re.search(rf"^\s*{re.escape(node_id)}\s*[\[\(\{{]", block, re.MULTILINE) is not None


def test_system_diagram_has_one_mermaid_block_and_no_binary_source() -> None:
    text = _read(SYSTEM_DIAGRAM)
    blocks = _mermaid_blocks(SYSTEM_DIAGRAM)

    assert len(blocks) == 1, "system diagram page must contain exactly one Mermaid block"
    assert blocks[0].lstrip().startswith("flowchart")
    for binary in ("![", "<img", ".png", ".jpg", ".jpeg", ".svg"):
        assert binary not in text, f"system diagram must not depend on binary asset {binary}"


def test_system_diagram_shows_required_components_and_groups() -> None:
    block = _mermaid_blocks(SYSTEM_DIAGRAM)[0]
    lowered = block.lower()

    assert block.count("subgraph") >= 8
    for group in (
        "Channels",
        "Service",
        "InputGuard",
        "Orchestration",
        "OutputGuard",
        "Deterministic",
        "State",
        "External",
    ):
        assert re.search(rf"^\s*subgraph\s+{group}\b", block, re.MULTILINE), (
            f"missing required group: {group}"
        )

    for node_id in REQUIRED_COMPONENT_IDS:
        assert _node_is_defined(block, node_id), f"missing required component: {node_id}"

    required_labels = [
        "customer",
        "text",
        "voice",
        "optional",
        "service boundary",
        "session-authorisation gate",
        "orchestration",
        "greeter",
        "bouncer",
        "specialist",
        "input guardrail",
        "output guardrail",
        "deterministic",
        "identity matching",
        "secret-answer verification",
        "customer classification",
        "support routing",
        "conversation history",
        "session state",
        "llm",
        "speech",
        "configuration",
        "response",
    ]
    for label in required_labels:
        assert label in lowered, f"system diagram is missing required label: {label}"


def test_system_diagram_links_from_primary_documentation() -> None:
    readme = _read(README)
    architecture = _read(ARCHITECTURE_DOC)

    assert "[System Architecture Diagram](docs/system-diagram.md)" in readme
    assert "system-level" in readme.lower()
    assert "docs/system-diagram.md" in architecture
    assert "System Architecture Diagram" in architecture
    assert _mermaid_blocks(ARCHITECTURE_DOC) == [], (
        "the detailed architecture document must not duplicate the system diagram source"
    )


def test_system_diagram_security_boundaries_are_explicit() -> None:
    block = _mermaid_blocks(SYSTEM_DIAGRAM)[0]
    lowered = block.lower()
    deterministic = _subgraph_block(block, "Deterministic")
    input_guard = _subgraph_block(block, "InputGuard")
    output_guard = _subgraph_block(block, "OutputGuard")
    external = _subgraph_block(block, "External")

    assert block.index("session_gate") < block.index("subgraph Orchestration"), (
        "the session-authorisation gate must appear before orchestration"
    )
    assert "deterministic" in lowered
    for node_id in ("matching", "secret", "classification", "routing", "proof"):
        assert node_id in deterministic, f"deterministic group is missing {node_id}"
    assert "input_guard" in input_guard and "deterministic" in input_guard.lower()
    assert "output_guard" in output_guard and "deterministic" in output_guard.lower()

    assert "llm" in external
    assert "external" in external.lower()
    assert "optional" in external.lower()
    assert "optional" in lowered

    for target in (
        "matching",
        "secret",
        "classification",
        "routing",
        "proof",
        "session_gate",
        "input_guard",
        "output_guard",
    ):
        assert re.search(rf"\bllm\s*(?:-->|-.->)\s*(?:\|[^|]*\|\s*)?{target}\b", block) is None, (
            f"language model must not drive security decision {target}"
        )

    explanation = _section(_read(SYSTEM_DIAGRAM), "## Security Boundaries").lower()
    assert "deterministic" in explanation
    assert "never" in explanation or "not" in explanation
    assert "authentication" in explanation
    assert "authorisation" in explanation or "authorization" in explanation


def test_system_diagram_maintenance_guidance_is_actionable() -> None:
    text = _read(SYSTEM_DIAGRAM)
    maintenance = _section(text, "## Maintenance and Preview")

    for required in (
        "docs/system-diagram.md",
        "GitHub",
        "VS Code",
        "uv run pytest tests/unit/test_system_diagram_docs.py -q",
        "uv run pytest",
        "uv run mypy src",
        "uv run ruff check src",
        "authoritative",
        "MUST match the committed source",
        "README",
        "architecture.md",
    ):
        assert required in maintenance, f"maintenance guidance is missing: {required}"

    assert "generator" in maintenance.lower()
    assert "binary" in maintenance.lower()
