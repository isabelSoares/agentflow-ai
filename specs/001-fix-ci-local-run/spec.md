# Feature Specification: Fix Dependency Update Pipeline and Local Run

**Feature Branch**: `fix/ci-lockfile-local-run`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "create a new branch based on branch main to solve the pipeline issues https://github.com/isabelSoares/agentflow-ai/pull/5 and cant run locally the project"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Green Pipeline for the Dependency Update (Priority: P1)

As a maintainer, I want the dependency update proposed in PR #5 to pass every required automated check so the change can be reviewed and merged without bypassing quality gates.

**Why this priority**: The dependency update is currently blocked by failing pipeline jobs, so the update cannot land and the project keeps depending on outdated packages.

**Independent Test**: Open a pull request from the new branch against `main` and confirm that all required jobs (quality, frontend, dependency audit, and container smoke checks) complete successfully.

**Acceptance Scenarios**:

1. **Given** a branch based on `main` that includes the dependency version updates from PR #5, **When** the full pipeline runs, **Then** the dependency installation step succeeds in locked mode for every job.
2. **Given** the same branch, **When** the quality job runs, **Then** linting, formatting, type checking, offline tests, and the coverage threshold all pass.
3. **Given** the same branch, **When** the dependency audit job runs, **Then** the strict vulnerability audit completes with no blocking findings.
4. **Given** the same branch, **When** the container job runs, **Then** the image builds, runs as the non-root runtime user, and reports a healthy service.

---

### User Story 2 - Reliable Local Setup (Priority: P2)

As a developer, I want to start the backend, run the test suite, and build the frontend locally using the documented setup steps so I can work on the project without environment workarounds.

**Why this priority**: Developers currently cannot run the project locally from the updated dependency state, which blocks development, review, and reproduction of issues.

**Independent Test**: From a clean checkout of the new branch, follow the documented setup steps and verify the backend health endpoint, offline test suite, and frontend build all succeed.

**Acceptance Scenarios**:

1. **Given** a clean checkout with the documented runtimes installed, **When** the developer installs dependencies using the documented locked command, **Then** installation completes without requesting a dependency-state refresh.
2. **Given** the backend is started with the documented command and default local settings, **When** the developer requests the liveness endpoint, **Then** the service reports healthy without requiring a live model provider key.
3. **Given** the same checkout, **When** the developer runs the offline test suite, **Then** all tests pass without network access or live model credentials.
4. **Given** the frontend directory, **When** the developer installs dependencies and runs the production build, **Then** the build succeeds with the documented runtime versions.

---

### User Story 3 - Dependency Updates Stay Consistent (Priority: P3)

As a maintainer, I want dependency manifest changes and the resolved dependency state to stay in sync so future update pull requests do not fail at the first installation step.

**Why this priority**: Repeated stale-resolution failures waste review cycles and erode trust in the dependency automation.

**Independent Test**: Make a dependency range change on a scratch branch, run the locked installation and audit jobs, and confirm the pipeline detects a complete and consistent update.

**Acceptance Scenarios**:

1. **Given** a change that raises a dependency version requirement, **When** the change includes a matching resolved dependency state, **Then** locked installation succeeds in continuous integration and locally.
2. **Given** a change that raises a dependency version requirement but omits the resolved state, **When** the pipeline runs, **Then** the failure is reported clearly at the installation step.
3. **Given** the merged fix, **When** the dependency automation opens a future update, **Then** the same locked installation and audit checks remain enforced.

---

### Edge Cases

