# Feature Specification: Automatic Static-Site Demo Fallback

**Feature Branch**: `004-static-chat-fallback`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "in this page https://isabelsoares.github.io/agentflow-ai/ 'i cannot start a session to begin' or write anything in demo, always showing this error 'This page is served as a static site without an API backend, so the request was rejected (405 Method Not Allowed). Use the offline demo on this page, or run the full stack locally — see the README.'. Add a fix that allows users to do a demo and understand what this project do and interact it, that's the reason there is a frontend side."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Demo works out of the box on the public static site (Priority: P1)

A visitor opens the publicly hosted page, which has no API backend behind it. Without clicking anything extra or seeing a technical error, an interactive support conversation starts, the message box is usable, and the visitor can complete a full demo turn from identity verification through routing.

**Why this priority**: The public page is the primary way people evaluate the project. If the demo cannot start, every capability the project demonstrates is unreachable and the product appears broken — which is the exact failure being reported.

**Independent Test**: Open the deployed page in a browser with no backend available. Confirm an active conversation appears automatically, no technical status-code error is shown, the message box accepts text, and a complete sample scenario reaches a routed outcome.

**Acceptance Scenarios**:

1. **Given** the page is served without a reachable API backend, **When** the page finishes loading, **Then** an interactive demo conversation starts automatically and the message box is enabled.
2. **Given** the offline demo has started, **When** the visitor reads the page, **Then** a clear, non-blocking notice explains that the deterministic demo is running in the browser rather than against the live service.
3. **Given** the offline demo is active, **When** the visitor sends a message, **Then** a reply is rendered and no technical error banner appears.
4. **Given** the offline demo is active, **When** the visitor follows the sample scenario (identify with two attributes, answer the security question, ask for billing help), **Then** the conversation advances through identification, verification, classification, and routing.
5. **Given** the page is served without a reachable backend, **When** the visitor views the page, **Then** no raw status-code text (such as "405 Method Not Allowed") is presented as a failure.

---

### User Story 2 - Visitors understand the project and how to interact (Priority: P2)

A first-time visitor can quickly understand what AgentFlow AI does and exactly what to type to experience it, without opening the README or any external documentation.

**Why this priority**: The frontend exists to explain and demonstrate the project. A working but unexplained demo still fails its purpose for a newcomer.

**Independent Test**: Show the page to someone unfamiliar with the project and confirm they can state what it does and complete the demo scenario using only on-page guidance.

**Acceptance Scenarios**:

1. **Given** a first-time visitor lands on the demo, **When** they read the demo area, **Then** they see a concise explanation of what the project does and what the demo will show them.
2. **Given** the visitor wants to try the demo, **When** they look for guidance, **Then** they see a suggested scenario with the fictional sample details needed to complete it (name plus phone or date of birth, the security answer, and a support request).
3. **Given** the visitor follows the suggested scenario, **When** they complete it, **Then** the conversation reaches a routed outcome without needing outside instructions.
4. **Given** the visitor prefers to explore freely, **When** they send their own messages, **Then** the demo responds coherently or gives a clarification prompt rather than failing.

---

### User Story 3 - Live backend is preferred when available (Priority: P2)

When the page is connected to a working API backend, the visitor uses the real service and never sees the offline notice. The offline demo remains a fallback, not the default behavior.

**Why this priority**: The same frontend is used locally and against a live deployment. Automatically preferring the offline demo would hide the real integration and regress the production setup.

**Independent Test**: Run the page against a reachable backend and confirm the live session starts, the offline notice is absent, and messages are served by the backend. Then make the backend unavailable and confirm the fallback takes over.

**Acceptance Scenarios**:

1. **Given** the API backend is reachable, **When** the page loads, **Then** a live session starts and no offline notice is displayed.
2. **Given** the API backend is reachable, **When** the visitor sends messages, **Then** replies come from the live service.
3. **Given** the backend was reachable and later becomes unreachable, **When** the visitor continues, **Then** they see an actionable message and can retry or continue with the demo.
4. **Given** the visitor previously used the offline demo, **When** a live backend becomes available and the visitor retries, **Then** the live session can be started without a page reload.

---

### User Story 4 - Genuine service errors are not hidden (Priority: P3)

If the service is reachable but rejects a request for a legitimate reason (for example an authorization or server-side failure), the visitor sees an actionable message and is not silently switched into the offline demo.

**Why this priority**: Masking real failures would hide integration defects and mislead maintainers and visitors about system health.

**Independent Test**: Simulate a genuine service error and confirm no offline fallback occurs, a readable explanation is shown, and the visitor can retry.

**Acceptance Scenarios**:

