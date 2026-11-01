# Phase 0 Research: Demo Session Recovery & Rounded Highlighted Topbar

**Feature**: `002-fix-demo-session-topbar`
**Date**: 2026-11-01

## Research Tasks

The Technical Context contained no `NEEDS CLARIFICATION` markers. Research focused on the root cause of the 404, the safest routing correction, frontend acceptance testing, and the topbar presentation approach.

---

## 1. Root Cause of the Session 404

**Decision**: Treat the browser client's empty default request base as the root cause. Change the default base to `/api` and keep `VITE_API_BASE_URL` as an explicit override for direct-origin deployments.

**Rationale**:
- `frontend/src/api.ts` builds requests from `(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')`. With no environment variable, it requests `/conversations` on the frontend origin.
- `frontend/vite.config.ts` proxies only `/api` to `http://127.0.0.1:8000` and strips the prefix. The backend routes are therefore reachable at `/api/conversations` through the dev server, not `/conversations`.
- The README's production guidance says to route `/api` to the backend. The same mismatch breaks the static build.
- The 404 is a frontend-host response, not a backend route error, which explains why the page never obtains a session.

**Alternatives considered**:
- Add `/conversations` to the Vite proxy: rejected because the documented production contract already uses `/api`, so it would fix only local development.
- Hardcode `http://localhost:8000` as the default: rejected because it breaks same-origin production deployments and introduces CORS dependence.
- Add a runtime discovery endpoint: rejected as unnecessary complexity for a demo with one documented deployment convention (Principle VII).

---

## 2. Session Failure and Retry Behavior

**Decision**: Keep the existing automatic start on page load, preserve the manual "Start session" action for failures, and map failures to an actionable message while retaining the HTTP status internally.

**Rationale**:
- The current `ApiError` already carries the status and a readable message. The UI already renders `error` in an alert banner and re-enables the start action when no session exists.
- A 404 should no longer occur once routing is correct. If it does recur, the message must point to the service or routing problem rather than exposing a bare status code.
- Retaining the status in `ApiError` keeps diagnostics available without exposing technical details to the visitor.

**Alternatives considered**:
- Automatic infinite retries: rejected because it hides deployment errors and can duplicate sessions.
- Silent fallback to a fake local session: rejected because it would misrepresent backend behavior and could mask security-relevant failures.
- Removing automatic start in favor of a manual button: rejected because the spec requires automatic start and the current UX already intends it.

---

## 3. Frontend Acceptance Testing

**Decision**: Add Vitest with jsdom and Testing Library as frontend dev dependencies, plus a `test` script. Cover automatic session start, manual retry, send-message behavior, and failure messaging.

**Rationale**:
- Constitution Principle IV requires every acceptance scenario to map to an automated test.
- The repository has no frontend test runner today, so UI acceptance scenarios cannot be proven by pytest alone.
- Vitest integrates directly with the existing Vite configuration and runs offline.
- Testing Library asserts user-visible behavior rather than implementation details, which suits the spec's user-outcome language.

**Alternatives considered**:
- Playwright end-to-end tests: rejected as heavier (browser download, CI runtime, server orchestration) than needed for a single-page demo.
- Python string assertions against `App.tsx`: rejected because they would not exercise state transitions or user-visible output.
- No frontend tests: rejected because it violates Principle IV.

---

## 4. Routing and Configuration Contract Test

**Decision**: Add `tests/contract/test_frontend_demo_contract.py` to assert the browser default base, the dev/preview proxy prefix, and the presence of the topbar presentation declarations.

**Rationale**:
- The 404 was a configuration mismatch between two files. A cross-file contract test prevents the two configurations from drifting again.
- The repository already uses Python contract tests for cross-cutting repository configuration (`test_ci_quality.py`, `test_container_runtime.py`).
- CSS visual intent can be guarded by asserting the required declarations exist, while manual review covers actual rendering.

**Alternatives considered**:
- Snapshot tests of the built bundle: rejected because hashed assets and minification make snapshots brittle.
- Visual regression tooling: rejected as disproportionate for this feature.

---

## 5. Topbar Presentation

**Decision**: Style the existing `.site-header` as a floating sticky surface inside `.app-shell`: keep sticky positioning with a small top offset, add a top margin, horizontal padding, rounded corners, an accent-tinted border, and a layered shadow/glow. Adjust the same properties in the mobile media query.

**Rationale**:
- `.app-shell` already provides 28px desktop and 16px mobile horizontal padding, satisfying the side-margin requirement without new layout wrappers.
- Using existing tokens (`--accent`, `--radius-lg`, `--shadow`, `--border`) keeps the change consistent with the design language.
- Keeping the header in place preserves sticky behavior, navigation structure, and accessibility.
- A border plus shadow/glow provides the requested highlight without reducing text contrast.

**Alternatives considered**:
- Full-bleed topbar with only bottom rounding: rejected because the spec requires visible left and right margins.
- New topbar component: rejected because the existing semantic `<header>` already provides the structure.
- Solid accent background: rejected because it would reduce contrast and depart from the dark visual language.

---

## 6. Local Production-Build Verification

**Decision**: Mirror the `/api` proxy in Vite's `preview` configuration so the built client can be validated locally against the backend with the same request base used in production.

**Rationale**:
- The built app defaults to `/api`; `vite preview` without a proxy would reproduce the original 404 in local verification.
- Mirroring the dev proxy keeps verification representative and requires no extra server tooling.
- Production reverse proxies remain responsible for `/api` routing, as already documented.

**Alternatives considered**:
- Build with `VITE_API_BASE_URL=http://localhost:8000`: rejected for the primary check because it bypasses the `/api` contract that caused the bug; it remains a supported override.
- Add a Node proxy server for verification: rejected as unnecessary tooling.
