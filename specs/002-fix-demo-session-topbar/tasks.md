# Tasks: Demo Session Recovery & Rounded Highlighted Topbar

**Input**: Design documents from `specs/002-fix-demo-session-topbar/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts), [quickstart.md](./quickstart.md)

**Tests**: Included because the project constitution requires every acceptance scenario to map to an automated test and the plan commits to frontend component tests plus Python contract tests.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and demonstrated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: User story label (`US1`, `US2`, `US3`)
- Every task includes an exact file path

## Path Conventions

- Backend: `src/healthcare_support/`
- Frontend: `frontend/src/`
- Frontend tests: `frontend/src/__tests__/`
- Python contract tests: `tests/contract/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the offline frontend test runner and configuration required by all UI tests.

- [x] T001 Add `vitest`, `jsdom`, `@testing-library/react`, and `@testing-library/jest-dom` to `frontend/package.json`, add a `test` script running `vitest run`, and regenerate `frontend/package-lock.json` with `npm install`
- [x] T002 [P] Create `frontend/vitest.config.ts` with the React plugin, `jsdom` environment, `frontend/src/test/setup.ts` setup file, and an include pattern for `frontend/src/__tests__/**/*.test.{ts,tsx}`
- [x] T003 [P] Create `frontend/src/test/setup.ts` that imports `@testing-library/jest-dom/vitest` and runs Testing Library cleanup after each test

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared test harness and browser request-base behavior needed by every user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 [P] Create shared frontend test utilities in `frontend/src/test/demoHarness.tsx`: a fetch mock, a `renderApp` helper, and fixture builders for conversation turn responses and proof headers
- [x] T005 [P] Set the default browser request base to `/api` in `frontend/src/api.ts` while preserving the `VITE_API_BASE_URL` override and trailing-slash normalization, and export a typed `resolveApiBase` helper for tests

**Checkpoint**: The test harness and shared request base are ready; user stories can proceed in parallel.

---

## Phase 3: User Story 1 - Start and use the demo session (Priority: P1) 🎯 MVP

**Goal**: A visitor gets a working session automatically, can retry after a failure, and can exchange messages in the same session.

**Independent Test**: Run the frontend component tests and open the demo with the backend running. Confirm automatic session creation, enabled composer, greeting, successful message send, reset, and an actionable retry state when the backend is stopped.

### Tests for User Story 1

> Write these tests first and confirm they fail before implementation.

- [x] T006 [P] [US1] Write `frontend/src/__tests__/App.session.test.tsx` covering automatic session start, request URL `/api/conversations`, composer enablement, greeting replacement, and absence of an error banner
- [x] T007 [P] [US1] Write `frontend/src/__tests__/App.retry.test.tsx` covering the starting state, duplicate-start prevention, actionable failure message, and successful retry
- [x] T008 [P] [US1] Write `frontend/src/__tests__/App.conversation.test.tsx` covering message send to the active session with the proof header, reply rendering, failure preservation, and reset behavior

### Implementation for User Story 1

- [x] T009 [US1] Map HTTP 404 to an actionable API-route message, status `0` to a connectivity message, and preserve string server details in `frontend/src/api.ts`
- [x] T010 [US1] Guarantee one automatic session start per page load, block duplicate starts while busy, clear stale errors on retry, and preserve an active session when a message send fails in `frontend/src/App.tsx`
- [x] T011 [US1] Verify and adjust start/reset labels, composer placeholder, and disabled states to match `specs/002-fix-demo-session-topbar/contracts/ui-contract.md` in `frontend/src/components/ChatPanel.tsx`
- [x] T012 [US1] Run `cd frontend && npm test -- App.session App.retry App.conversation` for the tests in `frontend/src/__tests__/` and fix all failures

**Checkpoint**: User Story 1 is independently functional and is the MVP.

---

## Phase 4: User Story 2 - Consistent session access across environments (Priority: P2)

**Goal**: The demo reaches the backend through `/api` in local development and in the built production path, and deployment requirements are documented.

**Independent Test**: Run the Python routing/config contract test and the frontend API-base test, then start the demo with `npm run dev` and with `npm run preview`; both create a session without a 404.

### Tests for User Story 2

- [x] T013 [P] [US2] Create `tests/contract/test_frontend_demo_contract.py` asserting the default `/api` base in `frontend/src/api.ts`, `/api` proxy entries for dev and preview in `frontend/vite.config.ts`, no root `/conversations` request literal, and `/api` routing guidance in `README.md`
- [x] T014 [P] [US2] Create `frontend/src/__tests__/apiBase.test.ts` covering the default `/api` resolution, `VITE_API_BASE_URL` override, and trailing-slash normalization

### Implementation for User Story 2

- [x] T015 [US2] Add a `preview` proxy in `frontend/vite.config.ts` that mirrors the dev `/api` proxy to `http://127.0.0.1:8000`
- [x] T016 [P] [US2] Update `frontend/.env.example` to document that an empty value uses `/api` and that `VITE_API_BASE_URL` is only for direct-origin deployments
- [x] T017 [P] [US2] Update `README.md` quickstart and troubleshooting to state that the browser uses `/api`, that production must route `/api/*` to the backend root, and how to diagnose a 404 session start
- [x] T018 [US2] Run `uv run pytest tests/contract/test_frontend_demo_contract.py -q`, `cd frontend && npm test -- apiBase` for `frontend/src/__tests__/apiBase.test.ts`, and `cd frontend && npm run build` for `frontend/vite.config.ts`

**Checkpoint**: User Story 2 is independently validated in both development and preview modes.

---

## Phase 5: User Story 3 - Rounded, highlighted topbar with side margins (Priority: P3)

