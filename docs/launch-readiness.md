# Launch Readiness Check

A single command verifies whether the project is ready to launch. It evaluates
every go/no-go criterion — offline tests, lint/format/type/coverage gates,
frontend tests and build, deployment configuration, and security posture — and
prints a fail-closed verdict with per-criterion remediation guidance.

## Run it

```bash
uv run python scripts/check_launch_readiness.py           # human-readable report
uv run python scripts/check_launch_readiness.py --json    # machine-readable report
```

Exit codes: `0` = ready to launch, `1` = not ready, `2` = the check itself errored.

Any failed or unverifiable criterion blocks launch (fail-closed). The report
never prints secret values, credentials, or patient PII. The same command runs
in CI as the `launch-readiness` job in `.github/workflows/ci.yml`.

## Validation guide

See [specs/003-launch-readiness-check/quickstart.md](../specs/003-launch-readiness-check/quickstart.md)
for end-to-end validation scenarios, and
[specs/003-launch-readiness-check/contracts/cli-schema.md](../specs/003-launch-readiness-check/contracts/cli-schema.md)
for the full CLI contract.
