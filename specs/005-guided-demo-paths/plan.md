# Implementation Plan: Guided Demo Paths

**Branch**: `005-guided-demo-paths` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Status**: Implemented

**Input**: Feature specification from `/specs/005-guided-demo-paths/spec.md`

## Summary

The in-browser demo currently accepts free-form typing and relies on heuristic parsing to decide identity, verification, and intent. That parser is the source of the "simulated real input does not work right" experience. This plan replaces free-form input in the offline demo with a small set of selectable **guided demo paths**. Each path is a named scenario with a fixed, non-editable sequence of pre-written visitor messages; a single "Next step" control sends the next message and the existing deterministic `offlineSend` engine produces the response and telemetry. Paths collectively demonstrate premium routing, regular routing, clarification (ambiguous identity), and failed verification/termination. The live backend experience keeps its editable free-text composer unchanged. No backend, API contract, or security logic changes.

## Technical Context

**Language/Version**: TypeScript (repository compiler), React 19.3, Vite 8.3.5, Node 22.12+/24; Python 3.13 backend unchanged

**Primary Dependencies**: React, Vite, Vitest, @testing-library/react, jsdom; no new runtime or development dependencies

**Storage**: No new persistence. Guided paths are static in-memory definitions; demo conversation state stays in memory; existing theme preference stays in browser localStorage

**Testing**: Vitest + Testing Library for the frontend; existing pytest backend suite must continue to pass unchanged

**Target Platform**: Modern evergreen browsers; GitHub Pages static hosting and local dev/preview servers

**Project Type**: Web application (React single-page frontend + FastAPI backend)

**Performance Goals**: Path selection and step advancement render within 100 ms; the guided demo is interactive within 2 seconds of page load on a static host

**Constraints**: Offline demo must require zero typing and be fully deterministic; no backend/API/security changes; only fictional sample data; keep the live free-text experience unchanged; no new dependencies or build-time configuration knobs

**Scale/Scope**: One public demo page; 4 guided paths of 1–5 steps each; changes confined to `frontend/src` (new path definitions and component, modified `App`, `ChatPanel`, `types`, `styles`) plus frontend tests and README/demo docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Security First | Guided paths must use fictional sample data only; no real PII, credentials, or secret answers exposed or logged | PASS — reuses existing fictional sample records; pre-written messages are demo data, not secrets to real systems |
| II. Deterministic Verification | Identity, verification, classification, and routing decisions must remain deterministic and LLM-independent | PASS — paths only supply inputs to the existing deterministic `offlineSend` engine; no LLM and no new decision logic |
| III. Separation of Concerns | Changes stay in the presentation/client layer; backend and engine boundaries untouched | PASS — frontend-only; `offlineDemo.ts` is reused as-is; no API changes |
| IV. Testability | Every acceptance scenario maps to automated tests; no external services required | PASS — path definitions are unit-testable; selection/advance/reset/live-unaffected behavior is covered by Vitest + Testing Library |
| V. Type Safety | New path and progress state must be explicitly typed | PASS — add `GuidedDemoPath`, `GuidedStep`, and path-progress types to the existing typed frontend |
| VI. Observability | State changes must be observable without logging PII or secrets | PASS — visible step progress, telemetry updates, and accessible status announcements; no new sensitive logging |
| VII. Simplicity | Prefer the smallest maintainable solution; no unneeded abstractions or knobs | PASS — static data plus one progress counter on top of the existing engine; no new dependency, router, or config flag |

**Post-Phase 1 re-check**: no new violations. The design reuses the existing deterministic engine, adds static typed path data, and keeps all changes in the frontend.

## Project Structure

### Documentation (this feature)

```text
specs/005-guided-demo-paths/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── guided-path-data.md
│   └── guided-mode-ui.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.tsx                       # Guided path state, selection/advance/reset, keep live free-text path
│   ├── offlineDemo.ts                # Existing deterministic engine (reused unchanged)
│   ├── guidedDemoPaths.ts            # NEW: typed guided path definitions (single source of truth)
│   ├── components/
│   │   ├── ChatPanel.tsx             # Render guided path UI in offline mode; live composer unchanged
│   │   ├── GuidedDemoPaths.tsx       # NEW: path picker, progress, next-step/restart controls
│   │   └── TelemetryPanel.tsx        # No behavior change
│   ├── types.ts                      # New guided path / progress types
│   ├── styles.css                    # Path picker, progress, and read-only message styling
│   └── __tests__/
│       ├── guidedDemoPaths.test.ts   # NEW: path shape, step order, expected outcomes
│       ├── App.guidedPaths.test.tsx  # NEW: select, advance, switch, restart, zero typing
│       ├── App.session.test.tsx      # Live free-text composer remains available
│       ├── App.offline.test.tsx      # Offline fallback still starts; guided mode shown
│       └── offlineDemo.test.ts       # Existing engine coverage unchanged

README.md                             # Update demo description to the guided-path walkthrough
src/healthcare_support/               # Backend unchanged
tests/                                # Backend tests unchanged
```

**Structure Decision**: Web application layout. The repository already separates the FastAPI backend (`src/healthcare_support`, `tests/`) from the React frontend (`frontend/`). This feature is confined to `frontend/src` and frontend tests. The existing `offlineDemo.ts` engine remains the single deterministic brain; guided paths provide scripted inputs to it instead of a parser, and a new presentation component owns path selection and progression.

## Complexity Tracking

> No constitution violations. No complexity justification required.
