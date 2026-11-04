# Implementation Plan: Launch Readiness Verification

**Branch**: `003-launch-readiness-check` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-launch-readiness-check/spec.md`

## Summary

Add a single launch readiness check that evaluates every go/no-go criterion — offline test suite, lint/format/type/coverage gates, frontend tests and build, deployment configuration, and security posture (no committed secrets, no PII/secrets in logs or API responses) — and emits a fail-closed report with an overall "ready to launch" / "not ready to launch" verdict plus per-criterion remediation guidance. Implemented as a deterministic, fully typed verification module in the backend package with a thin CLI wrapper, runnable identically locally and in CI.

## Technical Context

**Language/Version**: Python 3.12+ (CI runs 3.13; `requires-python = ">=3.12"`)

**Primary Dependencies**: FastAPI, uvicorn, LangGraph, Pydantic / pydantic-settings (existing); pytest + pytest-cov, ruff, mypy strict, pip-audit (existing dev gates the check evaluates); no new runtime dependencies

**Storage**: N/A (no database; seed dataset lives in the data-access layer)

**Testing**: pytest (offline suite `-m "not live_llm and not live_speech"`, coverage gate `--cov-fail-under=80`), ruff check/format, mypy strict — the exact CI gates the readiness check must invoke; plus new unit tests for the readiness module itself

**Target Platform**: Linux server (Docker runtime image) + GitHub Actions CI; React/TypeScript frontend built with npm

**Project Type**: web-service (backend API + frontend client) plus developer tooling (CLI check)

**Performance Goals**: full readiness report with verdict in under 5 minutes on a standard dev machine (SC-001)

**Constraints**: fail-closed verdicts (unverifiable = blocking); report must never print secrets, credentials, or PII; offline-capable checks must run without network; identical criteria and verdict logic locally and in CI; verdict logic deterministic, never LLM-based

**Scale/Scope**: single small project; one CLI command + one report format (text and JSON) consumed by maintainers and CI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **I. Security First**: PASS — the report model redacts values; security criteria scan for secrets/PII without printing them (FR-008). No patient data is read or exposed by the check.
- **II. Deterministic Verification**: PASS — verdict is computed from structured criterion results in code; no LLM involvement anywhere in the check.
- **III. Separation of Concerns**: PASS — readiness logic lives in its own module (`src/healthcare_support/readiness/`), callable without the API or agent layers; the CLI in `scripts/` is a thin wrapper.
- **IV. Testability**: PASS — every criterion evaluator and the verdict aggregator have unit tests that run offline with no LLM, network, or database; each spec acceptance scenario maps to a test.
- **V. Type Safety**: PASS — all models (ReadinessReport, CriterionResult) are Pydantic; full type hints; mypy strict applies.
- **VI. Observability**: PASS — each check run emits structured logs of criterion outcomes; logs contain criterion names and statuses only, never secret values or PII.
- **VII. Simplicity**: PASS — one module + one CLI script + Pydantic report models; no frameworks, no plugins, no configuration knobs beyond the existing gate commands.

No violations; Complexity Tracking remains empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-launch-readiness-check/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (/speckit.specify command)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/healthcare_support/readiness/       # NEW: deterministic readiness verification
├── __init__.py
├── models.py            # Pydantic: ReadinessReport, CriterionResult, Verdict, CriterionStatus
├── checks.py            # Criterion evaluators (tests, quality gates, deployment, security)
├── report.py            # Verdict aggregation (fail-closed) + text/JSON rendering
└── cli.py               # Argument parsing + exit codes (also exposed via scripts/)

scripts/
└── check_launch_readiness.py   # NEW: thin CLI wrapper -> healthcare_support.readiness.cli:main

tests/unit/readiness/    # NEW: offline unit tests for every evaluator + verdict logic
tests/contract/          # existing API contract tests (unchanged)

.github/workflows/ci.yml # readiness check added as a final gate job (same commands as local)
```

**Structure Decision**: Single project layout reused. The check is a backend-package module (typed, unit-testable, importable without API/agent per Principle III) with a thin script wrapper for local/CI use. No new top-level directories.

## Complexity Tracking

Empty — no constitution violations requiring justification.
