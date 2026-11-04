---

description: "Task list for launch readiness verification feature"
---

# Tasks: Launch Readiness Verification

**Input**: Design documents from `/specs/003-launch-readiness-check/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/cli-schema.md, quickstart.md

**Tests**: Included — constitution Principle IV requires every acceptance scenario to map to at least one automated test that runs offline. Write tests first, ensure they fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project: `src/`, `tests/`, `scripts/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the readiness package skeleton and CLI entry point per plan.md

- [ ] T001 Create package skeleton `src/healthcare_support/readiness/__init__.py` (empty exports) and `scripts/check_launch_readiness.py` thin wrapper that calls `healthcare_support.readiness.cli:main`
- [ ] T002 Create test directory `tests/unit/readiness/` with `__init__.py` so pytest collects it

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, verdict aggregation, and command-runner infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Create Pydantic models in `src/healthcare_support/readiness/models.py` per data-model.md: `Verdict` enum (`ready`/`not_ready`), `CriterionStatus` enum (`pass`/`fail`/`unable_to_verify`), `CriterionResult` (fields: name: str, category: str, status: CriterionStatus, details: str, remediation: str; validator: remediation MUST be non-empty when status != pass, details MUST be non-empty), `ReadinessReport` (fields: verdict: Verdict, run_at: datetime, results: list[CriterionResult])
- [ ] T004 [P] Implement deterministic fail-closed verdict aggregation and report rendering (text + JSON) in `src/healthcare_support/readiness/report.py`: verdict is `ready` iff every result status is `pass`; render functions emit only names/statuses/remediation — never secret values or PII (FR-007, FR-008, FR-010)
- [ ] T005 Implement subprocess runner with per-criterion timeout in `src/healthcare_support/readiness/runner.py`: runs a command, captures summarized output (no raw dump), returns CriterionResult with `unable_to_verify` on timeout/missing tool (default 240s, configurable via --timeout)
- [ ] T006 [P] Implement CLI argument parsing and exit codes in `src/healthcare_support/readiness/cli.py` per contracts/cli-schema.md: flags `--json`, `--timeout SECONDS`; exit 0 = ready, 1 = not_ready, 2 = check error
- [ ] T007 [P] Write foundational unit tests in `tests/unit/readiness/test_models.py` and `tests/unit/readiness/test_report.py`: enum values, remediation-required validator, verdict aggregation (all pass → ready; any fail/unable_to_verify → not_ready), redaction guarantee on rendered output

**Checkpoint**: Foundation ready — models, verdict logic, runner, and CLI skeleton are in place and unit-tested

---

## Phase 3: User Story 1 - Run a Complete Launch Readiness Check (Priority: P1) 🎯 MVP

**Goal**: A single command evaluates all go/no-go criteria (tests, quality gates, deployment config) and returns a definitive ready/not-ready verdict with per-criterion results

**Independent Test**: Run `uv run python scripts/check_launch_readiness.py` on a healthy checkout → exit 0, all criteria `pass`, verdict `READY`; force one failing test → exit 1, that criterion `fail`, verdict `NOT READY` (spec US1 acceptance scenarios 1–2; quickstart scenarios 1–3)

### Tests for User Story 1

