# Implementation Plan: Fix Dependency Update Pipeline and Local Run

**Branch**: `fix/ci-lockfile-local-run` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-fix-ci-local-run/spec.md`

## Summary

PR #5 raises backend dependency minimums in `pyproject.toml` but does not update `uv.lock`. Every failing job stops at the first step (`uv sync --locked`) with "The lockfile at `uv.lock` needs to be updated", which also explains why the updated project cannot be installed locally. A probe on a detached worktree of `main` with PR #5's `pyproject.toml` applied shows that regenerating `uv.lock` clears the pipeline failures: the locked installation succeeds, all 509 offline tests pass at 91.38% coverage, ruff/format/mypy pass, `pip-audit --strict` reports no vulnerabilities, and the frontend `npm ci && npm run build` succeeds. Implementing the quickstart with a real `.env` then exposed a second local-run failure: the upgraded settings library rejects comma-separated complex values before the project's custom parser runs. The plan therefore covers dependency-state reconciliation on a fresh branch from `main`, a targeted no-decode annotation for the two comma-separated setting fields plus a regression test, and a short documentation note so future dependency bumps include the lock update.

## Technical Context

**Language/Version**: Python >=3.12 (CI and container use 3.13); TypeScript with Node.js 22.12+ locally and Node.js 24 in CI

**Primary Dependencies**: FastAPI 0.162.0, Uvicorn 0.54.0, LangGraph 1.2.19, langchain-openai 1.7.3, OpenAI SDK 3.42.0, Pydantic 2.14.1, pydantic-settings 2.16.2, phonenumbers 9.0.42, schwifty 2026.10.1, python-multipart 0.0.32, OpenTelemetry API/SDK 1.45.1; React 19, Vite 8, TypeScript 7 in the frontend; pytest 9.1.1, pytest-cov 7.1.0, ruff 0.17.3, mypy 2.4.0, pip-audit 2.10.1, httpx 0.28.1 for development

**Storage**: In-memory repositories, session store, and conversation history adapters; no external database

**Testing**: pytest offline suite (510 tests including the new env-file regression test, 9 live tests deselected), coverage gate >=80%, ruff lint/format checks, strict mypy, frontend type-checked production build, `pip-audit --strict`

**Target Platform**: Linux CI runners and container runtime; macOS/Linux developer workstations

**Project Type**: Web service with a React single-page client

**Performance Goals**: Preserve existing service startup and health behavior; container must become healthy within the existing 30-second window

**Constraints**: Locked dependency installation everywhere, offline-capable tests, no live model key required locally, non-root container user UID 10001, Python 3.12+ and Node.js 22.12+ local support, no weakening of pipeline gates

**Scale/Scope**: One backend service, one frontend client, 97 resolved packages, and 190 tracked repository files; expected change surface is `pyproject.toml`, `uv.lock`, `src/banking_support/config/__init__.py`, `tests/unit/test_llm_configuration.py`, and README guidance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Security First | PASS | No runtime, data-access, authentication, or response-shaping code changes; existing security probes and sanitization tests remain mandatory and must pass. |
| II. Deterministic Verification | PASS | Identity matching, secret verification, classification, and routing logic are untouched; dependency bumps are validated by the full offline suite. |
| III. Separation of Concerns | PASS | Only dependency metadata and documentation change; module boundaries remain unchanged. |
| IV. Testability | PASS | The plan requires the entire 510-test offline suite, the 80% coverage gate, and all existing contract tests to pass without network or live services. |
| V. Type Safety | PASS | Strict mypy over `src` remains a required gate; dependency upgrades must not introduce type errors. |
| VI. Observability | PASS | Logging, tracing, and audit behavior are unchanged; no sensitive data is added to dependency or documentation changes. |
| VII. Simplicity | PASS | The smallest change that satisfies the requirement is to apply PR #5's manifest and regenerate the lock; no new abstractions, scripts, or workflow stages are introduced. |
| Additional Constraints | PASS | Technology baseline is unchanged, credentials are not introduced, and the existing CI quality gate remains the merge condition. |

**Gate result**: PASS. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-ci-local-run/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 validation guide
├── contracts/
│   └── ci-local-run-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
src/banking_support/
├── api/                 # FastAPI application and contracts
├── agents/              # LangGraph orchestration and nodes
├── core/                # Deterministic security and routing logic
├── data/                # Repositories, session access, history
├── domain/              # Pydantic domain models
├── observability/       # Logging and tracing
├── resilience/          # Retry and degradation policy
├── services/            # Guardrail service boundary
└── voice/               # Optional STT/TTS adapters

frontend/
├── src/                 # React + TypeScript client
├── package.json
└── package-lock.json

tests/
├── contract/            # API, workflow, container, dependency contracts
├── integration/         # End-to-end workflow and security scenarios
└── unit/                # Deterministic business-rule tests

.github/workflows/
├── ci.yml
├── container.yml
└── dependency-audit.yml

pyproject.toml
uv.lock
README.md
Dockerfile
```

**Structure Decision**: Keep the existing single-repository backend/frontend layout. This feature is a dependency and documentation maintenance change, so no source-tree reorganization is needed.

## Phase 0: Research

Research is recorded in [research.md](./research.md). Key decisions:

- Apply PR #5's dependency minimums and regenerate `uv.lock` on a branch created from current `main`; do not merge PR #5's pre-squash history.
- Keep workflow commands and the `--locked` contract unchanged; the lock must satisfy the manifest rather than relaxing CI.
- Keep the settings fix targeted: annotate the two comma-separated set fields with `NoDecode` so the existing validators handle `.env` values, and add a regression test that loads a real env file.
- Document the manifest-plus-lock workflow for future dependency bumps.

## Phase 1: Design

Design artifacts:

- [data-model.md](./data-model.md) defines the dependency update, resolved state, pipeline run, local quickstart, and compatibility finding.
- [contracts/ci-local-run-contract.md](./contracts/ci-local-run-contract.md) defines required pipeline jobs and local-run command outcomes.
- [quickstart.md](./quickstart.md) provides the runnable validation sequence.

## Implementation Approach

1. Start from current `main` and apply only PR #5's `pyproject.toml` version changes; do not carry over unrelated historical commits.
2. Regenerate the resolved dependency state with `uv lock` and commit the resulting `uv.lock`.
3. Fix the discovered `.env` parsing regression in `src/banking_support/config/__init__.py` by marking the comma-separated set fields `NoDecode`, and add a regression test in `tests/unit/test_llm_configuration.py`.
4. Validate the locked environment locally: `uv sync --locked`, offline tests with coverage, lint, format check, mypy, strict audit, backend startup with the copied env file, and the frontend build.
5. Add a concise README note explaining that dependency-version changes must be accompanied by a regenerated lock, including the exact recovery command when locked installation rejects a stale lock.
6. Open a pull request to `main` and confirm all required jobs pass; the original PR #5 can then be closed as superseded.

## Post-Design Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Security First | PASS | No security boundary, PII path, or credential handling changes. |
| II. Deterministic Verification | PASS | Deterministic logic remains untouched and fully tested. |
| III. Separation of Concerns | PASS | No module boundary changes. |
| IV. Testability | PASS | Quickstart and contracts require the full offline suite and coverage gate. |
| V. Type Safety | PASS | mypy strict remains a required validation step. |
| VI. Observability | PASS | No logging or tracing changes. |
| VII. Simplicity | PASS | Two metadata files plus one documentation note; no new mechanism. |

## Complexity Tracking

No constitution violations or added complexity. This section is intentionally empty.
