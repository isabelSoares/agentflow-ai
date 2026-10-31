# Contract: CI and Local Run

**Feature**: Fix Dependency Update Pipeline and Local Run
**Date**: 2026-10-31

This contract defines the observable behavior the fix must provide. It does not define application source changes. Existing HTTP API, session, security, and frontend contracts are unchanged.

## 1. Dependency Installation Contract

| Rule | Requirement |
|------|-------------|
| Locked install | `uv sync --locked` MUST succeed in a clean environment |
| Manifest consistency | Every requirement in `pyproject.toml` MUST be satisfied by `uv.lock` |
| Stale lock behavior | A manifest change without a matching lock MUST fail at installation, not later in the pipeline |
| Offline use | After installation, application startup and the offline test suite MUST NOT require network access or a live model key |
| Frontend install | `npm ci` in `frontend/` MUST succeed from `frontend/package-lock.json` |

## 2. Pipeline Contract

A pull request targeting `main` MUST expose these jobs, and all MUST conclude successfully before merge.

### 2.1 Quality

| Step | Command | Expected outcome |
|------|---------|------------------|
| Install | `uv sync --locked` | Success, no lock refresh requested |
| Lint | `uv run ruff check src tests` | No violations |
| Format | `uv run ruff format --check src tests` | All files already formatted |
| Types | `uv run mypy src` | No type errors |
| Tests | `uv run pytest -m "not live_llm and not live_speech"` with coverage flags | All selected tests pass |
| Coverage | `--cov-fail-under=80` | Coverage >=80% |

### 2.2 Frontend

| Step | Command | Expected outcome |
|------|---------|------------------|
| Install | `npm ci` in `frontend/` | Success, zero blocking vulnerabilities |
| Build | `npm run build` in `frontend/` | Type-checked production build succeeds |

### 2.3 Dependency Audit

| Step | Command | Expected outcome |
|------|---------|------------------|
| Install | `uv sync --locked` | Success |
| Export | `uv export --locked --format requirements.txt --no-editable --no-emit-project --output-file <file>` | Export succeeds |
| Audit | `uv run pip-audit --strict -r <file>` | No known blocking vulnerabilities |

### 2.4 Container

| Step | Expected outcome |
|------|------------------|
| Image build | `docker build -t agentflow-ai:ci .` succeeds |
| Non-root runtime | `id -u` returns `10001` |
| Runtime content | `/app/tests` and `/app/.env` are absent |
| Health | `curl -fsS http://127.0.0.1:8000/health` succeeds within 30 seconds |

## 3. Local Run Contract

These are the documented developer-facing commands. Paths are relative to the repository root unless stated otherwise.

| Scenario | Command | Expected outcome |
|----------|---------|------------------|
| Install backend | `uv sync --locked` | Success without a stale-lock error |
| Start backend | `uv run uvicorn banking_support.api.app:create_app --factory --port 8000` | Service starts with an empty `GROQ_API_KEY` |
| Health | `curl -fsS http://localhost:8000/health` | Healthy response |
| Offline tests | `uv run pytest -m "not live_llm and not live_speech"` | All offline tests pass |
| Lint and types | `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy src` | All pass |
| Frontend install | `npm ci` in `frontend/` | Success |
| Frontend build | `npm run build` in `frontend/` | Success with Node.js 22.12+ |

## 4. Documentation Contract

The repository MUST document, in the setup or dependency-maintenance guidance:

1. That dependency-version changes require a regenerated lock.
2. The exact recovery command when a locked installation reports a stale lock.
3. That the regeneration must be committed with the manifest change.

## 5. Compatibility Contract

- No required pipeline job may be removed, disabled, or changed to an unlocked install.
- No existing contract test may be weakened, skipped, or deleted.
- If a proposed version breaks a gate, the closest compatible version MUST be selected and the deviation from PR #5 documented.
- Security findings block acceptance regardless of other passing gates.

## 6. Out of Scope

- Changing application behavior, API schemas, authentication, or guardrails.
- Replacing the package manager, CI provider, or frontend toolchain.
- Adding new runtime dependencies for the fix.
- Changing the container runtime user or health-check design.
