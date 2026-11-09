# Offline Fallback Contract

**Feature**: `004-static-chat-fallback`
**Date**: 2026-11-09

This contract defines the observable behavior of the demo when the page loads with and without an API backend. It complements the existing session API contract in `specs/002-fix-demo-session-topbar/contracts/session-api.md`; the backend routes and payloads are unchanged.

## Startup outcome classification

| Observed startup result | Classification | Visitor-visible behavior |
|-------------------------|----------------|--------------------------|
| Successful session creation | `available` | Live session starts; no offline notice |
| Network failure (no response) | `unavailable` | Offline demo starts automatically; offline notice shown |
| HTTP `404` | `unavailable` | Offline demo starts automatically; offline notice shown |
| HTTP `405` | `unavailable` | Offline demo starts automatically; offline notice shown |
| HTTP `501` | `unavailable` | Offline demo starts automatically; offline notice shown |
| HTTP `502`, `503`, `504` (gateway/upstream unavailable) | `unavailable` | Offline demo starts automatically; offline notice shown |
| Startup timeout | `unavailable` | Offline demo starts automatically; offline notice shown |
| Any other HTTP error (e.g. `403`, `500`) | `error` | Actionable error shown; offline demo NOT started |

Rules:
- Classification MUST consider only the startup request outcome.
- `unavailable` MUST NOT be presented to the visitor as a status-code failure.
- `error` MUST remain visible and MUST NOT be silently replaced by the offline demo.
- At most one startup attempt may be in flight at a time.

## Offline notice

When the source is `offline`, the page MUST show a non-blocking notice that:

1. States that the demo is running in the browser without an API backend.
2. Explains that the public page is a static build and the full API flows run locally.
3. Is announced politely to assistive technology (`role="status"` / live region).
4. Does not include a raw HTTP status code as the primary message.
5. Remains visible while the visitor interacts with the demo.

The notice MUST NOT be a blocking modal and MUST NOT require dismissal before the visitor can type.

## Composer and controls

| Condition | Message input | Send | Reset | Retry live |
|-----------|---------------|------|-------|------------|
| No session, starting | disabled | disabled | hidden | hidden |
| Live session active | enabled | enabled when text present | enabled | hidden |
| Offline session active | enabled | enabled when text present | enabled | enabled |
| Genuine error, no session | disabled | disabled | hidden | hidden; "Start session" enabled |

## Retry behavior

- While offline, a "Try live service" action MUST attempt a live session start.
- On success, the page switches to the live source, clears the offline notice, and starts a fresh live conversation.
- On `unavailable`, the page remains offline with the notice and does not show an error.
- On `error`, the page shows the actionable error and remains offline so the visitor can keep using the demo.
- Retrying MUST NOT duplicate messages; switching sources starts a clean conversation.

## Accessibility

- The offline notice, session start, and source switch MUST be announced through a polite status mechanism.
- All controls MUST be reachable and operable by keyboard.
- Status MUST NOT rely on color alone.

## Non-goals

- No change to backend routes, payloads, authentication, or proof handling.
- No persistence of conversations across reloads.
- No offline support for real patient data.
