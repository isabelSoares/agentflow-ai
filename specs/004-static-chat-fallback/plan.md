# Implementation Plan: Automatic Static-Site Demo Fallback

**Branch**: `004-static-chat-fallback` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-static-chat-fallback/spec.md`

## Summary

The public site is a static build with no API backend, so starting a session currently fails with a 405, shows a blocking error banner, disables the composer, and hides the working offline demo behind a second-click button. This plan makes the frontend detect an unavailable API at startup and automatically start the existing in-browser deterministic demo, replacing the error banner with a non-blocking offline notice, enabling the composer immediately, and adding on-page guidance plus a sample scenario. A reachable backend is still preferred, genuine service errors remain visible, and visitors can retry the live service from offline mode. No backend behavior or security semantics change.

## Technical Context

**Language/Version**: TypeScript (with the repository's installed compiler), React 19.3, Vite 8.3.5, Node 24; Python 3.13 backend unchanged

**Primary Dependencies**: React, Vite, Vitest, @testing-library/react, jsdom; existing FastAPI backend (no changes)

**Storage**: No new storage. Existing theme preference stays in browser localStorage; demo state stays in memory

**Testing**: Vitest + Testing Library for the frontend; existing pytest backend suite must continue to pass unchanged

**Target Platform**: Modern evergreen browsers; static hosting (GitHub Pages) and local dev/preview servers

**Project Type**: Web application (React single-page frontend + FastAPI backend)

**Performance Goals**: An interactive session within 2 seconds of page load on a static host; no indefinite wait when the API hangs (bounded startup timeout, target `6s`)

**Constraints**: No API backend on static hosts; in-browser demo is deterministic and fictional; no real patient data, credentials, or secret answers in client logs; no build-time configuration switch added (keep runtime detection only)

**Scale/Scope**: One public demo page, single visitor session at a time, three frontend components (`App`, `ChatPanel`, API helper) plus tests and docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Security First | Demo data must be fictional; no real PII, credentials, or secret answers exposed or logged; offline notice must not leak data | PASS — reuses existing fictional sample records; no PII added to logs |
| II. Deterministic Verification | Identity, verification, classification, and routing decisions must stay deterministic, never LLM-driven | PASS — in-browser demo engine is deterministic and mirrors backend logic; no LLM in fallback |
| III. Separation of Concerns | Changes stay in the presentation/client layer; backend modules untouched | PASS — frontend-only change; existing API contract unchanged |
| IV. Testability | Every acceptance scenario maps to automated tests; offline-capable | PASS — new/updated Vitest tests cover fallback, live preference, genuine errors, guidance, and accessibility |
| V. Type Safety | New client state must be explicitly typed | PASS — extend existing TypeScript types for demo source, availability, and guidance |
| VI. Observability | Failures logged with context but no PII/secrets | PASS — no new PII logging; availability decisions are client state, not sensitive logs |
| VII. Simplicity | Prefer the smallest maintainable solution; no unneeded config knobs | PASS — reuse the existing offline engine and one runtime detection rule; no build flag or new abstraction |

**Post-Phase 1 re-check**: no new violations; design keeps all changes in the frontend and reuses existing deterministic demo logic.

## Project Structure

### Documentation (this feature)

```text
specs/004-static-chat-fallback/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── offline-fallback.md
│   └── demo-guidance.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.tsx                       # Auto-fallback, offline notice, retry-live, guidance wiring
│   ├── api.ts                        # Backend-availability classification + bounded startup timeout
│   ├── offlineDemo.ts                # Existing deterministic in-browser engine (reused, unchanged behavior)
│   ├── components/
│   │   ├── ChatPanel.tsx             # Offline notice, guided scenario, enabled composer
│   │   └── TelemetryPanel.tsx        # No behavior change; may show source hint
│   ├── types.ts                      # New demo source/availability/guidance types
│   ├── styles.css                    # Notice and guidance styling
│   └── __tests__/
│       ├── App.offline.test.tsx      # Updated: auto-start offline, no raw 405, retry live
│       ├── App.session.test.tsx      # Live path still preferred
│       ├── offlineDemo.test.ts       # Existing deterministic engine coverage
│       └── App.guidance.test.tsx     # New: on-page guidance and sample scenario
├── .github/workflows/pages.yml       # No change required (runtime detection works on any static host)
└── README.md                         # Update live-demo/static-hosting behavior

src/healthcare_support/               # Backend unchanged
tests/                                # Backend tests unchanged
```

**Structure Decision**: Web application layout. The repository already separates the FastAPI backend (`src/healthcare_support`, `tests/`) from the React frontend (`frontend/`). This feature is confined to `frontend/src` and frontend tests plus README documentation. The existing `offlineDemo.ts` engine is reused as-is; the new work is detection, state management, presentation, and guidance.

## Complexity Tracking

> No constitution violations. No complexity justification required.
