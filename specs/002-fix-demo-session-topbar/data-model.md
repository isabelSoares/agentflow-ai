# Phase 1 Data Model: Demo Session Recovery & Rounded Highlighted Topbar

**Feature**: `002-fix-demo-session-topbar`
**Date**: 2026-11-01

## Scope

This feature introduces no persistent storage changes and no new backend data entities. It changes how the browser client addresses the existing session API and how the existing header is presented. The entities below describe the client state that drives the acceptance scenarios and the presentation contract for the topbar.

---

## Session

**Represents**: A demo conversation created by the browser client and reused for every message until reset.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `id` | string (conversation identifier) | Backend `POST /api/conversations` response | Identifies the conversation across turns. |
| `proof` | string or null | `X-Session-Proof` response header | Ownership proof required on session-scoped requests. |
| `status` | `idle` \| `starting` \| `active` \| `error` | Client state | Controls composer availability, starting label, and retry affordance. |
| `messages` | ordered list of chat messages | Client state | Rendered conversation, beginning with the assistant greeting. |
| `telemetry` | telemetry snapshot | Backend turn response | Sanitized workflow state shown in the telemetry panel. |

**Relationships**:
- One demo page has zero or one active `Session`.
- One `Session` owns many chat messages.
- A `Session` is replaced when reset or restarted.

**Validation rules**:
- A session is `active` only after the create request succeeds and a conversation identifier is available.
- Session-scoped requests MUST include the current proof when one was issued.
- The composer MUST be disabled unless `status === active`.
- Duplicate session creation MUST be prevented while `status === starting`.
- Retry MUST be available when `status === error` and no active session exists.

**State transitions**:

```text
idle ──page load / Start session──▶ starting
starting ──success──▶ active
starting ──failure──▶ error
error ──Start session──▶ starting
active ──Reset session──▶ active (new proof, cleared telemetry)
active ──send message──▶ active (messages and telemetry updated)
```

---

## Chat Message

**Represents**: A single rendered message in the demo conversation.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Client-generated unique identifier for rendering. |
| `role` | `assistant` \| `user` \| `system` | Message author. |
| `text` | string | Rendered message content. |

**Validation rules**:
- The initial assistant greeting MUST be present when a session becomes active.
- A user message MUST be appended only after the visitor submits non-empty text.
- An assistant message MUST be appended only after a successful turn response.

---

## ApiError

**Represents**: A failed browser request with enough context to show an actionable message.

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Visitor-facing explanation. |
| `status` | number | HTTP status, or `0` when the service is unreachable. |

**Validation rules**:
- Network failure MUST use status `0` and a connectivity-oriented message.
- A non-success HTTP response MUST preserve the server-provided detail when it is a string.
- The error MUST NOT expose session proofs, patient data, or stack traces.

---

## Topbar

**Represents**: The persistent navigation surface containing the brand and primary navigation.

| Property | Requirement | Source |
|----------|-------------|--------|
| Horizontal margin | At least 16px desktop, at least 12px mobile | SC-004 |
| Corner radius | Visible rounding on all four corners | FR-009, SC-004 |
| Highlight | Accent-tinted border and/or shadow that separates it from the background | FR-010 |
| Stickiness | Remains visible while scrolling with a small top offset | FR-012 |
| Overlap | Does not obscure interactive page content | FR-012 |
| Responsiveness | No horizontal scrolling from 320px upward | FR-011, SC-005 |
| Accessibility | Navigation text and focus rings remain clearly visible | FR-013, SC-006 |

**Relationships**:
- The topbar is rendered once per page and contains the brand link and primary navigation links.
- The topbar's side margins are provided by the surrounding page shell; the topbar itself adds padding, rounding, border, and shadow.

**Validation rules**:
- The topbar MUST NOT use a solid accent fill that reduces text contrast.
- The topbar MUST retain its sticky behavior and z-index above page content.
- Mobile styles MUST preserve rounding and side spacing while stacking the brand and navigation.