- [ ] T008 [P] [US1] Unit tests in `tests/unit/readiness/test_checks.py` for each evaluator: offline-tests, frontend-tests, lint, format, type-check, coverage-gate, frontend-build, deployment-config — mocking the runner to return pass/fail/timeout and asserting the produced CriterionResult (covers spec edge cases: mid-development failures still complete; missing tool → unable_to_verify; offline run evaluates all offline criteria)
- [ ] T009 [P] [US1] CLI end-to-end test in `tests/unit/readiness/test_cli.py`: invoke `cli.main` with `--json` against a stubbed criterion set; assert exit codes 0/1/2 and JSON schema matches contracts/cli-schema.md

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement criterion evaluators in `src/healthcare_support/readiness/checks.py` invoking the exact CI gate commands from `.github/workflows/ci.yml`: `ruff check src tests`, `ruff format --check src tests`, `mypy src`, `pytest -m "not live_llm and not live_speech" --cov=src/healthcare_support --cov-branch --cov-fail-under=80`, frontend `npm test` / `npm run build` (skipped-and-blocking when `frontend/` absent)
- [ ] T011 [US1] Implement deployment-config criterion in `src/healthcare_support/readiness/checks.py`: presence of Dockerfile, `.github/workflows/ci.yml`, required env var NAMES present (values never read into the report) per FR-004
- [ ] T012 [US1] Wire all US1 criteria into `run_all_checks()` in `src/healthcare_support/readiness/checks.py`, aggregate via `report.py`, and connect in `cli.py` so the command prints the full report and sets the exit code (FR-001, FR-002, FR-003, FR-004, FR-009)

**Checkpoint**: User Story 1 fully functional and testable independently — `check_launch_readiness.py` yields a correct verdict on healthy and failing states

---

## Phase 4: User Story 2 - Actionable Remediation Guidance for Failures (Priority: P2)

**Goal**: Every failed or unverifiable criterion includes concrete remediation guidance naming the failing item and the step to resolve it

**Independent Test**: Force a failing gate and a timeout; run the check; assert each non-pass criterion's `remediation` names the gate and the exact command/step to fix it, and that a security-style failure never prints the sensitive value (spec US2 acceptance scenarios 1–2; quickstart scenarios 2 and 4)

### Tests for User Story 2

- [ ] T013 [P] [US2] Unit tests in `tests/unit/readiness/test_remediation.py`: for every criterion in the catalog, a fail and an unable_to_verify result MUST carry non-empty remediation text referencing the relevant command; rendered text and JSON outputs contain remediation for 100% of non-pass criteria (SC-004)

### Implementation for User Story 2

