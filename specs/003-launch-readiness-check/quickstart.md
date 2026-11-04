# Quickstart: Launch Readiness Verification

Runnable validation guide proving the feature works end-to-end. Prerequisites, commands, expected outcomes. Contracts and data model details: [contracts/cli-schema.md](contracts/cli-schema.md), [data-model.md](../data-model.md).

## Prerequisites

- Repo root checked out on branch `003-launch-readiness-check`
- `uv sync --locked` completed (dev dependencies installed)
- `frontend/node_modules` installed (`npm ci` in `frontend/`) for frontend criteria

## Scenario 1 — Healthy project yields "ready"

```bash
uv run python scripts/check_launch_readiness.py
```

Expected: exit code 0; every criterion line shows `pass`; final line `LAUNCH READINESS: READY`.

## Scenario 2 — Failing gate yields "not ready" with remediation

```bash
# introduce a deliberate failure, e.g. break one assertion in a unit test
uv run python scripts/check_launch_readiness.py
```

Expected: exit code 1; the `offline-tests` criterion shows `fail` with remediation naming the pytest command; final line `LAUNCH READINESS: NOT READY`. Revert the deliberate failure afterwards.

## Scenario 3 — JSON output for CI

```bash
uv run python scripts/check_launch_readiness.py --json
```

Expected: exit code 0 or 1; stdout is a single JSON object matching the `ReadinessReport` schema (verdict, run_at, results[]) with a `remediation` field on every non-passing criterion.

## Scenario 4 — Fail-closed on missing tool

```bash
# run with a PATH that hides ruff, or set --timeout 0
uv run python scripts/check_launch_readiness.py --timeout 0
```

Expected: affected criteria marked `unable_to_verify`, verdict `not_ready`, exit code 1 — never silently passed.

## Scenario 5 — Security violation blocks launch without leaking the secret

```bash
# add a fake AWS-style key (AKIA + 16 chars, split so docs don't self-flag) to a tracked file
echo 'AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLF"' >> some_tracked_file.py
uv run python scripts/check_launch_readiness.py
```

Expected: `committed-secrets` criterion `fail`; the report names the file and pattern but does NOT print the key value; verdict `not_ready`, exit code 1.

## Scenario 6 — Unit tests for the readiness module (offline)

```bash
uv run pytest tests/unit/readiness/ -m "not live_llm and not live_speech"
```

Expected: all pass with no network, LLM, or database (constitution Principle IV); every acceptance scenario in spec.md maps to at least one of these tests.

## CI validation

Push the branch and confirm the CI workflow's readiness job runs the same command and fails the build on exit code 1.
