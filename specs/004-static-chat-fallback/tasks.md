---
description: "Task list for Automatic Static-Site Demo Fallback"
---

# Tasks: Automatic Static-Site Demo Fallback

**Input**: Design documents from `/specs/004-static-chat-fallback/`

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: Required by the project constitution (Principle IV: every acceptance scenario maps to an automated test). Test tasks are included per user story and must fail before the related implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`, `US4`)
- Include exact file paths in descriptions

## Path Conventions

Web application layout: frontend code in `frontend/src/`, frontend tests in `frontend/src/__tests__/`, backend unchanged in `src/healthcare_support/` and `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a green baseline. No new dependencies are required.

- [X] T001 Confirm the current frontend baseline passes by running `cd frontend && npm test && npm run build`; record any pre-existing failures before changing code (no file changes).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared types and availability helpers required by every user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add shared demo types in `frontend/src/types.ts`: `DemoSource = 'none' | 'live' | 'offline'`, `BackendAvailability = 'available' | 'unavailable' | 'error'`, and a `ScenarioStep` type with `order: number`, `instruction: string`, and `example: string | null`.
- [X] T003 [P] Add a bounded startup timeout and startup-outcome helper in `frontend/src/api.ts`: classify no response, `404`, `405`, `501`, gateway-unavailable `502`/`503`/`504`, and timeout as `unavailable`; classify other HTTP failures (for example `403`, `500`) as `error`; successful creation as `available`; use a `6000ms` default timeout and treat an aborted request as status `0`.

**Checkpoint**: Shared types and availability classification ready.

---

## Phase 3: User Story 1 - Demo works out of the box on the public static site (Priority: P1) 🎯 MVP

**Goal**: On a static host with no API backend, the page automatically starts the deterministic in-browser demo, enables the composer, and shows a non-blocking notice instead of a 405 error banner.

**Independent Test**: Load the built page with no backend reachable and confirm an interactive session starts automatically, the composer is enabled, the offline notice is announced, no raw status code is shown as a failure, and the full sample scenario reaches a routed outcome.

### Tests for User Story 1 ⚠️

> Write these tests FIRST and confirm they fail before implementation.

- [X] T004 [P] [US1] Update `frontend/src/__tests__/App.offline.test.tsx`: a mocked `405` MUST auto-start the offline demo, MUST NOT render a blocking `role="alert"`, MUST show a `role="status"` offline notice, MUST NOT show raw `405`/`404` text as a failure, and MUST let the visitor complete identify → secret answer → billing route with an enabled composer.
- [X] T005 [P] [US1] Add `frontend/src/__tests__/apiTimeout.test.ts`: a startup request that never resolves within the timeout is classified `unavailable` and triggers the offline demo; successful creation is classified `available`.

### Implementation for User Story 1

- [X] T006 [US1] Implement automatic fallback in `frontend/src/App.tsx`: when the startup outcome is `unavailable`, start the offline demo immediately (`createOfflineSession` + `offlineGreeting`), set the source to `offline`, clear any error, and ensure at most one startup attempt is in flight (duplicate session creation MUST be prevented while starting).
- [X] T007 [US1] Replace the blocking error presentation in `frontend/src/components/ChatPanel.tsx` with a non-blocking offline notice rendered only when the source is `offline`; the notice MUST state that the demo runs in the browser without an API backend, MUST use `role="status"`, and MUST NOT include a raw HTTP status code as the primary message.
- [X] T008 [P] [US1] Add styles for the offline notice and composer/status states in `frontend/src/styles.css`; status MUST NOT rely on color alone.
- [X] T009 [US1] Wire the source state and callbacks through `frontend/src/App.tsx` to `frontend/src/components/ChatPanel.tsx`, remove the obsolete `offlineAvailable` / `onStartOffline` second-click flow, and enable the message input and send action whenever a session is active (`live` or `offline`).

**Checkpoint**: User Story 1 is fully functional on a static host and testable independently.

---

## Phase 4: User Story 2 - Visitors understand the project and how to interact (Priority: P2)

**Goal**: A first-time visitor sees a concise project explanation and an inline suggested scenario, including the fictional security answer, and can complete the demo using only on-page guidance.

