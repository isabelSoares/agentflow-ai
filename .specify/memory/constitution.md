# Personal Banking Support Agent Constitution

## Core Principles

### I. Security First

Sensitive customer data (name, phone number, IBAN, account details, secret answers) MUST
NEVER be exposed to unauthenticated or unauthorized users. Pre-authentication responses MUST
NOT confirm or deny whether any attribute value exists in customer records. A feature that
handles customer data is complete only after demonstrating non-disclosure under adversarial
probing.

Rationale: this is a banking assistant; a single data leak is a regulatory and
trust-destroying event, so confidentiality outranks convenience in every trade-off.

### II. Deterministic Verification

Customer identification (attribute matching), secret-answer verification and account
classification (e.g., premium vs. regular) MUST be implemented as deterministic code and
MUST NOT depend on LLM judgment. The LLM may conduct the conversation, but every security
or classification decision MUST be reproducible from the same inputs.

Rationale: LLMs are probabilistic; identity and access decisions must be exact, auditable
and unit-testable.

### III. Separation of Concerns

The API layer, agent orchestration, business logic and data access MUST remain independent
modules with explicit boundaries. Business logic MUST be callable without the API or the
agent framework, and data access MUST be replaceable without touching business rules.

Rationale: independence keeps each layer testable in isolation and lets the LLM and
orchestration stack evolve without destabilizing verified business rules.

### IV. Testability

Critical business logic — identity matching, secret-answer verification, attempt limiting,
account classification — MUST have automated tests that run without external services (no
live LLM, network or database). Every acceptance scenario in a feature specification MUST
map to at least one automated test before the implementation is considered done.

Rationale: if a rule protects money or identity, its correctness must be provable on every
change, not asserted by inspection.

### V. Type Safety

All Python code MUST use type hints. All data crossing module or process boundaries (API
requests/responses, customer records, workflow state) MUST be modeled with Pydantic models
rather than untyped dictionaries.

Rationale: typed contracts catch integration errors at development time and make layer
boundaries (Principle III) explicit and enforceable.

### VI. Observability

Workflow transitions (identification attempt, authentication success/failure, termination)
and failures MUST be logged with enough structured context to debug system behavior. Logs
MUST minimize personal data and MUST NEVER contain secret answers or full credentials in
plain text.

Rationale: a multi-agent banking workflow is opaque without transition logging, but logging
must not become a secondary channel for data exposure (Principle I).

### VII. Simplicity

Prefer the simplest maintainable solution that satisfies the requirements. Abstractions,
configuration knobs and extension points MUST be justified by a current requirement (YAGNI).
Complexity flagged in review MUST be simplified or justified in writing.

Rationale: this is a small, security-critical system; every unneeded abstraction is attack
surface and maintenance cost.

## Additional Constraints

- PII is confined to the data-access layer and redacted elsewhere; API keys and other
  credentials MUST NOT be committed to version control.
- Technology baseline per the project brief: Python with type hints and Pydantic models,
  LangGraph-style agent orchestration, FastAPI service boundary. Deviations require an
  amendment or an explicit reviewed justification.
- Quality gate: automated tests MUST pass in CI before any merge.

## Development Workflow

- All changes land via pull requests from feature branches (GitFlow-style), with logically
  scoped, well-described commits.
- Every PR review MUST verify compliance with this constitution; violations of MUST-level
  principles block the merge.
- Complexity that appears to violate Principle VII MUST be justified in the PR description.

## Governance

- This constitution supersedes conflicting practices, preferences and documentation.
- Amendments require: a written proposal in a PR, an updated Sync Impact Report, and a
  semantic version bump — MAJOR for backward-incompatible principle removals or
  redefinitions, MINOR for new principles or materially expanded sections, PATCH for
  clarifications and wording fixes.
- Compliance is reviewed on every PR; unresolved violations block the merge.

**Version**: 1.0.0 | **Ratified**: 2026-10-14 | **Last Amended**: 2026-10-14
