---

description: "Task list for Guided Demo Paths"
---

# Tasks: Guided Demo Paths

**Input**: Design documents from `/specs/005-guided-demo-paths/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. The constitution requires automated tests for every acceptance scenario, and the plan/quickstart define Vitest coverage. Write tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Every task includes an exact file path

## Path Conventions

- Web app: `frontend/src/` for the React single-page app, `frontend/src/__tests__/` for Vitest tests
- Backend `src/healthcare_support/` and `tests/` are unchanged by this feature

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm a green baseline before changing the demo

- [X] T001 Run `npm ci`, `npm test`, and `npm run build` in `frontend/` and record any pre-existing failures per `frontend/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared types and path data that every user story consumes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Add `GuidedStep` and `GuidedDemoPath` types to `frontend/src/types.ts`, with `GuidedStep` fields `id`, `message`, optional `label` per `data-model.md`; progress is derived from `activePathId` and `pathStepIndex`
- [X] T003 [P] Create `frontend/src/guidedDemoPaths.ts` exporting `GUIDED_DEMO_PATHS` with the four paths from `contracts/guided-path-data.md` (premium, regular, clarification, failed verification) and a `findGuidedPath(id)` helper; ensure every `id` is unique, every path has at least one step, and prepared messages are fictional and sent verbatim

**Checkpoint**: Types and path definitions are ready; user stories can proceed.

---

## Phase 3: User Story 1 - Complete a guided demo path without typing (Priority: P1) 🎯 MVP

**Goal**: In offline mode the visitor selects a named path and advances through non-editable prepared messages with no typing.

**Independent Test**: On the static preview with no backend, select the premium path, advance every step, and confirm each prepared message is sent unchanged, replies render, and the composer is not required.

### Tests for User Story 1

- [X] T004 [P] [US1] Add `frontend/src/__tests__/App.guidedPaths.test.tsx` covering: offline mode shows named paths, no editable composer is required, selecting the premium path starts a clean conversation, "Next step" appends the prepared user message and agent reply, and restart resets messages and progress
- [X] T005 [P] [US1] Update `frontend/src/__tests__/App.offline.test.tsx` to assert guided paths appear automatically when the backend is unavailable and no raw HTTP status code is shown

### Implementation for User Story 1

- [X] T006 [US1] Create `frontend/src/components/GuidedDemoPaths.tsx` with a path picker (title and description per path), a selected-path view showing "Step N of M" and the read-only prepared message, and "Next step", "Restart", and "Choose another path" controls
- [X] T007 [US1] Add guided path state and handlers to `frontend/src/App.tsx`: `activePathId`, `pathStepIndex`, clean `OfflineSession` creation on select/restart/switch, verbatim step send through `offlineSend`, telemetry mapping, and a `busy` guard against duplicate advancement
- [X] T008 [US1] Update `frontend/src/components/ChatPanel.tsx` to render `GuidedDemoPaths` when `source === 'offline'` and hide or disable the editable composer, suggestions, and free-text hint in that mode
- [X] T009 [US1] Add path picker, selected-path, prepared-message, progress, and control styling to `frontend/src/styles.css`

**Checkpoint**: A single guided path is fully usable with zero typing. This is the MVP.

---

## Phase 4: User Story 2 - Paths cover the real workflow outcomes (Priority: P2)

**Goal**: Every path ends in a distinct, clearly explained outcome, and the set demonstrates premium/regular classification, routing, clarification, and guardrail termination.

**Independent Test**: Run all four paths and confirm each ends in its declared outcome, no path is a dead end, and telemetry matches the final turn.

### Tests for User Story 2

- [X] T010 [P] [US2] Add `frontend/src/__tests__/guidedDemoPaths.test.ts` asserting unique path/step ids, non-empty ordered steps, and that applying each path's messages through `offlineSend` yields the contract signals: premium authenticated/routed, regular to `Standard Patient Support`, clarification, and terminated
- [X] T011 [P] [US2] Extend `frontend/src/__tests__/App.guidedPaths.test.tsx` to complete all four paths and assert each distinct outcome plus the presence of restart/choose-another controls at completion

### Implementation for User Story 2

- [X] T012 [US2] Derive and display the completion outcome from the final `ConversationTurn` (classification, routing status, support department, terminated) in `frontend/src/components/GuidedDemoPaths.tsx`, and show each path's declared expected outcome before it starts
- [X] T013 [US2] Ensure path switching midway resets messages, telemetry, and step progress in `frontend/src/App.tsx`, and that completion disables further advancement

**Checkpoint**: All workflow branches are demonstrable and independently verified.

---

## Phase 5: User Story 3 - Live backend behavior is unchanged (Priority: P2)

**Goal**: Guided paths appear only in offline mode; a reachable backend keeps the editable free-text composer, and switching to live clears guided state.

**Independent Test**: Run against a reachable backend and confirm a live session starts with an editable composer and no guided paths; then stop the backend and confirm guided paths take over.

### Tests for User Story 3

- [X] T014 [P] [US3] Update `frontend/src/__tests__/App.session.test.tsx`, `frontend/src/__tests__/App.livePreference.test.tsx`, and `frontend/src/__tests__/App.errors.test.tsx` to assert live mode shows an editable composer with no guided-path picker; an unavailable retry stays offline; and genuine `403`/`500` errors do not start the guided demo

### Implementation for User Story 3

