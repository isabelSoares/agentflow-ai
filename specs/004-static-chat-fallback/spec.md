# Feature Specification: Seamless Static-Site Chat Fallback

**Feature Branch**: `fix/static-chat-fallback`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "create a new branch based on main branch and solve this issue This page is served as a static site without an API backend, so the request was rejected (405 Method Not Allowed). Use the offline demo on this page, or run the full stack locally — see the README."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start a chat on the static page without hitting a dead-end error (Priority: P1)

A visitor opens the publicly hosted demo page (served as a static site with no API
backend behind it) and clicks **Start session**. Instead of seeing a failed-request
error such as "the request was rejected (405 Method Not Allowed)", the visitor is
placed directly into a working in-browser demo conversation, clearly told that they
are in offline demo mode, and can carry the guided support scenario through to
completion without any further setup.

**Why this priority**: The raw 405 message is the exact issue reported; it is the
first thing a public visitor sees, and it makes the live page look broken. Removing
the dead end is the core value of this feature.

**Independent Test**: Load the page in an environment where no API answers (static
host simulation), click **Start session**, and verify a usable demo conversation
begins with an explicit offline-mode indicator — no rejected-request error is shown.

**Acceptance Scenarios**:

1. **Given** the page is served without an API backend, **When** the visitor clicks **Start session**, **Then** an offline demo conversation begins and no rejected-request (405) error banner is displayed.
2. **Given** the offline demo has started, **When** the visitor reads the page, **Then** a clear, visible indicator states that the conversation is running locally in the browser without a backend.
3. **Given** the offline demo is running, **When** the visitor completes the guided scenario (introduce themselves, answer the identity question, ask for help), **Then** responses progress through verification and department routing exactly as the guided demo defines, ending in a routed outcome.
4. **Given** the page is served without an API backend, **When** the visitor resets the session, **Then** the session restarts in offline mode without surfacing a backend error.

---

### User Story 2 - Understand how to get the full experience (Priority: P2)

A visitor who wants the real, backend-backed assistant (not the offline demo) is
told plainly that the hosted page has no API backend and is pointed to the two
alternatives: use the offline demo on the page, or run the full stack locally per
the README. The guidance appears at the moment it is relevant, in plain language,
without technical jargon such as HTTP status codes.

**Why this priority**: Once the dead end is removed, the next failure mode is a
visitor not understanding why the hosted experience differs from the real product
and not knowing how to proceed.

**Independent Test**: On the static page, verify guidance toward the offline demo
and local setup is visible when a session starts, and that no raw HTTP status
codes appear in visitor-facing text.

**Acceptance Scenarios**:

1. **Given** the page is served without an API backend, **When** a session starts, **Then** the visitor sees plain-language guidance offering the offline demo and a pointer to the README for running the full stack locally.
2. **Given** the offline demo is running, **When** the visitor reviews any status or hint text, **Then** no raw HTTP status codes (e.g., "405 Method Not Allowed") are shown as the primary explanation.
3. **Given** the visitor reads the guidance, **When** they follow the local-setup pointer, **Then** the README contains run-full-stack instructions that match the guidance shown on the page.

---

### User Story 3 - Keep the real backend path intact (Priority: P3)

A developer or evaluator running the full stack locally (backend + frontend) must
see no behavioral change: sessions talk to the real API, real server-side errors
are surfaced as-is, and the offline fallback is never triggered or advertised.

**Why this priority**: The fallback must not mask genuine backend failures for
users who do have a backend — masking real errors would hide bugs.

**Independent Test**: Run the page against a local backend, start a session, and
verify the real API is used, server-provided error messages are shown verbatim,
and no offline-demo affordance appears.

**Acceptance Scenarios**:

1. **Given** the page is configured with a reachable backend, **When** the visitor clicks **Start session**, **Then** the conversation runs against the real API and no offline-mode indicator appears.
2. **Given** the backend returns a genuine application error (e.g., a validation or authorization failure), **When** the error is displayed, **Then** the server's message is shown and the offline demo is not offered as an alternative.
3. **Given** the backend is temporarily unreachable while configured, **When** the request fails, **Then** the visitor is told the backend could not be reached and is given the option to continue with the offline demo.

