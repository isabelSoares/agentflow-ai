# Data Model: Launch Readiness Verification

All models are Pydantic (constitution Principle V) and contain no secret or PII fields by construction (Principle I). See [contracts/cli-schema.md](contracts/cli-schema.md) for how reports are emitted.

## Verdict (enum)

- `ready` — every criterion passed; safe to launch.
- `not_ready` — at least one criterion failed or could not be verified (fail-closed, FR-007).

## CriterionStatus (enum)

- `pass` — criterion verified successfully.
- `fail` — criterion evaluated and violated.
- `unable_to_verify` — tool missing, timed out, or errored; treated as blocking.

## CriterionResult

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Criterion identifier, e.g. `"offline-tests"`, `"coverage-gate"`, `"committed-secrets"` |
| `category` | `str` | One of `tests`, `quality-gates`, `deployment`, `security` |
| `status` | `CriterionStatus` | Outcome of the evaluation |
| `details` | `str` | Human-readable summary; MUST NOT contain secret values or PII (FR-008) |
| `remediation` | `str` | Actionable fix guidance; empty when status is `pass` (FR-006) |

Validation rules:
- `remediation` MUST be non-empty when `status != pass`.
- `details` MUST be non-empty.

## ReadinessReport

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | `Verdict` | Derived: `ready` iff all results are `pass`, else `not_ready` |
| `run_at` | `datetime` | UTC timestamp of the run |
| `results` | `list[CriterionResult]` | One entry per go/no-go criterion; zero silently skipped (SC-002) |

Derived invariants:
- `verdict == ready` ⟺ every `results[].status == pass`.
- Report is immutable after construction; verdict computed by a deterministic function, never by LLM (Principle II).

## Criterion catalog (fixed set evaluated every run)

| name | category | Evaluates |
|------|----------|-----------|
| `offline-tests` | tests | `pytest -m "not live_llm and not live_speech"` |
| `frontend-tests` | tests | `npm test` in `frontend/` (skipped-and-blocking if no frontend) |
| `lint` | quality-gates | `ruff check src tests` |
| `format` | quality-gates | `ruff format --check src tests` |
| `type-check` | quality-gates | `mypy src` (strict) |
| `coverage-gate` | quality-gates | coverage `--fail-under=80` from the test run |
| `frontend-build` | quality-gates | `npm run build` in `frontend/` |
| `deployment-config` | deployment | required env vars present (names only, values never printed), Dockerfile present, CI workflows present |
| `dependency-audit` | security | `pip-audit` against locked dependencies |
| `committed-secrets` | security | pattern scan of tracked files for keys/tokens/private keys, values redacted |
| `no-pii-in-boundary` | security | API responses use sanitized models; no secret-answer fields in log statements |

State transitions: none — each run is stateless; a new run produces a new `ReadinessReport`.
