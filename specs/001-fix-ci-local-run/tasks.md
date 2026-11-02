---

description: "Task list for fixing dependency update pipeline and local run"
---

# Tasks: Fix Dependency Update Pipeline and Local Run

**Input**: Design documents from `/specs/001-fix-ci-local-run/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: No new test files are required. The existing offline suite (510 tests after adding the env-file regression test in `tests/unit/test_llm_configuration.py`) and the contract tests in `tests/contract/` are the validation gate and must remain intact.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- All paths are relative to the repository root `/Users/isabelsoares/Repos/agentflow-ai`

## Path Conventions

- Backend source: `src/healthcare_support/`
- Backend tests: `tests/`
- Frontend: `frontend/`
- Workflows: `.github/workflows/`
- Dependency metadata: `pyproject.toml`, `uv.lock`
- Developer documentation: `README.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the branch and scope before changing dependency metadata

- [X] T001 Confirm `fix/ci-lockfile-local-run` is based on current `main` and that the only existing feature changes are under `specs/001-fix-ci-local-run/` using `git log --oneline main..HEAD`, `git diff --stat main...HEAD`, and `git status --short`
- [X] T002 [P] Confirm PR #5 changes only `pyproject.toml` by running `gh pr diff 5 --repo isabelSoares/agentflow-ai --name-only`; record the result in the PR description for `specs/001-fix-ci-local-run/spec.md`

**Checkpoint**: Branch scope is understood and no unrelated PR history will be carried over.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Reconcile the manifest and lock state; every user story depends on this

**⚠️ CRITICAL**: No pipeline, local-run, or consistency validation can pass until this phase is complete.

- [X] T003 Apply PR #5's dependency minimums to `pyproject.toml`: `fastapi>=0.162.0`, `uvicorn[standard]>=0.54.0`, `langgraph>=1.2.18`, `langchain-openai>=1.7.3`, `openai>=3.39.0`, `pydantic>=2.14.1`, `pydantic-settings>=2.16.1`, `phonenumbers>=9.0.42`, `schwifty>=2026.10.1`, `python-multipart>=0.0.32`, `opentelemetry-api>=1.45.1`, `opentelemetry-sdk>=1.45.1`; dev group: `pytest>=9.1.1`, `pytest-cov>=7.1.0`, `pip-audit>=2.10.1`, `httpx>=0.28.1`, `ruff>=0.17.3`, `mypy>=2.4.0`
- [X] T004 Regenerate `uv.lock` with `uv lock` from the repository root and confirm the resolved set matches the versions recorded in `specs/001-fix-ci-local-run/research.md`
- [X] T005 Verify the reconciled state with `uv lock --check` and `uv sync --locked`; both must succeed with no request to update `uv.lock`

**Checkpoint**: `pyproject.toml` and `uv.lock` are consistent, so all user stories can now be validated.

---

## Phase 3: User Story 1 - Green Pipeline for the Dependency Update (Priority: P1) 🎯 MVP

**Goal**: Every required pull-request job passes on the new branch.

**Independent Test**: Open a pull request from `fix/ci-lockfile-local-run` to `main` and confirm the quality, frontend, dependency audit, and container jobs all conclude successfully.

### Validation for User Story 1

- [X] T006 [US1] Run the quality gate locally: `uv run pytest -m "not live_llm and not live_speech" --cov=src/healthcare_support --cov-branch --cov-report=term-missing --cov-fail-under=80`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, and `uv run mypy src`; expect 510 passed, coverage >=80%, and all static checks clean
- [X] T007 [US1] Run the strict dependency audit from `uv.lock`: `uv export --locked --format requirements.txt --no-editable --no-emit-project --output-file /tmp/agentflow-ai-requirements.txt` followed by `uv run pip-audit --strict -r /tmp/agentflow-ai-requirements.txt`; expect no known vulnerabilities
- [X] T008 [P] [US1] Validate the frontend job inputs from `frontend/package-lock.json` with `npm ci` and `npm run build` in `frontend/`; expect a successful type-checked production build
- [X] T009 [P] [US1] Validate the container job locally if Docker is available using `Dockerfile`: build the image, confirm `id -u` returns `10001`, start it, and poll `http://127.0.0.1:8000/health` for up to 30 seconds; if Docker is unavailable, record that the remote Container workflow is the authoritative check
- [ ] T010 [US1] Push `fix/ci-lockfile-local-run`, open or refresh the pull request against `main` using `.github/workflows/ci.yml`, `.github/workflows/dependency-audit.yml`, and `.github/workflows/container.yml`, and confirm all four required jobs pass with no skipped or disabled gates — **PENDING**: requires explicit approval to push and open a pull request

**Checkpoint**: User Story 1 is complete when the pull request is fully green.

---

## Phase 4: User Story 2 - Reliable Local Setup (Priority: P2)

**Goal**: A developer can follow the documented steps from a clean checkout and run the project locally.

**Independent Test**: From a clean clone of the branch, follow `specs/001-fix-ci-local-run/quickstart.md` and verify locked installation, backend health, offline tests, and frontend build all succeed.

### Implementation for User Story 2

- [X] T011 [US2] Add a short troubleshooting note to `README.md` in the Quickstart or dependency section stating that `uv sync --locked` fails when `pyproject.toml` and `uv.lock` drift, and that the recovery is `uv lock` followed by `uv sync --locked` with `uv.lock` committed alongside the manifest change
- [X] T012 [US2] Verify backend startup from `README.md` and `src/healthcare_support/api/app.py` with an empty `GROQ_API_KEY`: copy `.env.example` to `.env`, run `uv run uvicorn healthcare_support.api.app:create_app --factory --port 8000`, and confirm `curl -fsS http://localhost:8000/health` succeeds without a live model provider; if comma-separated env values fail to parse, mark `cors_allowed_origins` and `voice_supported_input_types` with `NoDecode` in `src/healthcare_support/config/__init__.py` and add a temporary-`.env` regression test in `tests/unit/test_llm_configuration.py`
- [X] T013 [US2] Execute `specs/001-fix-ci-local-run/quickstart.md` sections 1-5 in a fresh clone or clean worktree, including `uv sync --locked`, the offline test suite, `ruff`, `mypy`, the strict audit, backend health, and `npm ci` plus `npm run build` in `frontend/`; record any command that deviates from the guide