**Independent Test**: Open the demo and confirm the project summary, ordered scenario steps, sample identity, sample secret answer, and sample support request are visible in both live and offline modes, and the scenario can be completed from that text alone.

### Tests for User Story 2 ⚠️

- [X] T010 [P] [US2] Add `frontend/src/__tests__/App.guidance.test.tsx`: the project summary and ordered scenario steps are rendered; the sample identity (`Lisa`, `+14155552671`, `1990-01-15`), sample secret answer (`Yoda`), and a billing request are discoverable; guidance appears in both live and offline modes and is not dismissible.

### Implementation for User Story 2

- [X] T011 [P] [US2] Create `frontend/src/demoGuidance.ts` with the project summary, three ordered `ScenarioStep` entries, and only fictional sample values (`Lisa`, `+14155552671`, `1990-01-15`, `Yoda`, a billing request); no real personal data, credentials, or secret answers.
- [X] T012 [US2] Create `frontend/src/components/DemoGuide.tsx` and render it in `frontend/src/components/ChatPanel.tsx`: show the summary, ordered steps with associated example values, a note that the sample record is fictional, and a note that the same steps run against the live API when a backend is connected.
- [X] T013 [US2] Add guidance styles in `frontend/src/styles.css` (depends on T008 because both edit the same file); preserve heading hierarchy and document-order readability.

**Checkpoint**: User Story 2 works independently and remains available in both demo sources.

---

## Phase 5: User Story 3 - Live backend is preferred when available (Priority: P2)

**Goal**: When a backend is reachable, the page uses it and never shows the offline notice. After using the offline demo, the visitor can retry the live service without reloading the page.

**Independent Test**: Run the page against a reachable backend and confirm a live session starts with no offline notice. Then start offline with no backend, start the backend, select "Try live service", and confirm a clean live session replaces the offline conversation.

### Tests for User Story 3 ⚠️

- [X] T014 [P] [US3] Add `frontend/src/__tests__/App.livePreference.test.tsx`: a successful live start shows no offline notice; an offline session followed by a successful "Try live service" switches to `live` and clears prior messages; an unavailable retry stays offline without an error; a genuine error during retry shows an actionable error and keeps the offline demo usable.

### Implementation for User Story 3

- [X] T015 [US3] Add a `retryLive` flow in `frontend/src/App.tsx`: attempt a live session; on `available` switch the source to `live`, clear the offline notice, and start a fresh live conversation; on `unavailable` remain offline with no error; on `error` show the actionable message and remain offline. Switching sources MUST clear previous messages so the conversation is coherent.
- [X] T016 [US3] Add a "Try live service" action in `frontend/src/components/ChatPanel.tsx`, visible only when the source is `offline`, disabled while busy, and reachable by keyboard.
- [X] T017 [US3] Ensure every live start path (initial load and retry) clears the offline source and notice in `frontend/src/App.tsx`, so a reachable backend never displays the offline notice.

**Checkpoint**: User Story 3 works independently; live remains the preferred source.

---

## Phase 6: User Story 4 - Genuine service errors are not hidden (Priority: P3)

**Goal**: A reachable service that rejects a request for a legitimate reason shows an actionable error and does not silently switch to the offline demo.

**Independent Test**: Simulate `403` and `500` startup responses and confirm no offline demo starts, no offline notice appears, an accessible actionable error is shown, and the visitor can retry.

### Tests for User Story 4 ⚠️

- [X] T018 [P] [US4] Add `frontend/src/__tests__/App.errors.test.tsx`: startup with `403` and with `500` MUST NOT start the offline demo or show the offline notice, MUST show a readable actionable message in a `role="alert"`, MUST keep the composer disabled, and MUST offer a retry.

### Implementation for User Story 4

- [X] T019 [US4] Enforce the classification boundary in `frontend/src/App.tsx` and `frontend/src/api.ts`: only `unavailable` outcomes start the offline demo; `error` outcomes render `toMessage(caught)` and keep the source `none` (offline demo MUST NOT start for a genuine service error).
- [X] T020 [US4] Keep the error banner accessible and retryable in `frontend/src/components/ChatPanel.tsx`: retain `role="alert"` for genuine errors, show the "Start session" retry when no session exists, and ensure the offline notice is absent during genuine errors.

