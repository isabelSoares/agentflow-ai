# Quickstart Validation: Fix Dependency Update Pipeline and Local Run

**Feature**: Fix Dependency Update Pipeline and Local Run
**Date**: 2026-10-31
**Contract**: [contracts/ci-local-run-contract.md](./contracts/ci-local-run-contract.md)

Use this guide to prove the fix works from a clean checkout and to confirm the pull request pipeline is green. Commands run from the repository root unless stated otherwise.

## Prerequisites

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Node.js 22.12 or newer and npm
- Docker available only if you want to validate the container locally

## 1. Confirm the dependency state is consistent

```bash
uv lock --check
uv sync --locked
```

**Expected**: Both commands succeed. `uv sync --locked` must not report that `uv.lock` needs to be updated. The environment should install the reconciled dependency set described in [data-model.md](./data-model.md).

## 2. Run the offline quality gates

```bash
uv run pytest -m "not live_llm and not live_speech" \
  --cov=src/banking_support \
  --cov-branch \
  --cov-report=term-missing \
  --cov-fail-under=80

uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
```

**Expected**:

- All selected tests pass. The pre-fix baseline is 509 passed and 9 deselected.
- Coverage meets or exceeds 80%. The pre-fix baseline is 91.38%.
- Ruff reports no violations and all files are formatted.
- mypy reports no issues.

## 3. Run the strict dependency audit

```bash
uv export --locked --format requirements.txt --no-editable --no-emit-project \
  --output-file /tmp/agentflow-ai-requirements.txt
uv run pip-audit --strict -r /tmp/agentflow-ai-requirements.txt
```

**Expected**: The export succeeds and the audit reports no known vulnerabilities.

## 4. Verify backend startup and health

```bash
cp .env.example .env
uv run uvicorn banking_support.api.app:create_app --factory --port 8000
```

In a second terminal:

```bash
curl -fsS http://localhost:8000/health
```

**Expected**: The service starts with an empty `GROQ_API_KEY` and the health request succeeds. Stop the server with `Ctrl+C` after verification.

## 5. Verify the frontend build

```bash
cd frontend
npm ci
npm run build
```

**Expected**: Installation completes with no blocking vulnerabilities and the type-checked production build succeeds.

## 6. Optional: verify the container

Run only when Docker is available:

```bash
docker build -t agentflow-ai:ci .
docker run --rm agentflow-ai:ci id -u
docker run -d --name agentflow-ai-local -p 8000:8000 agentflow-ai:ci
curl -fsS http://127.0.0.1:8000/health
docker rm -f agentflow-ai-local
```

**Expected**: `id -u` returns `10001`, the health check succeeds within 30 seconds, and the container starts without a `.env` file or test suite inside the image.

## 7. Validate the remote pipeline

Push the branch and open a pull request against `main`, or use the GitHub CLI:

```bash
git push -u origin fix/ci-lockfile-local-run
gh pr create --base main --head fix/ci-lockfile-local-run
```

**Expected**: The quality, frontend, dependency audit, and container jobs all pass. No job may be skipped, disabled, or bypassed. Once green, the original PR #5 can be closed as superseded.

## Failure Recovery

If `uv sync --locked` reports a stale lock:

```bash
uv lock
uv sync --locked
```

Commit the regenerated `uv.lock` together with the manifest change. If a dependency version fails a quality gate, record the failure in a compatibility finding, select the closest compatible version, and document the deviation from PR #5.

## Acceptance Checklist

- [ ] Locked installation succeeds locally and in CI.
- [ ] All offline tests pass and coverage is at least 80%.
- [ ] Ruff and mypy pass.
- [ ] Strict dependency audit reports no blocking findings.
- [ ] Backend health check succeeds without a live model key.
- [ ] Frontend install and production build succeed.
- [ ] Container job passes, including non-root user and health check.
- [ ] Documentation explains how to recover from a stale lock.
- [ ] No pipeline gate or contract test is weakened.