---

### Edge Cases

- What happens when the static host returns a non-JSON error body for the rejected request? The visitor must still receive the friendly offline-fallback experience, not a parsing failure.
- What happens when the backend is configured but returns a real error (4xx/5xx with an application message)? The real message must be shown; the offline fallback must not mask it.
- What happens when the network is offline entirely (request never leaves the browser)? The page must fall back to the offline demo rather than showing a raw connection error.
- What happens if the visitor clicks **Start session** repeatedly while a session is already starting? Only one session may start; no error spam.
- What happens if the offline demo indicator is missed? The first assistant message and any status area must still make the offline nature discoverable without scrolling on common viewports.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When the page is served without a reachable API backend, starting a session MUST begin an in-browser offline demo conversation instead of displaying a rejected-request error.
- **FR-002**: The system MUST clearly indicate, in plain language, whenever a conversation is running in offline demo mode, and that indicator MUST be visible while the conversation is in progress.
- **FR-003**: Visitor-facing messages MUST NOT present raw HTTP status codes (such as "405 Method Not Allowed") as the primary explanation; explanations MUST be written in plain language for non-technical visitors.
- **FR-004**: When running offline, the demo MUST guide the visitor through the full scripted support scenario — greeting, identity verification, and department routing — without any backend.
- **FR-005**: When a backend IS reachable, the system MUST use it exclusively and MUST NOT activate or advertise the offline demo.
- **FR-006**: When a reachable backend returns a genuine application error, the system MUST display that error's message and MUST NOT substitute the offline fallback.
- **FR-007**: When the backend is configured but unreachable, the system MUST tell the visitor the backend could not be reached and MUST offer the offline demo as a continuation option.
- **FR-008**: The page MUST provide guidance, at the moment the offline mode engages, pointing visitors to the offline demo and to the README instructions for running the full stack locally.
- **FR-009**: The offline session MUST support starting, conversing, and resetting without any network access.
- **FR-010**: Session state MUST NOT leak between offline mode and a later real-backend session within the same page load (resetting or starting fresh MUST clear prior turns).

### Key Entities

- **Demo Session**: A conversation instance; either backend-backed or offline; tracks mode (live/offline), conversation turns, and an explicit mode indicator visible to the visitor.
- **Mode Indicator**: Visitor-facing state communicating whether the current conversation is live (backend) or offline (in-browser demo).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of session starts on a backend-less deployment result in a usable conversation; 0 rejected-request error banners are shown to visitors.
- **SC-002**: A visitor on the static page can complete the full guided scenario (greeting → identity verification → department routing) in under 3 minutes with no setup steps.
- **SC-003**: 0 visitor-facing messages display raw HTTP status codes as their primary explanation.
- **SC-004**: Every offline conversation shows a visible offline-mode indicator throughout the session (verified across all offline session states).
- **SC-005**: On a live (backend-connected) deployment, 0 sessions activate offline mode, and 100% of genuine backend error messages are surfaced verbatim.
- **SC-006**: The offline demo works with zero network connectivity (requests blocked at the browser) for start, conversation, and reset flows.

## Assumptions

- The guided offline scenario mirrors the existing deterministic demo script (seed patients, identity matching, secret question, premium/regular routing); this feature changes how the mode is entered and communicated, not the scenario content.
- The existing README already documents running the full stack locally; guidance on the page only needs to point there, not duplicate it.
- "Without an API backend" means requests fail at the network/hosting layer (rejected method, missing route, or no connection) — not application-level errors returned by a real backend.
- Visitors are non-technical and are on the public hosted page; raw status codes are considered implementation detail, not user value.
- Accessibility requirements (keyboard operability, announced status, contrast) apply to the offline indicator and guidance, consistent with the project's existing accessibility standards.
- Mobile and desktop viewports are both in scope for the indicator and guidance visibility.