**Checkpoint**: User Story 2 is complete when a clean checkout reaches a healthy local backend without workarounds.

---

## Phase 5: User Story 3 - Dependency Updates Stay Consistent (Priority: P3)

**Goal**: Future dependency manifest changes are validated against a matching lock and do not fail late in the pipeline.

**Independent Test**: In a scratch copy, change a dependency range without updating the lock and confirm that locked installation fails immediately; then regenerate the lock and confirm the same change passes.

### Implementation for User Story 3

- [X] T014 [US3] Add a maintainer-facing dependency-update note to `README.md` explaining that a version-range change in `pyproject.toml` must be paired with a regenerated `uv.lock`, and that `--locked` installation and strict audit remain the required checks
- [X] T015 [US3] Verify stale-lock detection in a temporary worktree or copy of `pyproject.toml` and `uv.lock`: raise one version requirement without running `uv lock`, confirm `uv sync --locked` fails with the stale-lock error, then run `uv lock`, confirm the locked install succeeds, and discard the scratch changes
- [X] T016 [P] [US3] Confirm dependency automation and gates remain enabled by reviewing `.github/dependabot.yml` for pip, npm, GitHub Actions, and Docker entries, and confirm `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml` still use `--locked`

**Checkpoint**: User Story 3 is complete when the stale-lock failure mode is detectable and the maintenance workflow is documented.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup across all stories

- [X] T017 Run `specs/001-fix-ci-local-run/quickstart.md` end-to-end one final time on the completed branch and compare the results against SC-001 through SC-008 in `specs/001-fix-ci-local-run/spec.md`
- [X] T018 Review `git diff main...HEAD` and confirm the change surface is limited to `pyproject.toml`, `uv.lock`, `src/healthcare_support/config/__init__.py`, `tests/unit/test_llm_configuration.py`, `README.md`, and `specs/001-fix-ci-local-run/`; confirm the only application-source change is the targeted `NoDecode` annotation and that no security logic, pipeline gate, container hardening, or existing contract test was weakened
- [ ] T019 After the pull request merges, close PR #5 as superseded and reference the merged pull request and the regenerated `uv.lock` — **PENDING**: requires the pull request to be pushed, reviewed, and merged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; this is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; can start after T005. The README task T011 does not depend on US1.
- **User Story 3 (Phase 5)**: Depends on Foundational; T014 edits `README.md` and should follow T011 to avoid conflicts. T015 and T016 can run independently.
- **Polish (Final Phase)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational; green pipeline is the first deliverable.
- **US2 (P2)**: Independent after Foundational; validates the same lock from the developer path.
- **US3 (P3)**: Independent after Foundational; adds recurrence protection and documentation after the local path is proven.

### Within Each User Story

- Foundational manifest and lock changes come before every validation.
- Local quality and audit checks come before the remote pull request run.
- Documentation updates happen before the final quickstart validation.
- The final diff review happens after all edits and before closing PR #5.

### Parallel Opportunities

- T001 and T002 can run in parallel.
- T008 (frontend) and T009 (container) can run in parallel with T006/T007 once T005 completes.
- T012 (backend health) and T016 (workflow review) can run in parallel after T005.
- T015 (scratch stale-lock check) can run in parallel with T016.
- T011 and T014 both edit `README.md` and must run sequentially.

---

## Parallel Example: User Story 1

```bash
# After T005 completes, launch independent validations:
Task: "Run the quality gate in tests/ and src/ (T006)"
Task: "Run the strict audit from uv.lock (T007)"
Task: "Build the frontend from frontend/package-lock.json (T008)"
Task: "Validate the container from Dockerfile (T009)"
```

---

## Parallel Example: User Story 3

```bash
# After T014 completes, run independent recurrence checks:
Task: "Verify stale-lock detection in a temporary worktree (T015)"
Task: "Review .github/dependabot.yml and workflow --locked usage (T016)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T002 to confirm branch scope.
2. Complete T003-T005 to reconcile `pyproject.toml` and `uv.lock`.
3. Complete T006-T009 to reproduce every pipeline job locally.
4. Complete T010 and stop when the pull request is green.
5. Validate that the original PR #5 can be closed as superseded.

### Incremental Delivery

1. **Foundational**: Apply the manifest and lock; validate locked installation.
2. **US1**: Prove all four pipeline jobs pass; this is the mergeable MVP.
3. **US2**: Add local troubleshooting documentation and validate the full developer path.
4. **US3**: Add recurrence protection documentation and verify stale-lock detection.
5. **Polish**: Run the final end-to-end quickstart, review the diff, and close PR #5.

### Notes

- [P] tasks touch different files or independent environments and can run concurrently.
- [US1], [US2], and [US3] map directly to the prioritized user stories in `spec.md`.
- Do not remove or weaken any existing test, workflow gate, or container control to make validation pass.
- If a dependency upgrade fails a gate, create a compatibility finding per `data-model.md`, select the closest compatible version, and document the deviation from PR #5.
- Do not commit unless the user explicitly requests it.
- T010 and T019 remain pending because pushing, opening a pull request, and closing PR #5 require explicit approval; every local implementation and validation task is complete.
