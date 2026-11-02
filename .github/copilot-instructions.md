# AgentFlow AI — repository instructions

AgentFlow AI is a secure multi-agent patient-support platform built with Python,
FastAPI, LangGraph, React, and TypeScript. The repository currently ships a
healthcare-support demo adapter (`src/healthcare_support`) that exercises
identity verification, authorization, classification, and routing.

## Architecture invariants

- Security decisions are deterministic. The LLM is advisory only and must never
  grant access, change classification, or select an unauthorized destination.
- Identity matching requires at least two trusted attributes: name, phone number,
  and date of birth.
- Session ownership, guardrails, PII redaction, and support routing must not be
  weakened.
- Never log or return PII, secret answers, credentials, or internal prompts.
- Keep the LangGraph node IDs and documented workflow shape stable unless a task
  explicitly changes the workflow.

## Commands

Backend:

```bash
uv sync --locked
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest -m "not live_llm and not live_speech" \
  --cov=src/healthcare_support --cov-branch \
  --cov-report=term-missing --cov-fail-under=80
```

Frontend:

```bash
cd frontend
npm ci
npm test
npm run build
```

Quickstart/evaluation helpers:

```bash
uv run python scripts/validate_quickstart.py
uv run python scripts/evaluate_extraction.py --dataset tests/evaluation/golden_extraction.json
```

## Conventions

- Python 3.12+, Ruff formatting with double quotes, strict mypy.
- Keep the existing layering: `domain` (pure models), `core` (deterministic
  logic), `agents` (LLM + LangGraph), `data` (repositories/seed), `api`
  (FastAPI), `voice` (STT/TTS adapters), `observability`, `resilience`.
- Add or update tests whenever behavior changes. Do not weaken existing
  contract, security, or guardrail tests.
- Update README and `docs/` when commands, architecture, or user-facing copy
  changes.
- Healthcare glossary: Patient, PatientClassification (premium/regular/
  non-patient), date of birth, appointment, prescription refill, coverage,
  claim, specialist referral, insurance and billing.
- Do not leave banking or IBAN terminology in active source, tests, docs, or
  frontend copy.

## Change discipline

- Work in one scoped phase per branch/PR.
- Run the full backend and frontend gates before opening a PR.
- Report any remaining `banking`, `iban`, or `schwifty` references.
- Do not commit secrets, force-push, or merge without explicit approval.
