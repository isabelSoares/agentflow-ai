# Quickstart Validation: Guided Demo Paths

**Feature**: `005-guided-demo-paths`
**Date**: 2026-11-09

Use this guide after implementation to prove the feature works end-to-end. It references [spec.md](./spec.md), [data-model.md](./data-model.md), and the contracts in [contracts/](./contracts) instead of duplicating them.

## Prerequisites

- Node.js 22.12+ and npm (Node 24 is used in CI)
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) for the live-backend path
- A terminal in the repository root
- No live LLM key required; the deterministic adapters and in-browser demo are sufficient

## Setup

```bash
cd frontend
npm ci
cd ..
```

## 1. Validate guided paths on the static (no-backend) build

This simulates the public static deployment where the API cannot be reached.

```bash
cd frontend
npm run build
npm run preview
```

Before opening the page, stop any backend on port 8000 (for example, confirm `curl -sS http://127.0.0.1:8000/health` fails). The preview proxy forwards `/api` to a port with nothing listening, which classifies as unavailable.

Open the preview URL (default `http://localhost:4173`) and verify:

1. An interactive session starts automatically and the non-blocking "Offline demo mode" notice is shown.
2. No editable message composer is required; the demo offers named guided paths instead.
3. Every path shows a title and a one-line description of what it demonstrates.
4. Selecting a path starts a clean conversation and shows the first prepared message as read-only.
5. "Next step" sends the prepared message unchanged and the agent reply updates the conversation and telemetry.
6. Progress shows "Step N of M" and no raw status codes appear.
7. Completing a path shows a plain-language outcome and offers restart or choose-another-path.
8. Switching paths midway clears previous messages, telemetry, and step progress.

Expected: every path completes with zero typing and no blocking error banner.

## 2. Validate required path coverage

Run each path and confirm distinct outcomes per [contracts/guided-path-data.md](./contracts/guided-path-data.md):

1. **Premium support journey** reaches authenticated, premium classification, and routing to a department.
2. **Regular support journey** reaches authenticated, regular classification, and Standard Patient Support.
3. **Clarification journey** ends with a request for more identifying detail.
4. **Failed verification journey** ends terminated as a non-client.

Expected: the set collectively demonstrates success, classification, routing, clarification, and guardrail termination.

## 3. Validate the live-backend experience is unchanged

```bash
uv sync --locked
cp .env.example .env
uv run uvicorn healthcare_support.api.app:create_app --factory --port 8000
```

In a second terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` and verify:

1. A live session starts automatically and no "Offline demo mode" notice appears.
2. The editable free-text composer is available and messages are served by the backend.
3. Guided-path-only restrictions do not replace live free-text input.

Expected: live behavior is unchanged and guided paths are absent.

## 4. Validate offline (network-disabled) operation

1. With the preview page loaded, switch the browser to offline mode (or disable networking).
2. Reload the page.
3. Confirm the guided paths appear and every path completes.

Expected: the guided demo has no network dependency.

## 5. Validate accessibility

1. Navigate the demo using only the keyboard: select a path, advance steps, restart, and choose another path.
2. Use a screen reader (or the accessibility assertions in the automated tests) to confirm:
   - The path group and each path control are labelled.
   - Step progress and outcome changes are announced through a polite live region.
   - The prepared message is readable before it is sent.
3. Confirm no state is conveyed by color alone.

Expected: the full guided walkthrough is operable and understandable without a mouse.

## 6. Run automated checks

```bash
cd frontend
npm test
npm run build
cd ..

uv run pytest -m "not live_llm and not live_speech" \
  --cov=src/healthcare_support --cov-branch --cov-report=term-missing --cov-fail-under=80
uv run mypy src
uv run ruff check src tests
uv run ruff format --check src tests
```

Expected: all frontend tests (path definitions, guided UI flows, offline fallback, live preference, accessibility) and all backend gates pass.

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Editable composer still shown offline | Guided mode not wired to the offline source | Show guided UI whenever `source === 'offline'` |
| A path step produces an unexpected reply | Prepared message does not match the engine's expected input | Adjust the step message or assert the correct turn in tests |
| Path switching leaves old messages | Session/messages/telemetry not reset on selection | Reset to a fresh offline session and greeting on every selection |
| Outcome text disagrees with telemetry | Outcome hand-authored separately from the turn | Derive the outcome from the final offline turn |
| Guided paths appear against a live backend | Mode condition too broad | Gate guided UI on the offline source only |
| Raw status code appears in the demo | Old error-banner path leaking into guided mode | Keep the non-blocking offline notice and suppress raw codes |
