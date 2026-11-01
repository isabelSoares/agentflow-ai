# Demo UI Contract

**Feature**: `002-fix-demo-session-topbar`
**Date**: 2026-11-01

## Page States

| State | Composer | Primary control | Message area | Error banner |
|-------|----------|-----------------|--------------|--------------|
| Idle (before automatic start) | Disabled, placeholder "Start a session to begin" | "Start session" | Starter assistant message | Hidden |
| Starting | Disabled, starting label | "Starting..." disabled | Starter or previous message | Hidden |
| Active | Enabled, placeholder "Ask a support question..." | "Reset session" | Greeting plus conversation | Hidden |
| Error (no session) | Disabled, placeholder "Start a session to begin" | "Start session" enabled for retry | Starter assistant message | Visible and actionable |
| Error (active session) | Enabled | "Reset session" | Conversation preserved | Visible and actionable |

### State Rules

- On first load, the page MUST attempt to create a session automatically.
- Automatic start MUST run once per page load, not once per render.
- While starting, duplicate session creation MUST be prevented.
- On success, the composer MUST become enabled and the greeting MUST replace the starter message.
- On failure, the error banner MUST be visible, the session MUST remain absent, and retry MUST be possible.
- Sending a message MUST append the visitor message immediately and the assistant reply on success.
- A failed message send MUST preserve the conversation and show the error banner.
- Reset MUST clear telemetry and replace the conversation with a fresh greeting.

---

## Topbar Presentation Contract

The topbar is the existing semantic `<header>` containing the brand and primary navigation.

### Layout

- Visible space MUST remain on the left and right between the topbar and the viewport edge.
- Desktop: at least 16px on each side.
- Mobile (up to 700px): at least 12px on each side.
- The topbar MUST remain sticky while scrolling, offset slightly from the viewport top.
- The topbar MUST NOT cause horizontal scrolling at any width from 320px upward.

### Shape and Highlight

- All four corners MUST be rounded.
- The surface MUST be visually distinct from the page background using the existing dark design language.
- The highlight MUST use an accent-tinted border and/or layered shadow/glow.
- The highlight MUST NOT be a solid accent fill.
- The topbar MUST remain opaque enough for navigation text to stay readable over page content.

### Responsiveness

- Desktop: brand and navigation share one row.
- Mobile: brand and navigation stack vertically, navigation may scroll horizontally within its own row.
- Rounding, side spacing, and highlight MUST persist at both breakpoints.

### Accessibility

- Navigation links MUST retain readable contrast against the highlighted surface.
- Keyboard focus MUST remain clearly visible on brand and navigation links.
- The topbar MUST not trap focus or introduce new focusable elements.
- Sticky positioning MUST not obscure focused interactive content elsewhere on the page.

---

## Acceptance Mapping

| Requirement | Automated check | Manual check |
|-------------|-----------------|--------------|
| FR-001, FR-002, FR-006 | Frontend component tests for auto-start, retry, and starting state | Load page with backend running |
| FR-003, FR-004 | Routing/config contract test plus component test using the `/api` base | Dev and preview session creation |
| FR-005 | Frontend component test for error message and retry affordance | Stop backend and reload |
| FR-007 | Frontend component test that sends a message to the active session | Multi-turn conversation |
| FR-008–FR-013 | CSS contract test for margin, radius, border, shadow, sticky, and mobile override | Desktop/mobile visual and keyboard review |
| FR-014 | Contract test plus README content assertion | Follow quickstart from a clean checkout |
