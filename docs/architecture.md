# Architecture

## Purpose

This document explains the component boundaries, request lifecycle, security
decisions, and maintenance workflow for AgentFlow AI. The banking support flow is
the reference demo adapter; the core workflow is domain-agnostic. The authoritative
diagrams are the project-level System Architecture Diagram in
[`docs/system-diagram.md`](system-diagram.md) and the architecture and workflow
Mermaid blocks in the [README](../README.md#architecture); this document provides
the detailed narrative and does not duplicate the diagram source.

## Diagram Map

| View | Purpose | Location |
|------|---------|----------|
| System Architecture Diagram | Project-level view of customer channels, the service boundary, deterministic controls, state, and external dependencies. | [`docs/system-diagram.md`](system-diagram.md) |
| Architecture Overview | Full-stack components, trust boundaries, dependencies, and optional integrations. | [README: Architecture](../README.md#architecture) |
| Multi-Agent Workflow | Status-driven transitions across turns, outcomes, and termination handling. | [README: Multi-Agent Workflow](../README.md#multi-agent-workflow) |

The System Architecture Diagram is the entry point for whole-system orientation. The
overview deliberately avoids implying that every agent runs on every request. The workflow
diagram is the source of truth for per-turn behavior. Voice requests enter the same
workflow as transcribed text; they do not bypass identity checks or guardrails.

## Components

| Component | Responsibility | Trust boundary |
|-----------|----------------|----------------|
| **FastAPI service** | Exposes text and optional voice endpoints, session creation, reset, and health checks. | Accepts untrusted requests. |
| **Session-ownership gate** | Verifies the presented proof against the stored proof before any graph or history state is touched. | Deterministic; runs outside LangGraph. |
| **LangGraph orchestration** | Executes the per-turn graph and carries persisted conversation status. | Orchestrates only; does not make identity decisions. |
| **Greeter** | Collects identity attributes, performs 2-of-3 matching, asks the secret question, and verifies the answer. | Deterministic identity and verification logic. |
| **Bouncer** | Classifies an authenticated customer as premium, regular, or non-customer. | Deterministic classification. |
| **Specialist** | Routes authenticated requests to standard support, premium support, or a specialist desk. | Deterministic routing with validated intent. |
| **Input Guardrail** | Blocks empty, manipulative, unsafe, or pre-authentication data requests. | Deterministic policy checks before extraction. |
| **Output Guardrail** | Checks the final reply for privacy and policy violations and replaces unsafe output. | Deterministic; every customer-facing reply passes through it. |
| **Deterministic business logic** | Matching, secret verification, classification, routing, and proof verification. | Never delegated to the LLM. |
| **Conversation history** | Stores redacted user and assistant messages with bounded context. | Session-scoped; stored in the checkpointed `messages` channel. |
| **Session store** | Stores proof digests, active state, and termination state. | Owns access and session lifecycle. |
| **Voice adapters** | Optional STT/TTS adapters that convert between audio and text. | Optional; no separate banking logic. |
| **LLM provider** | Performs natural-language extraction and advisory intent classification. | Untrusted for authentication and authorization. |
| **Configuration** | Environment-driven settings for providers, voice, limits, and phone region. | Validated at startup where applicable. |

## Request Lifecycle

Session access is checked before the graph is invoked. A denied proof returns a
uniform `401` response without reading or changing session state. Once access is
granted, each turn starts at the Input Guardrail and ends at the Output Guardrail
and Respond nodes.

| Turn shape | Starting status | Nodes that run | Typical outcome |
|------------|-----------------|----------------|-----------------|
| First contact | `collecting` | Input Guardrail, Extract, Identify, Output Guardrail, Respond | Unique match asks the secret question. Ambiguous or insufficient details ask for clarification. No match triggers a safe retry or termination after the attempt limit. |
| Secret-question answer | `identified` | Input Guardrail, Extract, Authenticate, Classify, Output Guardrail, Respond | A correct answer authenticates the customer and returns the classification message. An incorrect answer retries or terminates after the attempt limit. |
| Authenticated request | `authenticated` | Input Guardrail, Extract, Specialist, Output Guardrail, Respond | The request is routed to the appropriate department, clarified, or handled with a safe fallback. |
| Blocked input | Any active status | Input Guardrail, Output Guardrail, Respond | A safe refusal is returned without extraction or business logic. |
| Session termination | Any active status | Relevant turn nodes, Output Guardrail, Respond | The reply is returned, then the API layer deactivates the session. |

A unique identity match does not authenticate the customer in the same turn: the
Identify node produces the secret question and ends the turn. On the next turn,
Extract observes `identified` status and routes to Authenticate. This cross-turn
behavior is why the diagram does not draw `identify -> authenticate` as a normal
edge.

## Security Boundaries

| Boundary | Decision | Enforcement | LLM trusted? |
|----------|----------|-------------|--------------|
| Session ownership | A request may use a session only when its proof matches the stored proof. | Constant-time proof verification in `src/banking_support/data/session_access.py`, enforced in `src/banking_support/api/invoker.py` before graph invocation. | No |
| Identity matching | At least two of name, phone, and IBAN must match exactly after normalization. | `src/banking_support/core/matching.py` | No |
| Secret-question verification | The normalized answer must match the registered answer; attempts are limited. | `src/banking_support/core/verification.py` | No |
| Customer classification | Classification uses the trusted repository record for the verified customer. | `src/banking_support/core/classification.py` | No |
| Support routing | Routing requires authenticated status, a trusted classification, and a validated intent. | `src/banking_support/core/routing.py` | No; extracted intent is advisory |
| Input guardrails | Unsafe, manipulative, empty, or pre-authentication data requests are refused. | `src/banking_support/services/guardrails_service.py` and the guardrail node. | No |
| Output guardrails | Privacy and policy violations are replaced before the reply is returned. | `src/banking_support/services/guardrails_service.py` and the output guardrail node. | No |
| Natural-language extraction | The LLM extracts attributes and intent from text. | `src/banking_support/agents/llm.py` | Yes, for extraction only |

The LLM never authenticates a customer, grants authorization, or directly selects
a privileged support destination. Deterministic code validates every security
decision.

## Workflow Consistency

The diagram uses the same node IDs as `src/banking_support/agents/graph.py` so
that documentation tests can compare the graph registry with the diagram. The
`terminated` node is listed separately because it is declared in the graph but is
not reached through normal execution.

| Graph node | Diagram representation | Reachable | Rationale |
|------------|------------------------|-----------|-----------|
| `guardrail` | `guardrail` | Yes | First graph node on every authorized turn. |
| `extract` | `extract` | Yes | Extracts attributes and advisory intent after the input guardrail allows the turn. |
| `identify` | `identify` | Yes | Runs while the conversation is collecting identity details. |
| `authenticate` | `authenticate` | Yes | Runs on a later turn when persisted status is `identified`. |
| `classify` | `classify` | Yes | Runs immediately after successful authentication. |
| `specialist` | `specialist` | Yes | Runs on later turns when persisted status is `authenticated`. |
| `output_guardrail` | `output_guardrail` | Yes | Receives every reply path before Respond. |
| `respond` | `respond` | Yes | Returns the final reply and is followed by end-of-turn handling. |
| `terminated` | Not drawn as an executing node | No | Declared but unreachable in normal execution; termination replies flow through `output_guardrail`, and the API layer deactivates the session. |

## Declared-Unreachable Paths

These paths exist in routing code or graph declarations but are not reachable in
normal execution. They are documented rather than drawn as if they were live.

- **`terminated` node**: The graph registers a `terminated` node and routes to it
  when a terminated flag is already present. Normal termination is produced by the
  Identify or Authenticate node as a reply plus flag, then passed through the
  Output Guardrail and Respond. The API layer deactivates the session after the
  reply, so a later turn cannot reach the node.
- **`identify -> authenticate`**: This conditional target is declared after
  Identify. In practice, Identify always produces a reply (secret question,
  clarification, retry, or termination), so routing goes to the Output Guardrail.
  Authentication happens on the next turn via `extract -> authenticate`.
- **`classify -> specialist`**: Classification always routes to the Output
  Guardrail. Specialist routing happens on a later authenticated turn via
  `extract -> specialist`, not immediately after classification.

## Maintenance and Preview

The Mermaid source in `README.md` and
[`docs/system-diagram.md`](system-diagram.md) is the authoritative diagram source.
Do not add a second Mermaid copy to this document. When the workflow changes:

1. Update the authoritative Mermaid blocks in `README.md`, or the system view in
   `docs/system-diagram.md` when a component, boundary, or dependency changes.
2. Update the [workflow consistency table](#workflow-consistency) and the
   declared-unreachable paths above.
3. Update the prose in this document if a boundary, component, or outcome changed.
4. Preview the diagrams on GitHub or with the VS Code Mermaid preview extension.
5. Run the focused documentation contract tests:

   ```bash
   uv run pytest tests/unit/test_architecture_docs.py -q
   uv run pytest tests/unit/test_system_diagram_docs.py -q
   ```

6. Run the full quality gates:

   ```bash
   uv run pytest
   uv run mypy src && uv run ruff check src
   ```

The focused test parses the Mermaid blocks and compares their node IDs with the
graph registry from `src/banking_support/agents/nodes.py` (the same registry used
by `src/banking_support/agents/graph.py`). It also checks that every customer
response passes through the Output Guardrail, that unreachable paths are not drawn
as normal transitions, and that the consistency table covers every registered
node. Session-gate behavior is verified against
`src/banking_support/api/invoker.py`.

The test is offline and uses scripted fakes. No API key, network access, or image
generation step is required. If a new node is added to the graph, add it to the
workflow diagram and to the consistency table in the same change.

## Links

- [README architecture](../README.md#architecture)
- [System Architecture Diagram](system-diagram.md)
- [README multi-agent workflow](../README.md#multi-agent-workflow)
- [Workflow consistency](#workflow-consistency)
- [Declared-unreachable paths](#declared-unreachable-paths)
- [Maintenance and preview](#maintenance-and-preview)