- A major dependency upgrade introduces an incompatible interface that makes existing security, routing, or API behavior fail.
- The updated dependency set introduces a blocking vulnerability finding that the previous set did not have.
- The new branch diverges from `main` because the original pull request branch was created before `main` was squashed; unrelated historical commits must not be carried over.
- A developer has an old local environment or cache; setup must succeed from a clean environment using the documented runtimes.
- Developers use a supported but different runtime minor version than continuous integration; the documented support range must still work.
- The project is installed without network access or without live model credentials; offline development and testing must remain possible.
- The frontend dependency state is already updated while the backend dependency state is not; both must be consistent before the change is considered complete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The branch MUST be created from the current `main` branch and MUST include the dependency version updates proposed by PR #5.
- **FR-002**: The dependency manifest and resolved dependency state MUST be consistent so a locked installation succeeds in every pipeline job and in local setup.
- **FR-003**: The quality pipeline MUST pass linting, formatting verification, static type checking, the offline test suite, and the project's coverage threshold.
- **FR-004**: The frontend pipeline MUST install dependencies from its lock state and complete the type-checked production build.
- **FR-005**: The dependency audit MUST run against the resolved dependency state and MUST report no blocking vulnerabilities.
- **FR-006**: The container pipeline MUST build the image, run it as the expected non-root user, and pass the existing health check.
- **FR-007**: A developer MUST be able to install dependencies, start the backend, verify its health, run the offline tests, and build the frontend locally using only the documented setup steps.
- **FR-008**: Offline development and testing MUST NOT require a live model provider key or network access beyond package installation.
- **FR-009**: If a proposed dependency version is incompatible with existing behavior, the change MUST retain the closest compatible version set and document the deviation from PR #5.
- **FR-010**: Documentation MUST reflect any change to supported runtimes, setup commands, dependency constraints, or local troubleshooting steps.
- **FR-011**: The fix MUST preserve existing security guarantees, including deterministic identity verification, sanitized responses, and non-disclosure of sensitive patient data.
- **FR-012**: The change MUST NOT weaken or remove existing pipeline gates, security checks, container hardening, or automated contract tests.
- **FR-013**: Future dependency updates MUST continue to be validated by locked installation and strict audit checks.

### Key Entities *(include if feature involves data)*

- **Dependency Update**: The set of raised version requirements from PR #5, including runtime, development, and frontend packages.
- **Resolved Dependency State**: The complete locked resolution that all environments install from and that the audit inspects.
- **Pipeline Run**: The collection of required automated checks attached to a pull request, comprising quality, frontend, dependency audit, and container jobs.
- **Local Quickstart**: The documented sequence of installation, startup, health verification, test, and build steps for a developer workstation.
- **Compatibility Finding**: Any behavior, test, security, or vulnerability issue caused by a proposed dependency version, with the resulting decision to keep, adjust, or document the version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of required pipeline jobs pass on the new branch, with zero locked-installation failures.
- **SC-002**: A developer can go from a clean checkout to a healthy backend in under 10 minutes using only documented commands and offline-safe settings.
- **SC-003**: 100% of the existing offline automated test suite passes, and the project meets or exceeds its 80% coverage threshold.
- **SC-004**: The strict dependency audit reports zero blocking vulnerabilities for the resolved dependency state.
- **SC-005**: The frontend production build completes successfully with the documented Node.js version.
- **SC-006**: The built container reaches a healthy state within the existing 30-second health-check window and runs as the expected non-root user.
- **SC-007**: No existing contract, security, or architecture documentation test is removed, skipped, or weakened by the change.
- **SC-008**: A repeat dependency update that changes version requirements but not the resolved state fails clearly at the installation step rather than later in the pipeline.

## Assumptions

- `main` is the correct base and contains the current rebranded application, frontend, workflows, and tests; the new branch supersedes the original PR #5 branch rather than updating that branch in place.
- PR #5's intent is to adopt the newest proposed dependency versions; if an upgrade breaks required behavior, the closest compatible version set is acceptable when the deviation is documented.
- CI runs on Python 3.13 and Node.js 24, while the documented local support range (Python 3.12+ and Node.js 22.12+) must remain valid.
- An empty model provider key is valid for offline startup and tests; only a fully manual live conversation needs a real provider key.
- The frontend dependency updates already present on `main` are correct and do not need to be reverted.
- Package installation may require network access; running the application and the offline test suite must not.
- Existing pipeline stages and contract tests are the source of truth and should be preserved rather than replaced.