1. **Given** the service responds with a genuine error, **When** the request fails, **Then** the visitor sees a readable, actionable message.
2. **Given** a genuine service error occurred, **When** the visitor looks at the demo, **Then** the offline demo is not started and the offline notice is not shown.
3. **Given** a genuine service error occurred, **When** the visitor retries and the service recovers, **Then** the session starts successfully.

---

### Edge Cases

- The page is opened on any static host that rejects chat requests (not only the current host): the offline demo must still start automatically.
- The backend is slow or hangs on the initial request: the visitor must get an interactive experience without waiting indefinitely.
- The network is completely offline: the offline demo must still work because it runs entirely in the browser.
- The page is served with an incorrect API address or route: this must be treated like an unavailable backend and fall back to the demo.
- The visitor sends a message that does not match any sample identity: the demo must ask for more information rather than failing.
- The visitor answers the security question incorrectly: the demo must give bounded retries and a clear outcome.
- The visitor reloads the page: the demo must start cleanly again without duplicated or stale messages.
- The live service returns a genuine failure: the offline demo must not start, and the visitor must be told how to recover.
- Assistive technology users must receive the offline notice and session state changes as announced status, not only visually.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The page MUST detect when no API backend is available and automatically provide an interactive demo without requiring a second action from the visitor.
- **FR-002**: When the demo takes over because no backend is available, the page MUST NOT present a raw status-code error as the primary experience.
- **FR-003**: The page MUST show a clear, non-blocking notice explaining that the demo is running in-browser without a backend.
- **FR-004**: The page MUST enable the message input and send action as soon as the demo session is active.
- **FR-005**: The in-browser demo MUST support the complete reference scenario: greeting, identity matching from at least two attributes, security-question verification, classification, and support routing.
- **FR-006**: The demo MUST use only fictional sample data and MUST NOT expose or log real personal data, credentials, or secret answers.
- **FR-007**: The page MUST present a concise explanation of what the project does and why the demo is interactive.
- **FR-008**: The page MUST present a suggested scenario with the sample details required to complete the demo.
- **FR-009**: The page MUST use a reachable API backend when one is available and MUST NOT show the offline notice in that case.
- **FR-010**: The page MUST distinguish an unavailable backend from a genuine service error, and MUST NOT silently start the offline demo for a genuine service error.
- **FR-011**: When a request fails after a session is active, the visitor MUST see an actionable message and MUST be able to retry.
- **FR-012**: The visitor MUST be able to retry starting a live session without reloading the page.
- **FR-013**: The fallback MUST work on any static deployment, not only one specific hosting provider.
- **FR-014**: The page MUST announce the offline notice and session-state changes through an accessible status mechanism.
- **FR-015**: The page MUST document the static-hosting fallback behavior for maintainers so future deployments keep it working.

### Key Entities *(include if feature involves data)*

- **Demo Session**: A conversation shown to a visitor. It is either served by the live backend or by the in-browser demo, and it advances through identification, verification, classification, and routing.
- **Visitor Guidance**: The on-page explanation and suggested scenario that tell a newcomer what the project does and how to interact with the demo.
- **Backend Availability State**: The observed condition of the API connection, used to decide whether to show the live experience, the offline demo, or an actionable error.
- **Sample Patient Record**: Fictional identity data (name, phone, date of birth, security question and answer, service tier) used only to demonstrate the deterministic workflow.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of visits to the static-hosted page produce an interactive session within 2 seconds, with no visitor action required.
- **SC-002**: A first-time visitor can complete the full sample scenario within 3 minutes using only on-page guidance.
- **SC-003**: No visitor-facing failure message contains a raw HTTP status code on the static-hosted page.
- **SC-004**: With a reachable backend, 100% of demo loads use the live service and show no offline notice.
- **SC-005**: Genuine service errors result in the offline demo starting in 0% of cases, and always show an actionable message.
- **SC-006**: The offline demo works with the network disabled, demonstrating zero dependency on a backend during fallback.
- **SC-007**: Keyboard-only and screen-reader users can reach the demo notice and complete the sample scenario with announced status changes.

## Assumptions

- The public deployment is a static site that cannot run the Python backend; the in-browser demo mirrors the backend's deterministic reference behavior.
- The offline demo is an evaluation and demonstration aid, not a production channel for real patient data.
- All sample patient details used by the demo are fictional and safe to display.
- A genuine backend error (for example authorization or server failure) indicates a real integration problem and must remain visible rather than being masked by the fallback.
- The existing live API contract and security behavior are unchanged; this feature changes how the frontend presents and falls back between the live and in-browser experiences.
- Visitors are assumed to have a modern browser with JavaScript enabled, which is required to run the interactive demo.
- The guided scenario uses the existing sample record (Lisa, the listed phone number, date of birth, and security answer) already used by the offline demo.
