# System Architecture Diagram

This page presents the project-level system view for AgentFlow AI. The banking support flow is the reference demo adapter; the service boundaries and deterministic controls are domain-agnostic.
It shows how customers reach the service, where authorisation and deterministic security
decisions happen, which responsibilities run inside the system, and which services remain
external. It complements the detailed architecture overview and multi-agent workflow rather
than replacing them: per-turn transitions and detailed component behaviour remain in the
[detailed architecture](architecture.md) and the
[README workflow view](../README.md#multi-agent-workflow).

## System Diagram

```mermaid
flowchart TB
    subgraph Channels["Customer channels"]
        customer["Customer"]
        text_channel["Text chat channel"]
        voice_channel["Voice channel (optional STT/TTS)"]
    end

    subgraph Service["FastAPI service boundary"]
        request_handler["Request handling and validation"]
        session_gate["Session-authorisation gate"]
        deny["401 access denied"]
    end

    subgraph InputGuard["Deterministic input guardrail"]
        input_guard["Input Guardrail (deterministic)"]
    end

    subgraph Orchestration["LangGraph orchestration and agent responsibilities"]
        workflow["Per-turn workflow (status-driven agent selection)"]
        greeter["Greeter: collect identity"]
        bouncer["Bouncer: classify customer"]
        specialist["Specialist: route request"]
    end

    subgraph OutputGuard["Deterministic output guardrail"]
        output_guard["Output Guardrail (deterministic)"]
    end

    subgraph Deterministic["Deterministic business logic"]
        matching["2-of-3 identity matching"]
        secret["Secret-answer verification"]
        classification["Customer classification"]
        routing["Support routing"]
        proof["Session-proof verification"]
    end

    subgraph State["State and session management"]
        history["Conversation history"]
        session_store["Session ownership store (session state)"]
    end

    subgraph External["External services and configuration"]
        llm["LLM provider (external, interpretation and advisory intent only)"]
        speech["Speech provider (optional STT/TTS)"]
        config["Environment configuration"]
    end

    response["Customer response"]

    customer --> text_channel
    customer -.-> voice_channel
    text_channel --> request_handler
    voice_channel -.-> request_handler
    request_handler --> session_gate
    session_gate -->|authorised| input_guard
    session_gate -->|denied| deny
    session_gate -.-> proof
    proof -.-> session_store
    input_guard -->|allowed| Orchestration
    input_guard -->|blocked| output_guard
    Orchestration --> output_guard
    Orchestration -.->|status-driven| Deterministic
    Orchestration -.-> State
    Orchestration -.-> External
    voice_channel -.-> speech
    output_guard --> response
    deny --> response
    response --> customer

    classDef channel fill:#E7F0FF,stroke:#1F4E8C,color:#1F2937
    classDef service fill:#E8F5E9,stroke:#1A7F37,color:#1F2937
    classDef guard fill:#FFF4D6,stroke:#8A6100,color:#1F2937
    classDef orchestration fill:#E0F2FE,stroke:#0369A1,color:#1F2937
    classDef deterministic fill:#DDF4E4,stroke:#1A7F37,color:#1F2937
    classDef state fill:#E0F2F1,stroke:#0F766E,color:#1F2937
    classDef external fill:#F1F5F9,stroke:#475569,color:#1F2937
    classDef blocked fill:#FFE2E0,stroke:#B42318,color:#1F2937
    classDef success fill:#DDF4E4,stroke:#1A7F37,color:#1F2937

    class customer,text_channel,voice_channel channel
    class request_handler,session_gate service
    class input_guard,output_guard guard
    class workflow,greeter,bouncer,specialist orchestration
    class matching,secret,classification,routing,proof deterministic
    class history,session_store state
    class llm,speech,config external
    class deny blocked
    class response success
```

## How to Read the Diagram

- **Solid arrows** show primary request and response paths. **Dashed arrows** show optional
  voice handling, external calls, shared state, or supporting verification.
- **Channels** are the customer-facing ways into the system. Voice is optional and uses the
  same authorisation and security controls as text; it is not a separate business path.
- **Service boundary** is the first trust boundary. Every request passes through request
  handling and the session-authorisation gate before orchestration starts. A denied request
  returns a uniform `401` response and does not reach the workflow.
- **Orchestration** selects the responsible agent for the current turn based on persisted
  conversation status. Not every agent runs on every request.
- **Deterministic business logic and guardrails** contains the decisions that must be
  reproducible: identity matching, secret-answer verification, customer classification,
  support routing, session-proof verification, and input/output guardrails.
- **State** is system-managed. Conversation history and session ownership are not agent
  responsibilities.
- **External services** are outside the security-critical boundary. The language model is
  used for interpretation and advisory intent classification only. Voice and speech
  providers are optional.

## Security Boundaries

| Boundary | What is deterministic | What the language model may do |
|----------|-----------------------|-------------------------------|
| Session ownership | The presented session proof is verified against the stored proof before graph or history state is touched. | Nothing. It never authorises session access. |
| Identity | At least two of name, phone, and IBAN must match after normalisation. | Extract candidate attributes for the conversation. |
| Secret answer | The normalised answer is verified against the registered answer with attempt limits. | Extract the answer text; it never decides whether the answer is correct. |
| Classification | The customer is classified from the trusted repository record. | Provide advisory intent only. |
| Routing | Routing requires authenticated status, trusted classification, and validated intent. | Suggest intent; it never selects a privileged destination. |
| Guardrails | Input and output policy checks are deterministic and every customer-facing reply passes through the output guardrail. | Nothing. It never overrides a guardrail decision. |

The language model must never perform authentication or authorisation, classify an account
authoritatively, or choose a privileged support destination. Deterministic code owns every
security decision.

## Relationship to Other Views

| View | What it answers | Where to find it |
|------|-----------------|------------------|
| **System Architecture Diagram** (this page) | What the whole system contains, which boundaries it crosses, and which dependencies are external. | This page. |
| **Architecture Overview** | Which components, trust boundaries, and optional integrations exist in more detail. | [README: Architecture](../README.md#architecture) |
| **Multi-Agent Workflow** | Which nodes and conditional transitions run on a given turn, including blocked, clarification, failure, and termination outcomes. | [README: Multi-Agent Workflow](../README.md#multi-agent-workflow) |
| **Detailed Architecture** | Component responsibilities, request lifecycle, declared-unreachable paths, and maintenance rationale. | [Detailed architecture](architecture.md) |

## Maintenance and Preview

The authoritative source for the system-level view is
[`docs/system-diagram.md`](system-diagram.md). Do not duplicate this Mermaid block in the
README or in [`docs/architecture.md`](architecture.md). The repository does not use a
diagram generator, screenshot, or binary image for this view; the committed Mermaid source
is authoritative. If a future generator is introduced, its output MUST match the committed source.

Preview the diagram on GitHub or with a GitHub-compatible Markdown/Mermaid preview such as
the VS Code Markdown preview. Check both light and dark themes and a narrow pane before
merging.

When a component, dependency, boundary, or security responsibility changes:

1. Update the Mermaid block in `docs/system-diagram.md`.
2. Update the explanation or security boundaries above if the meaning changed.
3. Update the Diagram Map or links in [`docs/architecture.md`](architecture.md) if
   navigation changed.
4. Update [`tests/unit/test_system_diagram_docs.py`](../tests/unit/test_system_diagram_docs.py)
   if the expected content changed.
5. Preview the page and run the focused documentation test:

   ```bash
   uv run pytest tests/unit/test_system_diagram_docs.py -q
   ```

6. Run the full quality gates:

   ```bash
   uv run pytest
   uv run mypy src && uv run ruff check src
   ```

## Links

- [README architecture](../README.md#architecture)
- [README multi-agent workflow](../README.md#multi-agent-workflow)
- [Detailed architecture](architecture.md)
- [System diagram documentation test](../tests/unit/test_system_diagram_docs.py)
