# Phase 0 Research: Guided Demo Paths

**Feature**: `005-guided-demo-paths`
**Date**: 2026-11-09

## Research Questions

1. Should the offline demo reuse the existing engine or replace it?
2. How should guided paths and their steps be defined and kept maintainable?
3. Should the offline composer be removed or kept alongside guided paths?
4. Should a path auto-play or advance on explicit visitor action?
5. How should switching paths and restarting reset conversation state?
6. How should outcomes and telemetry be determined and displayed?
7. How should the guided mode remain accessible?
8. Which paths should ship initially to cover the workflow?
9. Does the backend or API contract need to change?

---

## Decision 1: Reuse the existing deterministic offline engine as the decision brain

**Decision**: Keep `frontend/src/offlineDemo.ts` unchanged. Guided paths supply the exact visitor messages in order; `offlineSend` continues to compute identification, verification, classification, routing, and termination.

**Rationale**: The engine is already deterministic, mirrors the backend's rules, and is covered by tests (identity matching, secret answers, classification, routing, termination). The problem is the unreliable free-text *input heuristic*, not the decisions. Feeding it scripted messages removes parsing risk while preserving verified behavior and constitution principles II and IV.

**Alternatives considered**:
- *Rewrite the demo engine to be path-aware*: rejected as unnecessary risk to verified logic and a violation of the simplicity principle.
- *Add precomputed transcript arrays per path (bypassing the engine)*: rejected because telemetry and state transitions would no longer reflect the real workflow, weakening the demo's purpose.
- *Keep free-text and improve the parser*: rejected because the user explicitly dislikes the simulated-input approach and parser tuning remains fragile.

---

## Decision 2: Define paths as static, typed data in one module

**Decision**: Add `frontend/src/guidedDemoPaths.ts` exporting typed `GuidedDemoPath` and `GuidedStep` definitions. Each path declares an id, title, description, expected outcome description, and an ordered list of steps, where each step holds the pre-written visitor message and an optional short label.

**Rationale**: A single data module makes paths easy to add or adjust without touching conversation logic, satisfying FR-016. Typed definitions satisfy the type-safety principle and allow unit tests to assert step order and expected outcomes.

**Alternatives considered**:
- *Inline path data in the component*: rejected because it mixes content with presentation and makes tests and future paths harder to maintain.
- *Fetch paths from the backend*: rejected because the offline demo has no backend and paths must work with no network.
- *Store paths in JSON*: rejected because typed TypeScript gives compile-time safety without an extra loader.

---

## Decision 3: Replace free-form input with guided paths only in offline mode

**Decision**: When the source is `offline`, hide or disable the editable composer and suggestion chips, and present the path picker and step controls instead. When the source is `live`, keep the existing editable composer and free-text interaction.

**Rationale**: The unreliable parsing only exists in the in-browser demo. The live backend has real natural-language handling, so restricting it would regress the integration (FR-011, US3). This keeps the change scoped and honest about each mode's capabilities.

**Alternatives considered**:
- *Force guided paths in live mode too*: rejected because it removes real free-text capability and regresses the production experience.
- *Keep both composer and paths in offline mode*: rejected because the user wants to remove the simulated typing; leaving it invites the same confusing, unreliable interaction.

---

## Decision 4: Advance on explicit visitor action, one step at a time

**Decision**: Selecting a path starts a fresh session and shows the prepared next message. A single "Next step" action sends that message unchanged and appends the agent reply. The visitor controls the pace; there is no autoplay timer.

**Rationale**: Explicit advancement is educational (the visitor can read each turn), avoids race conditions and duplicated sends, and makes keyboard/screen-reader testing straightforward. It directly satisfies FR-004 and FR-005.

**Alternatives considered**:
- *Auto-play the whole path*: rejected because it hides the step-by-step reasoning and risks feeling like a static video rather than an interactive demo.
- *Auto-send on selection and then require clicks*: rejected for inconsistent interaction and a surprise first message before the visitor is ready.

---

## Decision 5: Reset the engine session when selecting or restarting a path

**Decision**: Selecting any path (including a different one) and restarting the current path create a fresh `OfflineSession`, reset messages to the greeting, clear telemetry, and reset the step index to the first step. Path switching is blocked while a step is being applied to avoid interleaving.

**Rationale**: Clean resets prevent messages or security state from a previous scenario leaking into the next, satisfying FR-008 and the "switch midway" edge case. A `busy` guard prevents duplicate sends.

**Alternatives considered**:
- *Append a new path onto the existing conversation*: rejected because mixed state is incoherent and could show incorrect classification or routing.
- *Require a page reload to switch*: rejected because it is slower and less discoverable.

---

## Decision 6: Derive outcome and telemetry from the final engine turn

**Decision**: Each step reuses the existing `telemetryFromTurn` mapping. A path is complete when its last step has been applied. The final outcome shown to the visitor is derived from the last `ConversationTurn` (classification, routing status/intent, support department, terminated) and cross-checked in tests against each path's declared expected outcome.

**Rationale**: Outcome and telemetry stay consistent with the deterministic engine rather than a parallel hand-written transcript, satisfying FR-013. Declaring an expected outcome per path enables a data-level test that the demo really demonstrates what its label promises.

**Alternatives considered**:
- *Hard-code outcome text per path*: rejected because it can drift from the engine's actual reply and telemetry.
- *Infer outcome only from the last reply text*: rejected because structured turn fields are more reliable and already exist.

---

## Decision 7: Use accessible, keyboard-first controls and announcements

**Decision**: Present paths as a labelled group of buttons or a radio-style selector, show progress as "Step N of M" with the path title, announce step and outcome changes through a polite live region, and keep all controls reachable by keyboard with visible focus.

**Rationale**: Satisfies FR-014, FR-015, and SC-007, and follows the existing accessibility patterns in `ChatPanel` (`aria-live`, `role="status"`, labelled regions).

**Alternatives considered**:
- *Decorative cards with click handlers only*: rejected because they are not keyboard-operable or clearly announced.
- *Silent state updates*: rejected because screen-reader users would not know a step advanced.

---

## Decision 8: Ship four paths covering the main workflow branches

**Decision**: Initial paths:
1. **Premium billing journey** (Lisa): identity → security answer `Yoda` → billing request; ends authenticated, premium, routed to Insurance and Billing.
2. **Regular appointment journey** (John Doe): identity → security answer `Blue` → appointment request; ends authenticated, regular, routed to Standard Patient Support.
3. **Ambiguous identity journey** (shared phone / ambiguous name): identity that matches more than one fictional record; ends with the request for more detail.
4. **Failed verification journey** (unknown identity repeated): three non-matching identity attempts; ends terminated as a non-client.

**Rationale**: Together these demonstrate success, premium vs regular classification, routing, clarification, and guardrail termination, satisfying FR-006 and US2. All inputs already work with the existing engine's sample records.

**Alternatives considered**:
- *One path only*: rejected because it hides most of the workflow's value.
- *Add a wrong-secret-answer path*: considered but deferred; it overlaps the failed-verification guardrail story and can be added later through the same data module.

---

## Decision 9: No backend, API, or security-logic change

**Decision**: Keep the FastAPI service, API contracts, and deterministic security logic unchanged.

**Rationale**: The feature changes how the offline demo is driven and presented. Backend behavior is out of scope per the spec assumptions and constitution principle III.

**Alternatives considered**:
- *Add a backend "scripted demo" endpoint*: rejected because the static host cannot run the backend and the in-browser engine already exists.
