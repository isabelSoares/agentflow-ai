# Feature Specification: Guided Demo Paths

**Feature Branch**: `005-guided-demo-paths`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "i dont like the way like the demo tries to simulate real input but then it does not work right? i prefer to just have like a demo, maybe like a pre-built message ready to send (not editable) or something you know? or maybe a set of paths and one would select which one to go through you know? what do you think its best?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete a guided demo path without typing (Priority: P1)

A visitor on the static site is shown a small set of named demo paths. They pick one and advance through a fixed sequence of pre-written messages by clicking a single control. The visitor never has to type, and each step reliably produces the expected agent response and updates the visible workflow state.

**Why this priority**: The current offline demo tries to interpret free-form typing, so the experience depends on the visitor phrasing messages the way the parser expects. Replacing that with scripted, non-editable steps removes the failure mode and makes the demo trustworthy for every visitor.

**Independent Test**: Open the static page, select each available path, and advance it to the end using only clicks. Confirm every step produces the scripted response, the composer is not required, and the final outcome is reached without any typing.

**Acceptance Scenarios**:

1. **Given** the page is running the in-browser demo, **When** the visitor looks at the demo area, **Then** they see a set of named paths, each with a one-line description of what it demonstrates.
2. **Given** the visitor selects a path, **When** they advance to the next step, **Then** the prepared visitor message is sent unchanged and the agent's reply for that step is shown.
3. **Given** a path is in progress, **When** the visitor advances through all its steps, **Then** the conversation reaches that path's scripted outcome and the telemetry reflects the decisions made.
4. **Given** the offline demo is active, **When** the visitor looks for the message input, **Then** free-form typing is unavailable or clearly non-essential because every message is provided by the path.
5. **Given** a path has finished, **When** the visitor wants to continue, **Then** they can restart the same path or choose another path from a clean state.

---

### User Story 2 - Paths cover the real workflow outcomes (Priority: P2)

The available paths together demonstrate the meaningful branches of the project: successful identification and verification, premium versus regular classification, request routing to the correct department, and a failed-verification outcome. A visitor can see that the system does not always say yes.

**Why this priority**: A single scripted conversation would hide most of the product's value. The demo exists to show the deterministic security and routing workflow, including its guardrails.

**Independent Test**: Run every path and confirm each ends in a distinct, clearly labelled outcome, none ends in an unexpected or blank state, and the set collectively shows success, classification, routing, and failure.

**Acceptance Scenarios**:

1. **Given** the demo is active, **When** the visitor chooses the premium path, **Then** it completes identification, verification, premium classification, and routing to the appropriate department.
2. **Given** the demo is active, **When** the visitor chooses the regular path, **Then** it completes identification, verification, regular classification, and routing to standard support.
3. **Given** the demo is active, **When** the visitor chooses the failed-verification path, **Then** it shows bounded verification attempts ending in a clear non-client or termination outcome.
4. **Given** the demo is active, **When** the visitor chooses a path whose identity is ambiguous, **Then** the demo demonstrates the clarification response rather than failing.
5. **Given** any path, **When** it reaches its final step, **Then** the outcome is described in plain language and no step is a dead end.

---

### User Story 3 - Live backend behavior is unchanged (Priority: P2)

When a reachable API backend serves the page, the visitor keeps the existing live experience with a free-text composer and no guided-path restriction. Guided paths are the reliable fallback for environments without a backend.

**Why this priority**: The same frontend is used locally and against the deployed service. Restricting the live experience would regress the real integration, where free-text understanding is actually available.

**Independent Test**: Run the page against a reachable backend and confirm the live session starts with an editable composer and no guided-path-only limitation. Then remove the backend and confirm the guided paths appear as the fallback.

**Acceptance Scenarios**:

1. **Given** a reachable API backend, **When** the page loads, **Then** a live session starts and the visitor can type messages as before.
2. **Given** the live backend is available, **When** the visitor uses the demo, **Then** guided-path restrictions do not replace live free-text input.
3. **Given** the backend becomes unavailable, **When** the visitor continues or retries, **Then** the guided-path demo is offered without a page reload.
4. **Given** a genuine service error occurs, **When** the request fails, **Then** the visitor sees an actionable message and is not silently moved into the scripted demo.

---

### User Story 4 - The demo is clear and accessible (Priority: P3)

The demo explains that it is a scripted walkthrough, so visitors understand they are not expected to type. Path selection, advancing, and resetting are usable with a keyboard and are announced to assistive technology.

**Why this priority**: A demo that is reliable but confusing still fails to communicate the project. Accessibility keeps the walkthrough usable for everyone.

**Independent Test**: Navigate path selection and progression with only a keyboard and a screen reader, confirming each state change is announced and every control is reachable and labelled.

**Acceptance Scenarios**:

1. **Given** the guided demo is shown, **When** the visitor reads the demo area, **Then** a short note explains that the steps are scripted and that clicking advances the conversation.
2. **Given** a keyboard-only visitor, **When** they navigate the demo, **Then** they can select a path, advance steps, restart, and choose another path.
3. **Given** a step advances, **When** the conversation updates, **Then** the new message and workflow state are announced through an accessible status mechanism.

