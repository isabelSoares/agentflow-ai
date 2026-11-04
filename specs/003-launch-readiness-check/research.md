# Research: Launch Readiness Verification

All unknowns from the Technical Context are resolved below. Format: Decision / Rationale / Alternatives considered.

## R1 — Where the readiness check lives

- **Decision**: Core logic in `src/healthcare_support/readiness/` (Pydantic models + deterministic evaluators); thin CLI wrapper at `scripts/check_launch_readiness.py` calling `healthcare_support.readiness.cli:main`.
- **Rationale**: Constitution Principle III requires business logic callable without the API or agent framework, and Principle V requires typed boundaries — both are satisfied by keeping the logic in the typed package with a one-line script wrapper. Placing it only under `scripts/` would make it untyped and untestable via the package's test suite.
- **Alternatives considered**: standalone script in `scripts/` only (rejected: untyped, harder to unit-test); a FastAPI endpoint (rejected: readiness is a maintainer/CI concern, not a runtime user interface; adds attack surface contrary to Principle I).

## R2 — How quality gates are evaluated

- **Decision**: The check shells out to the exact CI gate commands already defined in `.github/workflows/ci.yml` and `pyproject.toml`: `ruff check`, `ruff format --check`, `mypy src`, `pytest -m "not live_llm and not live_speech" --cov --cov-fail-under=80`, plus frontend `npm test` and `npm run build` when the `frontend/` directory is present. Live-LLM/live-speech tests are excluded (they need external credentials and are not go/no-go gates).
- **Rationale**: The spec's assumption says existing CI gates are authoritative; invoking the same commands guarantees local and CI verdicts are identical (SC-005) and avoids redefining "passing".
- **Alternatives considered**: re-implementing lint/type/test logic in-process (rejected: duplicates CI, drifts from the authoritative gates, violates Principle VII simplicity); parsing CI logs from GitHub Actions (rejected: requires network, fails the offline edge case).

## R3 — Security criteria implementation

- **Decision**: Three deterministic checks: (a) committed-secret scan of tracked files using pattern matching (API keys, tokens, private keys) with values redacted in output; (b) `pip-audit` on the locked dependency set for known vulnerabilities; (c) static verification that log/response paths contain no plaintext secret-answer fields, by asserting the sanitized Pydantic response models are used at the API boundary (import-level check plus grep for forbidden field names in log statements).
- **Rationale**: Constitution Principle I (never disclose, never print secrets) and Principle II (deterministic, auditable) dictate pattern/static checks, not LLM judgment. `pip-audit` is already a dev dependency, so no new tooling.
- **Alternatives considered**: dedicated secret scanners like detect-secrets/gitleaks (rejected for now: new external dependency and network fetch of baselines; pattern scan covers the committed-secret criterion offline per Principle VII, can be revisited); LLM-based review of logs (rejected: violates Principle II).

## R4 — Fail-closed semantics and verdict aggregation

- **Decision**: Each criterion yields a `CriterionResult` with status `pass | fail | unable_to_verify`. Overall verdict is `ready` only if every criterion is `pass`; any `fail` or `unable_to_verify` yields `not_ready`. Exit codes: 0 = ready, 1 = not ready, 2 = the check itself errored. All deterministic code, no LLM.
- **Rationale**: FR-007 (fail closed) and SC-003 (no false "ready" verdicts 100% of the time); exit codes make CI gating trivial.
- **Alternatives considered**: warning-only mode for `unable_to_verify` (rejected: directly violates FR-007); probabilistic/majority verdict (rejected: violates Principle II).

## R5 — Report format and redaction

- **Decision**: Two output formats from the same Pydantic `ReadinessReport`: human-readable text (grouped pass/fail/unverifiable with remediation lines) and `--json` for CI. Remediation guidance is static text per criterion plus the failing gate's name; secret/PII values are never included in any field — only file paths and pattern names.
- **Rationale**: FR-008 (no secrets/PII in report), FR-010 (readable by non-technical stakeholders), FR-006 (actionable guidance); Pydantic models enforce the no-sensitive-field contract structurally (Principle V).
- **Alternatives considered**: rich terminal UI libraries (rejected: unnecessary dependency, Principle VII); emitting raw command output on failure (rejected: raw test/lint output could contain secrets, violating FR-008 — output is summarized, not dumped).

## R6 — Offline behavior

- **Decision**: All gate commands and security scans run offline against the local checkout. Any criterion whose tool is missing or errors out is marked `unable_to_verify` and blocks the verdict. `pip-audit` runs against the local lockfile (`--requirement uv.lock` / local DB); if its vulnerability DB cannot be updated offline it is marked `unable_to_verify` rather than skipped.
- **Rationale**: Spec edge case: checks that can run offline must run; anything else is skipped-and-blocking, never silently omitted.
- **Alternatives considered**: silently skipping network-dependent checks (rejected: violates the edge case and SC-002).

## R7 — Performance budget

- **Decision**: Run gate commands sequentially with a per-criterion timeout (default 240s each), total budget 5 minutes (SC-001). Timeouts mark the criterion `unable_to_verify`.
- **Rationale**: SC-001 requires the full report in under 5 minutes; timeouts prevent hangs, which the spec's edge cases explicitly call out.
- **Alternatives considered**: parallel execution (rejected: resource contention makes timing non-deterministic and can break coverage tooling; simplicity per Principle VII).