**Checkpoint**: All four user stories are independently functional; genuine errors remain visible.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, accessibility verification, and full validation.

- [X] T021 [P] Update `README.md` live-demo and troubleshooting sections: describe the automatic in-browser fallback, the guided scenario, the "Try live service" retry, and remove references to requiring a manual "Run offline demo" click.
- [X] T022 [P] Accessibility review of the offline notice, guidance, and retry action: confirm `role="status"` announcements, keyboard operability, heading hierarchy, and that status is not conveyed by color alone.
- [X] T023 Run the static/no-backend validation in `specs/004-static-chat-fallback/quickstart.md` (sections 1 and 2) and record the observed outcome.
- [X] T024 Run the live, retry, and genuine-error validations in `specs/004-static-chat-fallback/quickstart.md` (sections 3 through 5) and record the observed outcome.
- [X] T025 Run the full automated gate: `cd frontend && npm test && npm run build`, then `uv run pytest -m "not live_llm and not live_speech" --cov=src/healthcare_support --cov-branch --cov-report=term-missing --cov-fail-under=80`, `uv run mypy src`, `uv run ruff check src tests`, and `uv run ruff format --check src tests`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; complete first.
- **Foundational (Phase 2)**: Depends on Setup; BLOCKS all user stories.
- **User Stories (Phases 3–6)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories and is the MVP.
  - US2 (P2) is independent of US1 but polishes the same demo area.
  - US3 (P2) builds on US1's source state (offline → live retry).
  - US4 (P3) builds on US1's classification logic.
- **Polish (Phase 7)**: Depends on all desired user stories.

### User Story Dependencies

- **US1 (P1)**: After Foundational — no other story dependencies.
- **US2 (P2)**: After Foundational — independently testable; integrates visually with US1.
- **US3 (P2)**: After US1 — requires the `DemoSource` state introduced for fallback.
- **US4 (P3)**: After US1 — requires the availability classification introduced for fallback.

### Within Each User Story

- Tests MUST be written and fail before implementation.
- Shared types before components.
- `App.tsx` state and callbacks before `ChatPanel.tsx` prop wiring.
- Core behavior before styling and documentation.
- Complete one story and validate before moving to the next priority.

### Parallel Opportunities

- T003 can run alongside T002 only if it does not touch `types.ts` (it touches `api.ts`), so both are parallelizable.
- T004 and T005 (different test files) can run in parallel.
- T008 (`styles.css`) can run in parallel with T006/T007 (different files).
- T010 and T011 can run in parallel.
- T014 and T015/T016 are sequential within US3, but tests can be written before implementation.
- T018 can run in parallel with US1–US3 test authoring (different file).
- T021 and T022 can run in parallel.
- T023 and T024 are sequential manual validations after implementation; T025 runs last.

---

## Parallel Example: User Story 1

```bash
# Author the two US1 tests together (different files):
Task: "Update frontend/src/__tests__/App.offline.test.tsx for auto-start fallback"
Task: "Add frontend/src/__tests__/apiTimeout.test.ts for timeout classification"

# Style in parallel with behavior work (different files):
Task: "Add offline notice styles in frontend/src/styles.css"
Task: "Implement auto-fallback in frontend/src/App.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add frontend/src/__tests__/App.guidance.test.tsx"
Task: "Create frontend/src/demoGuidance.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (baseline).
2. Complete Phase 2 (shared types and availability classification).
3. Complete Phase 3 (US1: automatic static-site fallback).
4. **STOP and VALIDATE** with quickstart section 1 (no-backend static preview).
5. Deploy the frontend to make the public demo usable.

### Incremental Delivery

1. Setup + Foundational → classification ready.
2. US1 → static demo works automatically → deploy (MVP).
3. US2 → on-page explanation and guided scenario → deploy.
4. US3 → live preference and retry → deploy.
5. US4 → genuine errors stay visible → deploy.
6. Polish → docs and full validation gate.

### Notes

- `[P]` tasks touch different files and have no incomplete dependencies.
- Avoid editing `frontend/src/styles.css` in parallel tasks (T008 → T013 are sequential).
- The backend and `frontend/src/offlineDemo.ts` behavior are intentionally unchanged.
- The sample record is fictional; never substitute real patient data into guidance or tests.
