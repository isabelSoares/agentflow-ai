# Phase 0 Research: Fix Dependency Update Pipeline and Local Run

**Feature**: Fix Dependency Update Pipeline and Local Run
**Date**: 2026-10-31
**Spec**: [spec.md](./spec.md)

## Research Questions

1. Why do the PR #5 pipeline jobs fail?
2. Why can the updated project not be installed or run locally?
3. Does the latest dependency set remain compatible with the application and its security tests?
4. What is the smallest reliable fix, and how should it be validated?
5. How should the branch relate to PR #5 and to current `main`?

## Findings

### 1. Root cause of the pipeline failures

**Decision**: Treat the stale resolved dependency state as the single root cause.

**Evidence**:

- PR #5 changes only `pyproject.toml` (18 additions, 18 deletions); `uv.lock` is not part of the pull request.
- The CI `quality` job fails at `uv sync --locked` with:
  `error: The lockfile at uv.lock` needs to be updated, but `--locked` was provided.
- The Dependency Audit job fails at the same command for the same reason.
- The Container job fails while building the image because `uv sync --locked --no-dev --no-install-project` hits the same stale-lock error.
- The frontend job is not the source of failure; it already installs from an up-to-date `frontend/package-lock.json`.

**Rationale**: Locked installation is intentionally strict. A manifest change without a matching lock is therefore rejected before linting, tests, audit, or container start can run.

**Alternatives considered**:

- Replace `--locked` with an unlocked install in CI: rejected because it hides manifest/lock drift and makes builds non-reproducible.
- Add `--refresh` or delete the lock in CI: rejected for the same reason and because the lock is the audit input.
- Update only `uv.lock` without applying PR #5's manifest: rejected because the specification requires carrying the proposed dependency updates forward.

### 2. Root cause of the local installation problem

**Decision**: The local failure is the same manifest/lock drift when the PR #5 state is checked out or applied locally.

**Evidence**:

- On current `main`, `uv sync --locked`, the 509-test offline suite, ruff, format check, mypy, backend startup, `/health`, and the frontend build all succeed.
- On the PR #5 dependency state, `uv sync --locked` rejects the stale lock before the developer can start the service.
- The README quickstart depends on `uv sync --locked`, so a stale lock blocks the documented path even though the application code is healthy.

**Rationale**: Fixing the lock once resolves both the pipeline and the documented local setup path; no runtime workaround or alternate command is needed.

**Alternatives considered**:

- Change the README to instruct `uv sync` without `--locked`: rejected because it weakens reproducibility and conflicts with the CI contract.
- Pin older versions to match the existing lock: rejected because the newer set passes all gates and PR #5's intent is to adopt the updates.
- Ask developers to run `uv lock` manually after every update with no documentation: rejected because it caused this exact failure.

### 3. Compatibility of the proposed dependency set

**Decision**: Adopt PR #5's manifest updates and the resulting latest compatible resolution; no runtime code changes are required.

**Probe method**: Created a detached worktree from current `main`, applied PR #5's `pyproject.toml` diff, ran `uv lock` and `uv sync --locked`, then ran every quality gate and the frontend build in that clean worktree.

**Resolved versions after regeneration**:

| Package | Main lock | Resolved after PR #5 manifest |
|---------|-----------|-------------------------------|
| fastapi | 0.143.1 | 0.162.0 |
| langgraph | 1.2.15 | 1.2.19 |
| langchain-openai | 1.7.2 | 1.7.3 |
| openai | 3.31.0 | 3.42.0 |
| pydantic | 2.14.1 | 2.14.1 |
| pydantic-settings | 2.16.0 | 2.16.2 |
| phonenumbers | 9.0.41 | 9.0.42 |
| schwifty | 2026.7.3 | 2026.10.1 |
| ruff | 0.17.0 | 0.17.3 |
| uvicorn | 0.54.0 | 0.54.0 |
| pytest | 9.1.1 | 9.1.1 |
| pytest-cov | 7.1.0 | 7.1.0 |
| mypy | 2.4.0 | 2.4.0 |
| pip-audit | 2.10.1 | 2.10.1 |