### Edge Cases

- The visitor switches paths midway: the conversation resets cleanly and no messages from the previous path remain.
- The visitor reloads the page: the demo starts cleanly and shows the path choices again with no stale messages.
- A path has reached its terminal state: further advancement is prevented and the visitor is offered restart or another path.
- The visitor advances rapidly or repeatedly: duplicate messages are not sent while a step is still being applied.
- A live backend becomes available while a guided path is active: the visitor can switch to the live service without a page reload.
- The page is served with no network: the guided paths still work because they run entirely in the browser.
- The visitor cannot or does not want to type: no path requires free-form text at any step.
- Assistive technology users must receive path changes, step progress, and outcomes as announced status, not only visually.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: In the in-browser (no-backend) demo, the page MUST present a set of selectable guided demo paths instead of depending on free-form typed input.
- **FR-002**: Each guided path MUST have a name and a short plain-language description of the scenario and its expected outcome.
- **FR-003**: Each guided path MUST define a fixed, ordered sequence of pre-written visitor messages that the visitor cannot edit.
- **FR-004**: The visitor MUST be able to advance a selected path one step at a time, and each step MUST send its prepared message unchanged.
- **FR-005**: Each step MUST produce the deterministic agent response and workflow-state update expected for that path.
- **FR-006**: The available paths MUST collectively demonstrate successful identification and verification, premium and regular classification, routing to the correct department, and a failed-verification outcome.
- **FR-007**: The offline demo MUST NOT require or rely on free-form typing, and the message composer MUST be disabled, hidden, or clearly marked as unavailable while guided paths are active.
- **FR-008**: The visitor MUST be able to select a different path or restart the current path at any time, and doing so MUST reset the conversation to a clean state.
- **FR-009**: When a path reaches its final step, the page MUST show a clear outcome and offer restarting or choosing another path.
- **FR-010**: The guided demo MUST use only fictional sample data and MUST NOT expose or log real personal data, credentials, or secret answers.
- **FR-011**: When a reachable API backend serves the page, the existing live experience with an editable free-text composer MUST remain available and MUST NOT be replaced by guided-path-only behavior.
- **FR-012**: The page MUST keep the current backend-availability behavior: prefer the live service, fall back to the guided demo when no backend is available, and show an actionable message for genuine service errors.
- **FR-013**: Every guided step and outcome MUST update the visible workflow and telemetry consistently with the corresponding deterministic decision.
- **FR-014**: The page MUST explain that the demo is a scripted walkthrough so visitors know they are not expected to type.
- **FR-015**: Path selection, step advancement, restart, and path switching MUST be operable with a keyboard, and state changes MUST be announced through an accessible status mechanism.
- **FR-016**: The set of guided paths MUST be defined in a single, maintainable place so a path can be added or adjusted without rewriting the conversation logic.
- **FR-017**: The guided demo MUST NOT present raw status codes or technical stack traces as the visitor-facing experience.

### Key Entities *(include if feature involves data)*

- **Guided Demo Path**: A named, selectable scripted scenario with a description, an ordered set of steps, and a defined final outcome.
- **Guided Step**: A single pre-written visitor message within a path plus the deterministic response and workflow-state change it should produce.
- **Demo Outcome**: The plain-language result at the end of a path, such as an authenticated premium routing, standard support routing, clarification needed, or failed verification.
- **Demo Session**: The conversation state shown to the visitor while a path is running; it is reset when a path is restarted or switched.
- **Sample Patient Record**: Fictional identity data used only to demonstrate the deterministic workflow.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of guided steps in every path produce their expected response and state change, with zero dependency on how the visitor phrases anything.
- **SC-002**: A first-time visitor can complete any path with zero typing and in under 2 minutes.
- **SC-003**: Every available path reaches a clearly described outcome; 0% of paths end in a blank, unexpected, or dead-end state.
- **SC-004**: Switching paths or restarting resets the conversation in under 1 second and leaves no messages from the previous path.
- **SC-005**: The public static page shows 0 raw HTTP status codes and 0 technical error banners during the guided demo.
- **SC-006**: With a reachable backend, 100% of sessions use the live free-text experience and are not restricted to guided paths.
- **SC-007**: Keyboard-only and screen-reader users can select a path, complete it, restart it, and switch paths, with state changes announced.

## Assumptions

- The guided-path approach was chosen over a single pre-built message because it demonstrates the real workflow branches (premium, regular, clarification, failed verification) while still requiring zero typing.
- Guided paths replace free-form input only for the in-browser demo used when no backend is available; the live backend keeps its free-text composer because real natural-language handling is available there.
- The initial path set will cover the existing fictional sample records already used by the demo; the exact number and wording of paths may be refined during planning without changing this specification's intent.
- No backend, API contract, or security-logic changes are required; this feature changes how the offline demo is presented and driven.
- Existing telemetry fields, accessibility patterns, and offline/live detection behavior are reused.
- Visitors have a modern browser with JavaScript enabled, which is required to run the in-browser demo.
