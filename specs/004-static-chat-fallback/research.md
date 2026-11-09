# Phase 0 Research: Automatic Static-Site Demo Fallback

**Feature**: `004-static-chat-fallback`
**Date**: 2026-11-09

## Research Questions

1. How should the page decide that no backend is available?
2. Should the fallback be selected at build time or runtime?
3. How should the page avoid waiting forever on a hanging API?
4. How should the offline notice differ from an error banner?
5. What guidance does a first-time visitor need to complete the demo?
6. How can a visitor return to the live service after using the offline demo?
7. Does the backend need to change?

---

## Decision 1: Classify "backend unavailable" from the startup request outcome

**Decision**: Reuse the existing `isBackendUnreachable(status)` classification (`0` network failure, `404`, `405`, `501`) to decide when to start the offline demo automatically. Treat `403`, `500`, and other application responses as genuine errors that do not trigger the fallback.

**Rationale**: A static host rejects `POST` with `405`; a wrong gateway route yields `404`/`501`; an offline device yields a network failure (`0`). These are exactly the conditions where no backend can serve the demo. Application-level errors mean a backend *is* present and failing, which the visitor must see.

**Alternatives considered**:
- *Fallback on any non-OK response*: rejected because it would hide authorization and server defects (violates spec FR-010).
- *Fallback only on `405`*: rejected because other static hosts and misrouted gateways return `404`/`501` or fail at the network layer.

---

## Decision 2: Detect availability at runtime, not with a build-time switch

**Decision**: On mount, attempt a normal live session. If the outcome is classified as "backend unavailable", automatically start the offline demo. Do not add a build-time environment flag.

**Rationale**: Runtime detection works on every static host without host-specific configuration and keeps the live path as the default when a backend exists. It satisfies FR-001, FR-009, and FR-013 with one code path. It also respects the constitution's simplicity principle by avoiding an extra configuration knob.

**Alternatives considered**:
- *Build-time `VITE_OFFLINE_DEMO` flag set in the Pages workflow*: rejected as an additional, host-specific knob; it still requires runtime fallback for other deployments, so it adds complexity without removing it.
- *Require a manual click on "Run offline demo"*: rejected because it is the current behavior the user reports as broken; visitors should not need to discover a hidden button.

---

## Decision 3: Bound the startup request with a timeout, then fall back

**Decision**: Give the initial session-start request a bounded timeout (target `6s`) using an abort signal. If the request times out, treat it as "backend unavailable" and start the offline demo, while leaving genuine error responses untouched.

**Rationale**: A hanging or black-holed backend must not leave the visitor on a disabled composer indefinitely. A short bound keeps the page responsive; the static-host path is immediate anyway, so the 2-second success criterion is met there.

**Alternatives considered**:
- *No timeout*: rejected because a stalled request leaves the demo unusable.
- *Very short timeout (≤1s)*: rejected because a slow-but-working backend could be incorrectly abandoned; the fallback is still available via retry.

---

## Decision 4: Replace the blocking error with a non-blocking, announced notice

**Decision**: When the offline demo starts automatically, do not show an error banner. Show a small informational notice announcing "Offline demo mode" using the existing polite status mechanism, plus a short explanation that the public page is static and the deterministic demo runs in the browser.

**Rationale**: The 405 is expected on a static host, not a visitor error. A blocking banner with a status code is what makes the page look broken. A polite status announcement also serves screen-reader users (FR-014).

**Alternatives considered**:
- *Modal dialog*: rejected because it interrupts the demo and adds dismissal friction.
- *Keep the error banner but add a button*: rejected because it preserves the reported bad experience and still requires an extra click.

---

## Decision 5: Provide an inline guided scenario, including the security answer

**Decision**: Add a compact "Try this scenario" block in the chat panel with ordered steps and the sample values: identify with Lisa plus the listed phone number or date of birth, answer the security question with the sample answer, then ask for billing help to see routing. Keep free-form chat available, and keep the existing suggestion chips.

**Rationale**: A newcomer cannot complete verification without knowing the fictional security answer; the current suggestions omit it. On-page guidance satisfies FR-007 and FR-008 without sending visitors to the README. Fictional values are safe to display (FR-006).

**Alternatives considered**:
- *Link to the README for details*: rejected because it breaks the "understand and interact on the page" goal.
- *Only expand suggestion chips*: rejected because the multi-step verification flow still needs an explanation of order and the secret answer.
- *Add a "Run sample scenario" automated playback button*: candidate enhancement, but not required; it adds state and could mask the agent interaction. Keep manual steps for the demo's educational value.

---

## Decision 6: Offer an explicit "Try live service" retry while offline

**Decision**: In offline mode, keep a visible retry action that attempts to start a live session again. If it fails as unavailable, remain in offline mode without showing an error. If it succeeds, switch to the live session and hide the offline notice.

**Rationale**: Satisfies US3 (prefer live when available) and the edge case where the backend recovers without a reload. It is a single explicit action, not background polling.

**Alternatives considered**:
- *Force a page reload*: rejected because it loses context and is less discoverable than a labelled action.
- *Poll the backend automatically*: rejected for simplicity and to avoid noisy requests.

---

## Decision 7: Do not change the backend or the offline engine behavior

**Decision**: Keep the FastAPI service and the deterministic in-browser engine (`frontend/src/offlineDemo.ts`) behavior as-is. The feature adds availability detection, state, presentation, and guidance around them.

**Rationale**: The reported defect is presentation/fallback, not workflow logic. The offline engine already mirrors the backend's seed patients, 2-of-3 matching, secret-answer check, classification, and routing, and is covered by tests. Changing it would risk regressing verified deterministic behavior (constitution principles I, II, IV).

**Alternatives considered**:
- *Add a public demo mode to the backend*: rejected because a static host cannot run Python at all.
- *Rewrite the offline engine*: rejected as unnecessary and higher risk.
