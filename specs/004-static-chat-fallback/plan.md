# Implementation Plan: Seamless Static-Site Chat Fallback

**Branch**: `fix/static-chat-fallback` | **Date**: 2026-11-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-static-chat-fallback/spec.md`

## Summary

Visitors on the statically hosted demo page currently hit a dead-end: clicking
**Start session** (or loading the page, which auto-starts) surfaces a rejected-request
error containing the raw `405 Method Not Allowed` text before the existing offline
demo can be reached via a secondary button. The plan makes the page fall back
**automatically and silently** into the in-browser offline demo when no API backend
is reachable, replaces raw status-code messaging with plain-language guidance that
points to the README for the full local stack, and guarantees that a reachable
backend keeps exclusive, unmasked use of the real API.

Technical approach: reuse the existing deterministic offline engine
(`frontend/src/offlineDemo.ts`) and the existing unreachable-status detection
(`isBackendUnreachable` in `frontend/src/api.ts`); change only the session-entry
flow, error messaging, and mid-conversation fallback affordance in the frontend
layer. No backend, schema, or contract changes.

## Technical Context

**Language/Version**: TypeScript 7 (strict) on React 19; Python backend untouched

**Primary Dependencies**: React 19, Vite 8, Vitest 5 + Testing Library, axe-core
(backend FastAPI/LangGraph not modified)

**Storage**: N/A — both modes are in-memory; no persistence changes

**Testing**: Vitest (`npm test` in `frontend/`), jsdom, Testing Library; existing
suites `App.offline.test.tsx`, `App.retry.test.tsx`, `App.session.test.tsx` are the
regression baseline; CI runs frontend tests separately from the Python suite

**Target Platform**: Modern browsers; GitHub Pages static host (GET/HEAD only) and
local Vite dev server proxying to FastAPI on :8000

**Project Type**: Web application (`frontend/` + `backend/`; this feature is
frontend-only)

**Performance Goals**: Offline fallback engages on the first failed start attempt
(no extra network probes); page remains interactive during mode transitions

**Constraints**: Constitution gates (below); no raw HTTP status codes in
visitor-facing primary messages; offline mode must never activate when a backend
is reachable and answering; accessibility (role=status/alert, keyboard) preserved

**Scale/Scope**: Single-page demo; ~3 source files (`App.tsx`, `api.ts`,
`ChatPanel.tsx`) + tests; no new dependencies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Notes |
|-----------|---------|-------|
| I. Security First | ✅ Pass | Offline demo uses seed patients only; no real PII, no new data paths; live-path errors still surface verbatim (no masking) |
| II. Deterministic Verification | ✅ Pass | Fallback decision is pure status-code logic (`isBackendUnreachable`), not LLM-dependent; offline engine already deterministic |
| III. Separation of Concerns | ✅ Pass | Changes confined to frontend presentation/session-entry layer; API client, offline engine, and backend remain independent |
| IV. Testability | ✅ Pass | Every acceptance scenario maps to a Vitest test (backend-less mock vs. reachable-backend mock); no live services needed |
| V. Type Safety | ✅ Pass | All changes in strict TypeScript; no untyped dictionaries crossing boundaries |
| VI. Observability | ✅ Pass | Mode transitions remain visible via existing status/alert regions; no secrets or PII involved |
| VII. Simplicity | ✅ Pass | Reuses existing offline engine and detection helper; no new abstractions, knobs, or dependencies (YAGNI) |

**No violations** — Complexity Tracking table not needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-static-chat-fallback/
├── plan.md              # This file
├── spec.md              # Feature specification
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.tsx                    # Session-entry flow: auto-fallback, mode state
│   ├── api.ts                     # Error classification + plain-language messages
│   ├── offlineDemo.ts             # Existing deterministic offline engine (reused)
│   ├── components/
│   │   └── ChatPanel.tsx          # Mode indicator, guidance copy, fallback CTA
│   └── __tests__/
│       ├── App.offline.test.tsx   # US1/US2: no dead-end error, guidance
│       ├── App.retry.test.tsx     # US3: real-backend errors unmasked
│       ├── App.session.test.tsx   # Live path regression
│       └── offlineDemo.test.ts    # Offline engine regression
└── package.json                   # npm test / npm run build

README.md                          # Local full-stack run instructions (pointer target)
```

**Structure Decision**: Web application layout (`frontend/` + `backend/`); this
feature touches only `frontend/src/`. The backend, `src/healthcare_support/`, and
its contract/integration tests are explicitly out of scope.

## Complexity Tracking

> No constitution violations — table intentionally empty.