**Goal**: The topbar renders as a floating sticky surface with visible side spacing, rounded corners, and an accent highlight at desktop and mobile widths.

**Independent Test**: Run the CSS contract and topbar render tests, then inspect the page at 1440px, 768px, and 320px widths for margins, rounding, highlight, sticky behavior, no horizontal scroll, and visible keyboard focus.

### Tests for User Story 3

- [x] T019 [P] [US3] Create `tests/contract/test_topbar_presentation.py` asserting the `.site-header` rule includes `position: sticky`, a top offset, margin, padding, `border-radius`, a border, `box-shadow`, and `backdrop-filter`, plus a mobile media-query override preserving radius and padding
- [x] T020 [P] [US3] Create `frontend/src/__tests__/App.topbar.test.tsx` asserting the page renders a `site-header` element containing the brand link and primary navigation links

### Implementation for User Story 3

- [x] T021 [US3] Restyle `.site-header` in `frontend/src/styles.css` as a floating sticky surface with a top offset, margin, horizontal padding, all-corner rounding, an accent-tinted border, and a layered shadow/glow
- [x] T022 [US3] Update the `max-width: 700px` `.site-header` rule in `frontend/src/styles.css` to preserve side spacing, rounding, highlight, and stacked layout without horizontal scrolling
- [x] T023 [US3] Add hover/focus-within highlight intensification and confirm focus-visible contrast for topbar links in `frontend/src/styles.css`
- [x] T024 [US3] Run `uv run pytest tests/contract/test_topbar_presentation.py -q`, `cd frontend && npm test -- App.topbar`, and `cd frontend && npm run build`, then perform the visual checks in `specs/002-fix-demo-session-topbar/quickstart.md`

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Full quality gates and end-to-end validation across the feature.

- [x] T025 [P] Run `uv run pytest -m "not live_llm and not live_speech" --cov=src/healthcare_support --cov-branch --cov-report=term-missing --cov-fail-under=80` against `tests/`
- [x] T026 [P] Run `uv run mypy src`, `uv run ruff check src tests`, and `uv run ruff format --check src tests` against `src/healthcare_support/` and `tests/`
- [x] T027 [P] Run `cd frontend && npm test` for `frontend/src/__tests__/` and `cd frontend && npm run build` for `frontend/`
- [x] T028 Execute every scenario in `specs/002-fix-demo-session-topbar/quickstart.md`, including backend-down retry and responsive topbar checks
- [x] T029 [P] Review `README.md`, `frontend/.env.example`, and `specs/002-fix-demo-session-topbar/contracts/session-api.md` for consistent `/api` guidance and remove stale 404 instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; no dependency on other stories.
- **User Story 2 (Phase 4)**: Depends on Foundational; does not require US1 implementation.
- **User Story 3 (Phase 5)**: Depends on Foundational; does not require US1 or US2 implementation.
- **Polish (Phase 6)**: Depends on all desired stories being complete.

### User Story Dependencies

- **US1**: Independent after Phase 2. T009 depends on T005 because both edit `frontend/src/api.ts`.
- **US2**: Independent after Phase 2. T015 edits `frontend/vite.config.ts`; T016 and T017 are separate files and can run in parallel with T015.
- **US3**: Independent after Phase 2. T022 and T023 depend on T021 because all three edit `frontend/src/styles.css`.

### Within Each User Story

- Tests are written first and must fail before implementation.
- Shared client/config changes precede story-specific UI changes.
- Run the story's focused tests before moving to the next priority.

### Parallel Opportunities

- Setup: T002 and T003 can run in parallel after T001 installs dependencies.
- Foundational: T004 and T005 can run in parallel.
- US1: T006, T007, and T008 are separate test files and can run in parallel. T010 and T011 are separate files and can run in parallel after T009.
- US2: T013 and T014 are separate test files. T016 and T017 are separate documentation files.
- US3: T019 and T020 are separate test files.
- Polish: T025, T026, T027, and T029 are independent checks.

---

## Parallel Example: User Story 1

```bash
# Launch the three story tests together:
Task: "Write frontend/src/__tests__/App.session.test.tsx"
Task: "Write frontend/src/__tests__/App.retry.test.tsx"
Task: "Write frontend/src/__tests__/App.conversation.test.tsx"

# After T009, launch the UI changes together:
Task: "Update frontend/src/App.tsx"
Task: "Update frontend/src/components/ChatPanel.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch the independent test files:
Task: "Create tests/contract/test_frontend_demo_contract.py"
Task: "Create frontend/src/__tests__/apiBase.test.ts"

# Launch the documentation updates together:
Task: "Update frontend/.env.example"
Task: "Update README.md"
```

## Parallel Example: User Story 3

```bash
# Launch the independent test files:
Task: "Create tests/contract/test_topbar_presentation.py"
Task: "Create frontend/src/__tests__/App.topbar.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Run the US1 component tests and manually confirm a session starts, messages send, reset works, and failures retry.
5. Deploy or demo the MVP.

### Incremental Delivery

1. Setup + Foundational → test harness and `/api` base ready.
2. US1 → working session flow (MVP).
3. US2 → validated development and production routing plus documentation.
4. US3 → polished floating highlighted topbar.
5. Polish → full quality gates and quickstart validation.

### Parallel Team Strategy

1. One developer completes Setup and Foundational.
2. Then:
   - Developer A: User Story 1.
   - Developer B: User Story 2.
   - Developer C: User Story 3.
3. Integrate and run the full polish phase.

---

## Notes

- `[P]` marks different files with no dependency on an incomplete task.
- Tests are mandatory for this feature because of Constitution Principle IV and the plan's acceptance mapping.
- Do not change backend session, proof, guardrail, telemetry, or Pydantic response contracts.
- Commit after each logical group and stop at each checkpoint to validate independently.