- [X] T015 [US3] Gate guided UI strictly on `source === 'offline'` in `frontend/src/components/ChatPanel.tsx` and `frontend/src/App.tsx`, leaving the live composer unchanged
- [X] T016 [US3] Clear `activePathId` and `pathStepIndex` when a live session succeeds via `applyLiveSession` or "Try live service" in `frontend/src/App.tsx`

**Checkpoint**: Live and offline experiences are correctly separated.

---

## Phase 6: User Story 4 - The demo is clear and accessible (Priority: P3)

**Goal**: Visitors understand the demo is scripted, and path selection, progression, restart, and switching work with keyboard and assistive technology.

**Independent Test**: Using only a keyboard and a screen reader, select a path, complete it, restart, and switch paths, confirming progress and outcomes are announced.

### Tests for User Story 4

- [X] T017 [P] [US4] Add guided-mode accessibility coverage to `frontend/src/__tests__/App.accessibility.test.tsx`: labelled path group, keyboard-operable path controls, and polite live-region announcements for step and outcome changes
- [X] T018 [P] [US4] Update `frontend/src/__tests__/App.guidance.test.tsx` to assert the scripted-walkthrough explanation is visible in offline mode

### Implementation for User Story 4

- [X] T019 [US4] Add the scripted-walkthrough note, accessible group/control labels, progress text, and polite live-region announcements in `frontend/src/components/GuidedDemoPaths.tsx`
- [X] T020 [US4] Add visible focus styles and non-color-only state styling for guided controls in `frontend/src/styles.css`

**Checkpoint**: The guided demo is understandable and operable without a mouse.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and full validation

- [X] T021 [P] Update `README.md` to describe the guided-path demo and remove instructions that imply typing free-form messages in offline mode
- [X] T022 [P] Reconcile `frontend/src/demoGuidance.ts` and `frontend/src/components/DemoGuide.tsx` so live-mode wording is accurate and no free-text typing copy is shown in offline guided mode
- [X] T023 Run `npm test` and `npm run build` in `frontend/` and the backend gates from `specs/005-guided-demo-paths/quickstart.md`
- [X] T024 Execute the scenarios in `specs/005-guided-demo-paths/quickstart.md` (static, offline, live, accessibility) and record the evidence and limitations in `specs/005-guided-demo-paths/validation.md`
- [X] T025 [P] Add a data-guard test to `frontend/src/__tests__/guidedDemoPaths.test.ts` proving path copy uses only the documented fictional identities and contains no credentials, email addresses, or raw HTTP status codes
- [X] T026 [P] Add timing coverage to `frontend/src/__tests__/App.guidedPaths.test.tsx` for the SC-004 reset/switch budget (<1 s) and the SC-002 path-completion budget (<2 min)
- [X] T027 [P] Sync `spec.md`, `plan.md`, `data-model.md`, and `tasks.md` with the analysis findings: FR-006 clarification, FR-012 actionable-error definition, Guided Step wording, derived progress state, and US3 test traceability

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on T001; blocks all user stories
- **User Stories (Phase 3+)**: Depend on Phase 2
  - US1 is the MVP and should be completed first
  - US2 builds on US1's UI and uses the shared path data
  - US3 and US4 can follow US1; they extend the same files, so run them sequentially
- **Polish (Phase 7)**: Depends on all targeted stories

### User Story Dependencies

- **US1 (P1)**: Requires T002, T003
- **US2 (P2)**: Requires US1 completion (UI/progression) plus T002, T003
- **US3 (P2)**: Requires US1 completion (offline UI) plus T002, T003
- **US4 (P3)**: Requires US1 completion (guided UI) plus T002, T003

### Within Each User Story

- Tests before implementation; confirm they fail first
- Types and path data before UI and state
- Component before App wiring where possible
- Complete and verify one story before the next

### Parallel Opportunities

- T002 and T003 can run in parallel (different files)
- T004 and T005 can run in parallel (different test files)
- T010 and T011 can run in parallel (different test files)
- T017 and T018 can run in parallel (different test files)
- T021 and T022 can run in parallel (different docs/files)
- T025, T026, and T027 can run in parallel (different test/docs files)
- Implementation tasks that share `App.tsx`, `ChatPanel.tsx`, `GuidedDemoPaths.tsx`, or `styles.css` must not run in parallel

---

## Parallel Example: User Story 1

```bash
# Write the two test files in parallel:
Task: "Add App.guidedPaths.test.tsx covering path selection, advancement, and restart"
Task: "Update App.offline.test.tsx for automatic guided paths and no raw status codes"
```

## Parallel Example: User Story 2

```bash
# Write the data-level and UI-level coverage tests in parallel:
Task: "Add guidedDemoPaths.test.ts asserting path coverage via offlineSend"
Task: "Extend App.guidedPaths.test.tsx for all four outcomes"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (types + path data)
3. Complete Phase 3: US1
4. STOP and validate: one guided path completes with zero typing on the static preview
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → validate a full guided path → demo (MVP)
3. US2 → validate all four outcomes → demo
4. US3 → validate live composer unchanged → demo
5. US4 → validate keyboard/screen-reader flow → demo
6. Polish → docs, cleanup, full gates

---

## Notes

- [P] marks tasks on different files with no incomplete dependencies
- [Story] labels map tasks to spec user stories
- Keep `frontend/src/offlineDemo.ts` unchanged; guided paths only supply its inputs
- No backend, API, or security-logic changes
- Validation evidence and requirement-to-test traceability live in `specs/005-guided-demo-paths/validation.md`
- Commit after each task or logical group; stop at checkpoints to validate independently
