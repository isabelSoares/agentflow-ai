# Implementation Plan: Demo Session Recovery & Rounded Highlighted Topbar

**Branch**: `002-fix-demo-session-topbar` | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-fix-demo-session-topbar/spec.md`

## Summary

The demo currently calls `/conversations` on the frontend origin while the documented API surface is exposed under `/api` (dev proxy and production reverse proxy). The request therefore hits the static frontend host and returns 404, leaving the page stuck on "Start a session to begin". The fix makes `/api` the default request base for the browser client, preserves the direct-origin override, and adds an actionable failure state with retry. The topbar is restyled as a floating sticky surface with side margins, rounded corners, and an accent highlight. Verification uses new frontend component tests, Python contract tests for the routing/configuration and CSS contract, and the existing build/typecheck/quality gates.

## Technical Context

**Language/Version**: Python 3.12+ (project runtime 3.13), TypeScript 7 with React 19, Node.js 22.12+

**Primary Dependencies**: FastAPI, LangGraph, Pydantic (backend); React 19, Vite 8 (frontend); Vitest, jsdom, Testing Library (new frontend dev dependencies for component tests)

**Storage**: In-memory session access store and conversation history; no persistence change

**Testing**: pytest + FastAPI TestClient for API contracts; Vitest + Testing Library + jsdom for frontend session-state tests; existing `tsc -b` and `vite build`; new Python CSS/config contract test

**Target Platform**: Modern web browsers (desktop and mobile widths from 320px) with the FastAPI service on Linux

**Project Type**: Web application (React frontend + FastAPI backend)

**Performance Goals**: A usable session is created within 2 seconds of page load (SC-001); failures surface an actionable message within 2 seconds (SC-003)

**Constraints**: No change to session, proof, guardrail, or telemetry behavior; offline test suite; Python coverage gate remains at 80%; topbar must stay sticky without causing horizontal scrolling

**Scale/Scope**: One demo page, three session endpoints, one shared header presentation, one browser API client

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Security First — PASS**: No authentication, authorization, session-proof, or data-disclosure behavior changes. The fix only changes the URL prefix used by the browser client and the visual shell.
- **II. Deterministic Verification — PASS**: Identity matching, secret verification, classification, and routing are untouched. No LLM decisions are added.
- **III. Separation of Concerns — PASS**: Request-base configuration stays in the frontend API client; session orchestration stays in the backend; presentation stays in CSS. No layer crossing is introduced.
- **IV. Testability — PASS**: Each acceptance scenario maps to a frontend component test, an API contract test, or a CSS/config contract test. All run offline. The new frontend test runner is required to satisfy this principle for UI state.
- **V. Type Safety — PASS**: The browser client remains strict TypeScript; any new Python test helpers use type hints. The existing Pydantic response contract is unchanged.
- **VI. Observability — PASS**: Existing server-side logging is unchanged. Client failures remain visible in the UI and continue to carry the underlying HTTP status in the error object.
- **VII. Simplicity — PASS**: The smallest viable fix is a default base path plus CSS. Vitest is added only because the constitution requires automated acceptance coverage and the repository currently has no frontend test runner.

**Post-Design Re-evaluation**: PASS. The design adds no backend endpoints, no new runtime dependencies, and no new architectural layers. The only new tooling is an offline frontend test runner.

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-demo-session-topbar/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── session-api.md   # Session request routing and response contract
│   └── ui-contract.md   # Demo states and topbar presentation contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

```text
src/healthcare_support/            FastAPI service and workflow (no business-logic changes)
├── api/
│   ├── app.py                  CORS and application wiring
│   ├── routes.py               Existing /conversations endpoints
│   └── schemas.py              Existing typed request/response models
└── ...

frontend/
├── src/
│   ├── api.ts                  Default request base and error mapping
│   ├── App.tsx                 Auto-start, retry, and session state
│   ├── components/ChatPanel.tsx
│   ├── styles.css              Floating rounded highlighted topbar
│   └── __tests__/              New Vitest component tests
├── vite.config.ts              Dev and preview /api proxy alignment
├── package.json                Add test script and test dev dependencies
└── .env.example                Clarify /api default and direct-origin override

tests/
├── contract/
│   └── test_frontend_demo_contract.py   New routing/config/CSS contract test
└── ...

README.md                       Deployment routing and troubleshooting note
```

**Structure Decision**: The repository is a two-part web application. Backend routes and workflow stay in `src/healthcare_support`; the defect is in `frontend/src/api.ts` and the visual work is in `frontend/src/styles.css`. Tests follow the existing `tests/contract` layout for cross-cutting configuration contracts, with component tests colocated under `frontend/src/__tests__`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | — | — |
