# Quickstart Validation: Automatic Static-Site Demo Fallback

**Feature**: `004-static-chat-fallback`
**Date**: 2026-11-09

> **Superseded (offline input UX)**: The typed demo steps below were replaced by selectable guided paths in [005-guided-demo-paths](../005-guided-demo-paths/quickstart.md). Use the 005 quickstart to validate the current offline demo; the fallback and live-preference checks here remain useful. This document is preserved as the historical record for feature 004.

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

## 1. Validate the no-backend (static-site) experience

This simulates the public static deployment where the API cannot be reached.

```bash
cd frontend
npm run build
npm run preview
```

Before opening the page, stop any backend on port 8000 (for example, confirm `curl -sS http://127.0.0.1:8000/health` fails). The preview proxy forwards `/api` to a port with nothing listening, which classifies as unavailable.

Open the preview URL (default `http://localhost:4173`) and verify:

1. No "Start a session to begin" disabled state remains; the composer is enabled.
2. An interactive conversation greeting appears automatically, without a second click.
3. A non-blocking "Offline demo mode" notice is shown; no raw `405`/`404` status text appears as a failure.
4. The "Try this scenario" guidance is visible, including the sample identity, security answer, and billing request.
5. Follow the scenario:
   - Send "Hi, I'm Lisa — my phone is +14155552671 and my date of birth is 1990-01-15."
   - When asked the security question, answer "Yoda".
   - Send "I need help with a medical bill."
6. Confirm the replies advance through identification, verification, premium classification, and routing to the Insurance and Billing Department, with telemetry updating.
7. Reload the page and confirm the demo starts cleanly again with no duplicate messages.

Expected: every step passes without a blocking error banner.

## 2. Validate the offline (network-disabled) experience

1. With the preview page loaded, switch the browser to offline mode (or disable networking).
2. Reload the page.
3. Confirm the offline demo still starts and the sample scenario completes.

Expected: the in-browser demo has no network dependency.

## 3. Validate the live-backend preference

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
2. Messages are served by the backend (session proof is active in telemetry).
3. The guidance block is still visible and the scenario works against the live API.

Expected: live is preferred and the offline notice is absent.

## 4. Validate retry from offline to live

1. Start with no backend running and load the page; confirm the offline demo starts.
2. Start the backend on port 8000.
3. Use the "Try live service" action on the page.
4. Confirm the page switches to a live session, the offline notice disappears, and the conversation restarts cleanly.

Expected: recovery without a page reload and without duplicated messages.

## 5. Validate genuine errors are not masked

1. Simulate a genuine service error (for example, point the browser at an endpoint returning `403`, or use the automated test that mocks a `403`).
2. Confirm no offline demo starts automatically and the offline notice is not shown.
3. Confirm the visitor sees a readable, actionable message and can retry.

Expected: genuine errors stay visible; only an unavailable backend triggers the fallback.

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

Expected: all frontend tests (including the updated offline fallback tests and new guidance tests) and all backend gates pass.

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Raw 405 still shown on the live site | Deployment is serving an older build | Rebuild and redeploy `frontend/dist` |
| Composer stays disabled with no notice | Startup classification not reaching the fallback | Confirm the unavailable statuses include network failure, `404`, `405`, `501`, and timeout |
| Offline demo starts for a `500` | Genuine errors are being classified as unavailable | Restrict fallback to the unavailable list in the contract |
| Guidance missing the security answer | Scenario content incomplete | Add the sample secret answer to the guidance steps |
| Live path shows the offline notice | Source state not cleared after a successful live start | Clear the offline source and notice on success |
