# Phase 1 Data Model: Fix Dependency Update Pipeline and Local Run

**Feature**: Fix Dependency Update Pipeline and Local Run
**Date**: 2026-10-31

This feature introduces no new application data. The entities below describe the dependency and validation artifacts that must be consistent for the fix to be complete.

## Entity: Dependency Update

The set of version-requirement changes proposed by PR #5.

| Field | Description | Validation |
|-------|-------------|------------|
| `source` | Origin of the update | Must reference PR #5 and be applied to a branch based on current `main` |
| `runtime_requirements` | Raised minimums for runtime packages | Must match PR #5's proposed changes |
| `development_requirements` | Raised minimums for development packages | Must match PR #5's proposed changes |
| `frontend_state` | Frontend dependency lock already on `main` | Must remain unchanged and installable |
| `scope` | Files affected | Must not include application source changes unless required by a compatibility finding |

**Relationships**:

- Has exactly one `Resolved Dependency State` after reconciliation.
- May produce zero or more `Compatibility Finding` records.
- Is validated by one or more `Pipeline Run` records.

## Entity: Resolved Dependency State

The complete locked resolution installed by CI, the container build, and local setup.

| Field | Description | Validation |
|-------|-------------|------------|
| `lock_source` | Repository lock artifact | Must be generated from the reconciled `Dependency Update` |
| `package_set` | All direct and transitive packages | Must satisfy every manifest requirement |
| `locked_install` | Result of a locked installation | Must succeed in CI, container build, and local setup |
| `audit_result` | Result of a strict vulnerability audit | Must report no blocking vulnerabilities |
| `reproducibility` | Whether repeated installs resolve identically | Must be deterministic for the same lock |

**Relationships**:

- Satisfies exactly one `Dependency Update`.
- Is consumed by every `Pipeline Run` and every `Local Quickstart`.
- Produces one `Compatibility Finding` when a package version breaks an existing gate.

**State transitions**:

```text
Manifest updated
  -> Lock regenerated
  -> Locked install succeeds
  -> Quality gates pass
  -> Audit passes
  -> Container passes
  -> Ready to merge
```

If any validation step fails, the state returns to `Compatibility Finding` review before the lock is accepted.

## Entity: Pipeline Run

A required automated validation attached to the pull request.

| Field | Description | Validation |
|-------|-------------|------------|
| `name` | Job identity | One of quality, frontend, dependency audit, or container |
| `trigger` | Event that starts the job | Pull request targeting `main` |
| `install_step` | Dependency installation result | Must use locked installation and succeed |
| `checks` | Job-specific gates | Must all succeed |
| `conclusion` | Overall result | Must be success before merge |

**Relationships**:

- Validates one `Resolved Dependency State`.
- One `Pipeline Run` contains all four required jobs.
- A failed job blocks merge and must not be bypassed.

**Job-level validation**:

| Job | Required checks | Success condition |
|-----|-----------------|-------------------|
| quality | Locked install, ruff lint, ruff format, mypy, offline tests, coverage | All pass; coverage >=80% |
| frontend | `npm ci`, type-checked production build | Build succeeds |
| dependency audit | Locked export, strict audit | No blocking vulnerabilities |
| container | Image build, non-root UID 10001, `/health` within 30 seconds | All pass |

## Entity: Local Quickstart

The documented developer path from clean checkout to a working local environment.

| Field | Description | Validation |
|-------|-------------|------------|
| `prerequisites` | Required runtimes and tools | Python 3.12+, uv, Node.js 22.12+, npm |
| `install_command` | Dependency installation | Uses locked installation and succeeds without a refresh request |
| `backend_command` | Service startup | Starts with default local settings and an empty model key |
| `health_check` | Liveness verification | Returns a healthy response |
| `test_command` | Offline validation | Entire offline suite passes without network or live credentials |
| `frontend_command` | Client build | Production build succeeds |
| `troubleshooting` | Recovery guidance for stale locks | Explains how to regenerate and commit the lock |

**Relationships**:

- Consumes one `Resolved Dependency State`.
- Must be reproducible from a clean checkout.
- Is validated by at least one fresh local execution before merge.

## Entity: Compatibility Finding

A record of any behavior, test, audit, or build issue caused by a proposed dependency version.

| Field | Description | Validation |
|-------|-------------|------------|
| `package` | Affected package | Must identify the package and version |
| `failure` | Observed failure | Must reference the failing command or test |
| `decision` | Resolution | One of keep, adjust version, or document deviation |
| `rationale` | Why the decision preserves requirements | Must cite the failing evidence |
| `downgrade_documented` | Whether a deviation from PR #5 is explained | Required when the version is lowered |

**Relationships**:

- May be caused by one `Dependency Update`.
- May block acceptance of a `Resolved Dependency State`.
- Produces a documented deviation when a proposed version cannot be used.

**Validation rules**:

- A downgrade without a documented rationale is invalid.
- A passing gate cannot be waived to accommodate a dependency change.
- Security findings always block acceptance regardless of other passing gates.

## No Application Schema Changes

No database, API request/response model, Pydantic domain model, or session state is added or modified by this feature. Existing contracts and security invariants remain in force.