- [ ] T014 [US2] Add the static remediation catalog (one entry per criterion name from data-model.md's criterion catalog, e.g. offline-tests → "Run `uv run pytest -m \"not live_llm and not live_speech\"` and fix the failing tests") to `src/healthcare_support/readiness/checks.py` and attach it when building each CriterionResult (FR-006)
- [ ] T015 [US2] Extend text rendering in `src/healthcare_support/readiness/report.py` to group results by category and print remediation lines under each non-pass criterion, ending with `LAUNCH READINESS: READY` / `LAUNCH READINESS: NOT READY` (FR-010)

**Checkpoint**: User Stories 1 AND 2 both work independently — verdicts are correct and every failure is actionable

---

## Phase 5: User Story 3 - Verify Security and Compliance Posture (Priority: P3)

**Goal**: The check explicitly verifies security criteria — no committed secrets, dependency vulnerabilities audited, no PII/secret answers at the API/log boundary — and blocks launch on any violation without disclosing sensitive values

**Independent Test**: Append a fake API key (`AKIA...EXAMPLE`) to a tracked file, run the check → `committed-secrets` is `fail`, report names file+pattern but NOT the key value, verdict NOT READY, exit 1; remove it → criterion passes (spec US3 acceptance scenarios 1–3; quickstart scenario 5)

### Tests for User Story 3

- [ ] T016 [P] [US3] Unit tests in `tests/unit/readiness/test_security.py`: committed-secret pattern scan detects key/token/private-key patterns in tracked files and redacts values from details; dependency-audit maps pip-audit output to pass/fail/unable_to_verify; boundary check asserts sanitized response models and absence of secret-answer fields in log statements

### Implementation for User Story 3

- [ ] T017 [P] [US3] Implement `committed-secrets` criterion in `src/healthcare_support/readiness/checks.py`: scan `git ls-files` output for API-key/token/private-key patterns; report only file path + pattern name, never the matched value (FR-005, FR-008)
- [ ] T018 [P] [US3] Implement `dependency-audit` criterion in `src/healthcare_support/readiness/checks.py` using existing `pip-audit` against the locked dependency set; offline DB failure → `unable_to_verify` (research R3/R6)
- [ ] T019 [US3] Implement `no-pii-in-boundary` criterion in `src/healthcare_support/readiness/checks.py`: verify API response models are the sanitized Pydantic models and no log statement includes secret-answer/credential fields (static import + source check, deterministic per Principle II)
- [ ] T020 [US3] Register all three security criteria in `run_all_checks()` in `src/healthcare_support/readiness/checks.py` (FR-005)

**Checkpoint**: All user stories independently functional — full check covers tests, quality gates, deployment, and security

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: CI integration, constitution compliance validation, and quickstart verification

- [ ] T021 Add a readiness job to `.github/workflows/ci.yml` that runs `uv run python scripts/check_launch_readiness.py` after the quality/frontend jobs and fails the workflow on exit code 1 (FR-009, SC-005)
- [ ] T022 [P] Run full offline validation per quickstart.md scenarios 1–6: `uv run pytest tests/unit/readiness/ -m "not live_llm and not live_speech"`, plus ruff, mypy strict, and coverage gate on the new module — all must pass (constitution quality gate)
- [ ] T023 [P] Update `docs/` with a short "Launch readiness check" section linking to `specs/003-launch-readiness-check/quickstart.md` (FR-010 stakeholder readability)
- [ ] T024 Final constitution compliance pass: confirm Principle I (no PII/secrets in report — T004/T017 tests), II (deterministic verdict — T004), III (module independent of api/agents — T001), IV (offline tests map to acceptance scenarios — T007–T016), V (Pydantic + type hints, mypy strict — T022), VI (structured logs of criterion outcomes without sensitive values), VII (no unjustified abstractions)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Stories (Phases 3–5)**: All depend on Phase 2; proceed in priority order P1 → P2 → P3, or in parallel if staffed
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational — no dependencies on other stories (MVP)
- **User Story 2 (P2)**: After Foundational — builds on report rendering from Phase 2 and criteria from US1, but is independently testable via its own tests
- **User Story 3 (P3)**: After Foundational — independent criteria, independently testable

### Within Each User Story

- Tests MUST be written first and FAIL before implementation (T008 before T010–T012, T013 before T014–T015, T016 before T017–T020)
- Models before services; runner before evaluators; evaluators before CLI wiring

### Parallel Opportunities

- Phase 2: T003, T004, T006, T007 are [P] (different files)
- US1: T008 and T009 are [P]; T010 is [P] once runner exists
- US2: T013 is [P] alongside T014/T015 implementation files
- US3: T016, T017, T018 are [P] (different files/concerns)
- Polish: T022 and T023 are [P]

---

## Parallel Example: User Story 3

```bash
Task: "Unit tests for security criteria in tests/unit/readiness/test_security.py (T016)"
Task: "Committed-secrets scan in src/healthcare_support/readiness/checks.py (T017)"
Task: "Dependency-audit criterion in src/healthcare_support/readiness/checks.py (T018)"
```

(Note: T017/T018 edit the same file, so run sequentially in practice; T016 is fully parallel.)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run `uv run python scripts/check_launch_readiness.py`; verify exit 0 on healthy tree and exit 1 with a forced failure
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add US1 → test independently → MVP (a working launch readiness verdict)
3. Add US2 → remediation guidance complete → test independently
4. Add US3 → security posture verified → test independently
5. Polish: CI gate + docs + constitution pass

---

## Notes

- [P] tasks = different files, no dependencies (where noted)
- [Story] labels map tasks to spec.md user stories for traceability
- Every acceptance scenario in spec.md maps to at least one test task (T007–T016) per constitution Principle IV
- Verify tests fail before implementing each story
- Commit after each task or logical group
- Stop at each checkpoint to validate the story independently
