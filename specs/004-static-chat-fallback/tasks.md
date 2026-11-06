---

description: "Task list template for feature implementation"
---

# Tasks: Seamless Static-Site Chat Fallback

**Input**: Design documents from `/specs/004-static-chat-fallback/`

**Prerequisites**: plan.md (required), spec.md (required for user stories); research.md, data-model.md, contracts/ — not present (frontend-only feature, none needed)

**Tests**: INCLUDED — the constitution (Principle IV) and spec checklist require every acceptance scenario to map to an automated test. Vitest suites in `frontend/src/__tests__/` are written first and must FAIL before the corresponding implementation task.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, tests in `frontend/src/__tests__/`
- All commands run from `frontend/` (`npm test`, `npm run build`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm a green baseline before any changes so regressions are attributable

- [ ] T001 Run baseline frontend test suite in `frontend/` via `npm test` and record results as the regression baseline
- [ ] T002 [P] Run baseline type-check/build in `frontend/` via `npm run build` and confirm it passes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core prerequisites that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Rewrite visitor-facing error detail copy in `frontend/src/api.ts` to plain language with zero raw HTTP status codes as the primary explanation (FR-003), keeping the `ApiError.status` field intact for programmatic fallback decisions

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Start a chat on the static page without hitting a dead-end error (Priority: P1) 🎯 MVP

**Goal**: On a backend-less page, **Start session** (including the auto-start on load) drops the visitor straight into the offline demo conversation — no rejected-request error banner, explicit offline-mode indicator, full scenario playable.

**Independent Test**: Mock all conversation requests to return 405; load the app; assert an offline greeting appears, `role="status"` shows "Offline demo mode", no `role="alert"` error is shown, no "405" text appears, and the guided scenario (name → identity question → routing) completes entirely client-side; reset restarts offline without error.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T004 [P] [US1] In `frontend/src/__tests__/App.offline.test.tsx`, rewrite the 405 start test to assert automatic fallback: offline greeting appears with no error alert and no "405 Method Not Allowed" text (FR-001, FR-003, SC-001)
- [ ] T005 [P] [US1] In `frontend/src/__tests__/App.offline.test.tsx`, add an assertion that the offline-mode indicator (`role="status"`) is visible during the conversation (FR-002, SC-004)
- [ ] T006 [P] [US1] In `frontend/src/__tests__/App.offline.test.tsx`, add a reset test: resetting an offline session restarts the offline greeting with no backend error surfaced (FR-001, acceptance scenario 4)
- [ ] T007 [P] [US1] In `frontend/src/__tests__/App.offline.test.tsx`, add a fully-offline scenario test blocking `window.fetch` entirely (network dead) that still completes start → converse → reset (FR-009, SC-006)

### Implementation for User Story 1

- [ ] T008 [US1] In `frontend/src/App.tsx` (`startSession`), on `ApiError` with `isBackendUnreachable(caught.status)`, automatically invoke the offline session start instead of calling `setError` with the rejected-request message (FR-001)
- [ ] T009 [US1] In `frontend/src/App.tsx`, guard against double-start so repeated/rapid start attempts cannot spawn two sessions or error spam (edge case: repeated Start clicks)
- [ ] T010 [US1] In `frontend/src/components/ChatPanel.tsx`, keep the offline-mode `role="status"` indicator rendered for the whole offline conversation and ensure it stays visible without scrolling on common viewports (FR-002, edge case: missed indicator)
- [ ] T011 [US1] Run `npm test` in `frontend/` and confirm all US1 tests plus pre-existing suites pass (SC-001, SC-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — this is the MVP

---

## Phase 4: User Story 2 - Understand how to get the full experience (Priority: P2)

**Goal**: When offline mode engages, the visitor sees plain-language guidance offering the offline demo and pointing to the README for running the full stack locally; no raw status codes anywhere in visitor-facing copy.

**Independent Test**: With a backend-less mock, assert the guidance text (mentioning the offline demo and README/local full stack) is present when the session starts; grep-level assertion that rendered visitor-facing messages contain no `405`/`Method Not Allowed` strings; verify README still documents the local run flow the guidance points to.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US2] In `frontend/src/__tests__/App.offline.test.tsx`, add an assertion that offline-mode guidance naming the offline demo and the README for local full-stack setup is visible when the session starts (FR-008, acceptance scenario 1)
- [ ] T013 [P] [US2] In `frontend/src/__tests__/App.offline.test.tsx`, add an assertion that no rendered visitor-facing message contains raw status-code patterns such as "405" or "Method Not Allowed" (FR-003, SC-003)

### Implementation for User Story 2

- [ ] T014 [US2] In `frontend/src/components/ChatPanel.tsx`, replace/extend the offline hint copy with plain-language guidance that offers the offline demo and points visitors to the README for running the full stack locally (FR-008), keeping `role="status"` semantics
- [ ] T015 [US2] In `frontend/src/api.ts`, ensure the unreachable-backend detail string uses plain language only (no status codes as primary explanation) per T003, and that any remaining message shown alongside the fallback never includes raw codes (FR-003)
- [ ] T016 [US2] Verify the README section referenced by the guidance exists and matches the message (README.md "run full stack locally" instructions) and update the guidance or README wording if they diverge (acceptance scenario 3)
- [ ] T017 [US2] Run `npm test` in `frontend/` and confirm all US2 tests plus prior suites pass (SC-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Keep the real backend path intact (Priority: P3)

**Goal**: A reachable backend is used exclusively; genuine application errors surface verbatim with no offline fallback offered; an unreachable-but-configured backend mid-conversation tells the visitor plainly and offers offline continuation.

**Independent Test**: Mock a reachable backend returning a real error (403 with JSON detail); assert the server's message renders, no offline-demo affordance appears, and offline mode never activates; with a healthy backend, assert zero offline indicators; with a mid-conversation network failure, assert a plain-language "could not be reached" message plus an offline continuation option.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US3] In `frontend/src/__tests__/App.retry.test.tsx`, assert a real backend error (403 with `detail` body) is displayed verbatim and no "Run offline demo" affordance is rendered (FR-006, SC-005)
- [ ] T019 [P] [US3] In `frontend/src/__tests__/App.session.test.tsx`, assert that with a healthy backend mock no offline-mode indicator or guidance ever appears across start → send → reset (FR-005, SC-005)
- [ ] T020 [P] [US3] In `frontend/src/__tests__/App.retry.test.tsx`, add a mid-conversation unreachable test: send fails with network error → plain-language "backend could not be reached" message plus offline continuation option appears (FR-007)

### Implementation for User Story 3

- [ ] T021 [US3] In `frontend/src/App.tsx` (`handleSend`), on unreachable-status failures set the offline-continuation state and a plain-language message instead of a raw failure string (FR-007), leaving genuine application errors on the existing verbatim path (FR-006)
- [ ] T022 [US3] In `frontend/src/App.tsx`, verify mode-state isolation: starting live clears offline state and vice versa; no turn/telemetry leakage across modes within a page load (FR-010)
- [ ] T023 [US3] Run `npm test` in `frontend/` and confirm all US3 tests plus prior suites pass (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T024 [P] Extend `frontend/src/__tests__/App.accessibility.test.tsx` with axe checks covering the offline indicator, guidance text, and fallback CTA in offline mode (spec Assumptions: accessibility applies to indicator/guidance)
- [ ] T025 [P] Update `README.md` live-page troubleshooting section so its description matches the new automatic-fallback behavior (guidance pointer target, SC-003 consistency)
- [ ] T026 Run full validation: `npm test` and `npm run build` in `frontend/`, plus `uv run ruff check src tests && uv run pytest -m "not live_llm and not live_speech"` from repo root to confirm the Python suite is untouched and green
- [ ] T027 Review final diff against spec FR-001…FR-010 and SC-001…SC-006; confirm constitution gates (no masking of real errors, no PII, offline deterministic) still hold

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational (T003) completion
  - Recommended order: US1 → US2 → US3 (priority order); US2/US3 can proceed in parallel with US1 once T003 is done, since they touch mostly distinct tests/copy, but `App.tsx` is shared between US1 and US3 — serialize `App.tsx` edits
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (T003) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (T003) — builds on US1's offline state for its guidance but is independently testable via the offline-start path
- **User Story 3 (P3)**: Can start after Foundational (T003) — must not regress US1; shares `frontend/src/App.tsx` with US1, so coordinate edits (US1 first)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Error/classification layer (`api.ts`) before session flow (`App.tsx`) before presentation (`ChatPanel.tsx`)
- Story complete before moving to next priority
- Commit after each task or logical group

### Parallel Opportunities

- T001 and T002 run in parallel (Setup)
- T004, T005, T006, T007 all target the same test file — run sequentially within the file, but they are parallelizable against T003
- T012 and T013 run in parallel (US2 tests, same file — serialize edits, parallel reviews)
- T018, T019, T020 target different test files — fully parallel
- T024 and T025 (Polish) are parallel (different files)
- After Foundational: US2 test authoring (T012–T013) can proceed while US1 implementation (T008–T011) is in flight, if staffed

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (after T003):
Task T004: "Rewrite 405 start test → auto-fallback assertions in frontend/src/__tests__/App.offline.test.tsx"
Task T005: "Add offline indicator assertion in frontend/src/__tests__/App.offline.test.tsx"
Task T006: "Add offline reset test in frontend/src/__tests__/App.offline.test.tsx"
Task T007: "Add fetch-blocked offline test in frontend/src/__tests__/App.offline.test.tsx"

# Then implementation (sequential, shared file):
Task T008: "Auto-fallback in startSession in frontend/src/App.tsx"
Task T009: "Double-start guard in frontend/src/App.tsx"
Task T010: "Persistent offline indicator in frontend/src/components/ChatPanel.tsx"
```

## Parallel Example: User Story 3

```bash
# Different files — launch together:
Task T018: "Real-error-unmasked test in frontend/src/__tests__/App.retry.test.tsx"
Task T019: "Healthy-backend-no-offline test in frontend/src/__tests__/App.session.test.tsx"
Task T020: "Mid-conversation unreachable test in frontend/src/__tests__/App.retry.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T004–T011)
4. **STOP and VALIDATE**: `npm test` in `frontend/` — static page starts straight into offline demo with zero error banners
5. Deploy/demo if ready (Pages deploy on merge to main)

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → test independently → deploy/demo (**MVP: the reported issue is fixed**)
3. Add User Story 2 → test independently → deploy/demo (guidance polish)
4. Add User Story 3 → test independently → deploy/demo (live-path guarantees)
5. Polish → full validation → merge

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once T003 is done:
   - Developer A: User Story 1 (owns `frontend/src/App.tsx`)
   - Developer B: User Story 2 (owns `ChatPanel.tsx` copy + `api.ts` copy review)
   - Developer C: User Story 3 tests (test files only until A lands `App.tsx` changes)
3. Stories complete and integrate independently; serialize `App.tsx` writes

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (write-first discipline per constitution Principle IV)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts (`App.tsx` shared by US1/US3), cross-story dependencies that break independence
- Out of scope (per plan.md): backend (`src/healthcare_support/`), new dependencies, persistence
