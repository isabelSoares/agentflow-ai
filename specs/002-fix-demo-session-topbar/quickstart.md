# Quickstart Validation: Demo Session Recovery & Rounded Highlighted Topbar

**Feature**: `002-fix-demo-session-topbar`
**Date**: 2026-11-01

Use this guide after implementation to prove the feature works end-to-end. It references the contracts in [contracts/](./contracts) and the entities in [data-model.md](./data-model.md) instead of duplicating them.

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 22.12+ and npm
- A terminal in the repository root
- No live LLM key required for these checks; the offline adapters are sufficient

## Setup

```bash
uv sync --locked
cd frontend
npm ci
cd ..
```

## 1. Start the backend

```bash
cp .env.example .env
uv run uvicorn healthcare_support.api.app:create_app --factory --port 8000
```

Confirm liveness in a second terminal:

```bash
curl -fsS http://localhost:8000/health
```

Expected: `{"status":"ok"}`

## 2. Validate local development (session recovery)

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 and verify:

1. No "Request failed with status 404" banner appears.
2. The composer is enabled and its placeholder is "Ask a support question...".
3. The page shows the assistant greeting instead of "Start a session to begin".
4. The network panel shows the create request going to `/api/conversations` and returning `201`.
5. Sending a suggestion appends the visitor message and an assistant reply.
6. Selecting "Reset session" clears telemetry and restores the greeting.

Expected: every step passes without a 404 and without a technical status-code error.

## 3. Validate failure and retry

1. Stop the backend.
2. Reload http://localhost:5173.
3. Confirm the error banner explains that the demo service cannot be reached and that a retry is possible.
4. Confirm the "Start session" button is enabled and the composer is disabled.
5. Restart the backend and select "Start session".
6. Confirm the session becomes active and the composer is enabled.

Expected: a recoverable error state, no bare 404, and a successful retry.

## 4. Validate the production build path

```bash
cd frontend
npm run build
npm run preview
```

Open the preview URL and repeat the session checks from step 2.

Expected: the built client uses `/api`, the preview proxy forwards to the backend, and the session starts successfully.

For a direct-origin deployment instead:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run build
npm run preview
```

Add the preview origin to `CORS_ALLOWED_ORIGINS` before using this override.

## 5. Validate the topbar presentation

Use browser responsive mode at 1440px, 768px, and 320px widths and verify:

- Visible space remains between the topbar and both viewport edges.
- All four corners are rounded at every width.
- The accent border and/or glow distinguishes the topbar from the background.
- The page does not scroll horizontally at any tested width.
- Scrolling keeps the topbar sticky with a small gap above it and no content hidden underneath.
- At mobile widths, the brand and navigation stack without clipping.
- Tab through the brand and navigation links; focus rings remain clearly visible and text stays readable.

Expected: every observation matches [contracts/ui-contract.md](./contracts/ui-contract.md).

## 6. Run automated checks

```bash
uv run pytest tests/contract/test_frontend_demo_contract.py -q
cd frontend && npm test
cd .. && npm --prefix frontend run build
uv run pytest -m "not live_llm and not live_speech" \
  --cov=src/healthcare_support --cov-branch --cov-report=term-missing --cov-fail-under=80
uv run mypy src
uv run ruff check src tests
uv run ruff format --check src tests
```

Expected: all checks pass, including the new routing/CSS contract test and the frontend component tests.

## 7. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| 404 on session start in development | The browser base is not `/api` or the dev proxy is missing | Confirm `frontend/src/api.ts` defaults to `/api` and `vite.config.ts` proxies `/api` |
| 404 on session start in production | The reverse proxy does not route `/api/*` to the backend root | Add the `/api` route and retry |
| CORS error with a direct-origin override | The frontend origin is not allowed | Add it to `CORS_ALLOWED_ORIGINS` and restart the backend |
| Session starts but messages fail with 401 | The proof header is missing or stale | Reset the session; confirm `X-Session-Proof` is sent and exposed |
| Topbar touches the viewport edges | The page shell padding was removed | Restore the shell horizontal padding and the topbar's own inset |
| Horizontal scroll on mobile | The topbar or navigation exceeds the viewport | Keep navigation scrollable within its row and remove fixed widths |
