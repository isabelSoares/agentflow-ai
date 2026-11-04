# CLI Contract: check_launch_readiness

The launch readiness check is exposed as a command-line tool (the interface users and CI interact with). There is no HTTP API for this feature.

## Command

```text
uv run python scripts/check_launch_readiness.py [--json] [--timeout SECONDS]
```

## Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--json` | flag | off | Emit the report as JSON instead of human-readable text |
| `--timeout` | int | 240 | Per-criterion timeout in seconds; a timed-out criterion is `unable_to_verify` |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | verdict = `ready` (all criteria passed) |
| 1 | verdict = `not_ready` (any criterion failed or could not be verified) |
| 2 | the check itself errored (e.g., invalid arguments) |

## Output (text mode)

Human-readable report grouped by category (`tests`, `quality-gates`, `deployment`, `security`), each criterion line showing status and remediation, ending with the overall verdict line:

```text
LAUNCH READINESS: NOT READY
```

## Output (JSON mode, `--json`)

Serialized `ReadinessReport` per [data-model.md](../data-model.md):

```json
{
  "verdict": "not_ready",
  "run_at": "2026-11-04T12:00:00Z",
  "results": [
    {
      "name": "offline-tests",
      "category": "tests",
      "status": "fail",
      "details": "3 tests failed in tests/unit/...",
      "remediation": "Run `uv run pytest -m \"not live_llm and not live_speech\"` and fix the failing tests."
    }
  ]
}
```

## Guarantees

- Output NEVER contains secret values, credentials, or patient PII — only criterion names, statuses, file paths, and remediation text (FR-008).
- Every criterion in the catalog appears exactly once in `results`; none are silently skipped (SC-002).
- Any `fail` or `unable_to_verify` status implies verdict `not_ready` and exit code 1 (fail-closed, FR-007 / SC-003).
- Identical criteria and verdict logic locally and in CI (FR-009 / SC-005).

## CI integration

Add a final job to `.github/workflows/ci.yml` that runs the same command on `main` pushes; exit code 1 fails the workflow.