**Probe results**:

- `uv sync --locked`: success.
- Offline suite: 509 passed, 9 deselected.
- Coverage: 91.38%, above the required 80%.
- `ruff check src tests`: all checks passed.
- `ruff format --check src tests`: 124 files already formatted.
- `mypy src`: no issues in 61 source files.
- `pip-audit --strict`: no known vulnerabilities.
- Frontend `npm ci` and `npm run build`: success with Vite 8.3.5.
- Container validation was not executed in the probe because Docker was unavailable in the research environment; the Dockerfile and container workflow are unchanged, so the plan keeps the existing container job as the authoritative validation.

**Rationale**: Every existing quality, security, typing, audit, and frontend gate passes with the newer resolved set, so adding compatibility shims or downgrading would add unjustified complexity and violate the simplicity principle.

**Alternatives considered**:

- Pin the dependency set to the previous lock and ignore the PR: rejected because it does not satisfy the requested update.
- Introduce code changes for unverified incompatibilities: rejected because no incompatibility was observed.
- Move to a different package manager: rejected as out of scope and unnecessarily disruptive.

### 4. Validation strategy

**Decision**: Use the existing pipeline as the authoritative acceptance mechanism, preceded by the same commands locally.

**Validation sequence**:

1. `uv lock` after applying the manifest change, then `uv sync --locked`.
2. `uv run pytest -m "not live_llm and not live_speech"` with the same coverage flags as CI.
3. `uv run ruff check src tests`, `uv run ruff format --check src tests`, and `uv run mypy src`.
4. `uv export --locked ...` followed by `uv run pip-audit --strict -r ...`.
5. Backend startup with an empty model key and a successful `/health` request.
6. Frontend `npm ci` and `npm run build`.
7. Push the branch and confirm the CI, Dependency Audit, and Container workflows all pass on the pull request.

**Rationale**: The pipeline already encodes the project's quality contract, including coverage, strict audit, non-root container runtime, and health checks. Running the same commands locally catches failures before the remote round trip.

**Alternatives considered**:

- Rely only on manual checks: rejected because the specification requires pipeline evidence.
- Add new CI jobs: rejected because the existing jobs already cover the failure and the constitution favors simplicity.

### 5. Branch and history strategy

**Decision**: Create a fresh branch from current `main`, apply only PR #5's `pyproject.toml` changes, regenerate `uv.lock`, and supersede PR #5.

**Evidence**:

- Current `main` is a single squashed import commit containing the rebrand, frontend, workflows, and tests.
- PR #5's branch is based on older, pre-squash commits and contains unrelated historical commits.
- Cherry-picking or merging the old branch would reintroduce history that `main` no longer has.

**Rationale**: A fresh branch keeps the change reviewable, avoids unrelated history, and still satisfies the requirement to include PR #5's dependency updates.

**Alternatives considered**:

- Force-update PR #5's branch: rejected because it mixes unrelated history and is harder to review.
- Merge `main` into PR #5's branch: rejected because the resulting diff still carries obsolete history and conflicts.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| A newer transitive dependency changes behavior in an untested path | Low | Medium | Run the full offline suite, contract tests, strict audit, and container smoke job before merge. |
| A vulnerability is disclosed in the new resolved set later | Medium | Medium | Keep the scheduled strict audit workflow enabled; update the lock when it fails. |
| Future Dependabot PRs again update only the manifest | Medium | Medium | Document that dependency changes must include a regenerated lock and keep the `--locked` gates unchanged. |
| Docker validation differs from the local probe | Low | Medium | Treat the Container workflow as a required gate; do not merge until it passes. |
| A developer uses a runtime outside the documented range | Low | Low | Keep Python 3.12+ and Node.js 22.12+ documented and validate CI on the production versions. |

## Unresolved Clarifications

None. All technical unknowns were resolved by the probe and by the existing workflow contracts.
