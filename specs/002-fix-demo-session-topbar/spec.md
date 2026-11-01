# Feature Specification: Demo Session Recovery & Rounded Highlighted Topbar

**Feature Branch**: `002-fix-demo-session-topbar`

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description: "The demo don't allow 'start a session to begin' and appears an error 'Request failed with status 404'. Solve it. Plus, the topbar must rounded with left and right margins, and give highlight the topbar for that."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start and use the demo session (Priority: P1)

A visitor opens the demo page and immediately gets a working conversation session. The composer is enabled, the "Start a session to begin" placeholder is replaced by an active prompt, and no error banner appears when the backend is running. If session creation fails, the visitor can retry with the "Start session" button.

**Why this priority**: The demo is the product's primary proof point. If a session cannot start, every other capability is unreachable and the demo appears broken.

**Independent Test**: Open the demo with the backend running, confirm a session is created automatically, the composer becomes usable, and the "Start session" control remains available only when no session exists. Then stop the backend, reload, and confirm a clear recoverable error appears.

**Acceptance Scenarios**:

1. **Given** the backend is running and the page is opened, **When** the page finishes loading, **Then** a session is created automatically and the composer becomes enabled without any error message.
2. **Given** no active session, **When** the visitor selects "Start session", **Then** a new session is created and the first assistant message is shown.
3. **Given** the backend is running, **When** any session-start request is made, **Then** the request reaches the session endpoint and does not return a 404.
4. **Given** session creation fails, **When** the failure is shown, **Then** the error explains that the session could not be started and the visitor can retry.
5. **Given** a session is active, **When** the visitor sends a message, **Then** the message is delivered to the same session and the reply is rendered.

---

### User Story 2 - Consistent session access across environments (Priority: P2)

The same demo works when run locally with the development server and when served as a static build behind the production API route. Session requests always reach the backend instead of the static host, so the 404 is eliminated in both configurations.

**Why this priority**: The defect is environment-dependent; fixing only one configuration leaves the demo broken for the other deployment path.

**Independent Test**: Run the demo locally with the documented development command, then build and serve the static output with the documented production routing. In both cases, start a session and confirm it succeeds.

**Acceptance Scenarios**:

1. **Given** the local development setup, **When** the page creates a session, **Then** the request is routed to the backend and succeeds.
2. **Given** the static production build served with the documented API route, **When** the page creates a session, **Then** the request is routed to the backend and succeeds.
3. **Given** the backend is unreachable, **When** the page tries to create a session, **Then** the visitor sees an actionable connectivity message rather than a bare status-code error.

---

### User Story 3 - Rounded, highlighted topbar with side margins (Priority: P3)

The top navigation bar appears as a distinct floating surface with rounded corners, visible space on its left and right sides, and a subtle highlight that separates it from the page background while scrolling.

**Why this priority**: This is a visual polish request that improves perceived quality and focus, but it does not block the demo workflow.

**Independent Test**: Load the page at desktop and mobile widths, confirm the topbar has visible left and right margins, rounded corners on all sides, and a highlight that distinguishes it from the background. Scroll and confirm the sticky bar keeps its rounded appearance without content overlap.

**Acceptance Scenarios**:

1. **Given** the page is loaded on a desktop viewport, **When** the topbar is displayed, **Then** it has visible left and right margins, rounded corners, and a highlight treatment.
2. **Given** the page is loaded on a narrow mobile viewport, **When** the topbar is displayed, **Then** it keeps left and right margins and rounded corners without causing horizontal scrolling.
3. **Given** the visitor scrolls the page, **When** the topbar remains sticky, **Then** it stays visually separated from page content and retains its rounded highlighted appearance.
4. **Given** the topbar highlight is applied, **When** the navigation links receive keyboard focus, **Then** focus remains clearly visible and text contrast is preserved.

### Edge Cases

- The backend is not running or refuses the connection: the visitor must see a clear, actionable message and be able to retry, not a raw 404.
- The backend returns a server error or malformed response: the visitor must see a readable error and keep the ability to start a new session.
- Session creation is slow: the visitor must see a starting state and the controls must not allow duplicate session starts.
- The page is loaded at a very narrow width: the topbar margins and rounding must not introduce horizontal scrolling or clipped navigation.
- The topbar is sticky while scrolling: its rounded corners and highlight must remain visible and must not cover interactive content.
- The API route prefix is missing in a deployment: the failure must be detectable and documented as a deployment requirement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The demo MUST create a session automatically when the page loads, without requiring an extra click.
- **FR-002**: The demo MUST provide a "Start session" action whenever no active session exists, and starting a session MUST enable the message composer.
- **FR-003**: Session creation and subsequent session requests MUST reach the backend in both the local development setup and the documented static production setup.
- **FR-004**: The session-start flow MUST NOT surface a 404 response when the backend is running and correctly routed.
- **FR-005**: When session creation fails, the demo MUST show a human-readable, actionable error and MUST allow the visitor to retry.
- **FR-006**: While a session is starting, the demo MUST show a starting state and MUST prevent duplicate session creation.
- **FR-007**: An active session MUST retain its identity across messages so replies belong to the same conversation.
- **FR-008**: The topbar MUST be visually separated from the viewport edges by visible left and right margins.
- **FR-009**: The topbar MUST have rounded corners on all sides.
- **FR-010**: The topbar MUST carry a visual highlight that distinguishes it from the page background, using the existing design language.
- **FR-011**: The topbar MUST preserve its rounded, margined, highlighted appearance at desktop and mobile widths without causing horizontal scrolling.
- **FR-012**: The topbar MUST remain sticky while scrolling and MUST NOT overlap or obscure interactive page content.
- **FR-013**: Navigation text and keyboard focus indicators in the highlighted topbar MUST remain readable and clearly visible.
- **FR-014**: The deployment requirements for routing demo requests to the backend MUST be documented so the 404 cannot silently return in a future deployment.

### Key Entities *(include if feature involves data)*

- **Session**: A demo conversation identified by a conversation identifier and an ownership proof. The session is created when the demo starts, is reused for every message, and is replaced when reset or restarted.
- **Topbar**: The persistent navigation surface containing the product brand and primary navigation links, displayed above the page content while scrolling.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the backend running, 100% of demo page loads create a usable session within 2 seconds.
- **SC-002**: The session-start flow produces zero 404 responses in both the documented local and static production setups.
- **SC-003**: When the backend is unavailable, 100% of attempts show an actionable error message within 2 seconds and offer a retry path.
- **SC-004**: The topbar has at least 16 pixels of visible space on each side at desktop widths and at least 12 pixels at mobile widths, with rounded corners visible on all four sides.
- **SC-005**: The page shows no horizontal scrolling at viewport widths from 320 pixels upward.
- **SC-006**: The topbar highlight preserves readable text and clearly visible keyboard focus in manual accessibility review.
- **SC-007**: A first-time visitor can start a session and send a message without encountering a technical status-code error.

## Assumptions

- The backend is expected to run locally on port 8000, as described in the project documentation.
- In the static production setup, the frontend and backend share an origin and the backend is exposed under a dedicated route prefix, as described in the project documentation.
- "Topbar" refers to the existing sticky site header containing the brand and primary navigation.
- "Highlight" is interpreted as a subtle accent border and/or glow consistent with the existing dark visual design, not a solid color change.
- The session request contract (conversation creation, message sending, reset) remains unchanged; this work corrects request routing and presentation.
- Existing authentication, guardrail, and telemetry behavior is out of scope and must not change.
- The visual change is expected to preserve the current sticky navigation behavior and responsive layout.
