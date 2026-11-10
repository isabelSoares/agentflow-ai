# Validation Record: Guided Demo Paths

**Feature**: `005-guided-demo-paths`
**Date**: 2026-11-10
**Branch**: `fix/demo-workflow`
**Environment**: macOS, Node.js 24.21.0, npm 11.19.0, uv 0.12.13

This record captures the checks used to verify the implemented feature and maps the specification requirements to automated coverage. It distinguishes automated verification from checks that still require a real browser or assistive-technology run.

## Checks Run

| Check | Command / Method | Result |
|-------|------------------|--------|
| Frontend tests | `cd frontend && npm test` | PASS — 15 files, 79 tests |
| Documentation and contract tests | `uv run pytest tests/unit/test_architecture_docs.py tests/unit/test_system_diagram_docs.py tests/contract/test_frontend_demo_contract.py -q` | PASS — 14 tests |
| Frontend production build | `cd frontend && npm run build` | PASS |
| Pages-style build and serve | `npm run build -- --base=/agentflow-ai/`, serve under `/agentflow-ai/` | PASS — index `200`; `POST /api/conversations` returns `501`, which triggers offline mode |
| Live backend smoke | `GET /health`; `POST /conversations` on the Docker backend at port 8000 | PASS — health `200`; conversation creation `201` |
| CI on PR #24 at commit `d91068e` | GitHub checks | PASS — `quality`, `frontend`, `smoke`, `live-llm`, and `launch-readiness` green |

All required PR checks passed on the validation commit before merge.

## Requirement Traceability

| Requirement / Scenario | Automated coverage |
|------------------------|--------------------|
| US1.1–US1.5: offline paths, prepared messages, completion, restart, switch | `App.guidedPaths.test.tsx` |
| US2.1–US2.4: premium, regular, clarification, failed verification | `guidedDemoPaths.test.ts`, `App.guidedPaths.test.tsx` |
| US2.5: every path ends with a clear outcome and restart/switch controls | `App.guidedPaths.test.tsx` |
| US3.1–US3.2: live mode keeps the composer and does not show guided paths | `App.session.test.tsx`, `App.livePreference.test.tsx` |
| US3.3: unavailable retry stays in offline mode | `App.livePreference.test.tsx` |
| US3.4: genuine `403`/`500` errors do not start the guided demo | `App.errors.test.tsx`, `App.livePreference.test.tsx` |
| US4.1: scripted-walkthrough explanation | `App.guidance.test.tsx` |
| US4.2–US4.3: keyboard operation, labels, live-region announcements | `App.accessibility.test.tsx` |
| FR-006: premium, regular, clarification, failed verification | `guidedDemoPaths.test.ts`, `App.guidedPaths.test.tsx` |
| FR-010: fictional-only path data, no credentials or real contact data | `guidedDemoPaths.test.ts` data-guard tests |
| FR-012: actionable error and no silent offline fallback | `App.errors.test.tsx`, `App.livePreference.test.tsx` |
| FR-017 / SC-005: no raw HTTP status codes in guided mode | `App.offline.test.tsx`, `App.guidedPaths.test.tsx`, `guidedDemoPaths.test.ts` |
| SC-001 / SC-003: every path reaches its expected outcome | `guidedDemoPaths.test.ts`, `App.guidedPaths.test.tsx` |
| SC-002: complete a path within two minutes | `App.guidedPaths.test.tsx` timing test (`< 120000 ms`) |
| SC-004: restart or switch in under one second | `App.guidedPaths.test.tsx` timing test (`< 1000 ms`) |
| SC-006: live sessions keep the free-text experience | `App.session.test.tsx`, `App.livePreference.test.tsx` |
| SC-007: keyboard and screen-reader-oriented behavior | `App.accessibility.test.tsx`, `App.guidance.test.tsx` |

## Accessibility Note

The quickstart allows screen-reader validation to be represented by the automated accessibility assertions. The current run used Testing Library assertions for labels, keyboard-operable controls, and polite live-region updates. A real screen-reader and browser pass was not performed in this environment and remains a recommended pre-launch manual check.

## Timing Note

The automated timing tests guard the SC-002 and SC-004 budgets, but they run in jsdom. They prove the interaction path stays far below the budgets; they are not a substitute for measuring real-browser rendering and first-time-user completion.

## Known Limitations

- The public GitHub Pages deployment is a static build and uses the guided offline demo. It does not run the FastAPI service.
- A full live-backend identity flow needs a configured `GROQ_API_KEY`; the default fake extractor has no scripted turns.
- Wiring the Pages build to a real backend requires `VITE_API_BASE_URL` and a Pages origin in `CORS_ALLOWED_ORIGINS`.
- This project remains a demo/evaluation adapter using fictional data. A production clinical deployment requires a separate review of consent, retention, identity proofing, PHI storage, rate limiting, monitoring, and compliance controls.

## Conclusion

The specification, plan, tasks, and implementation are consistent for the static demo. All automated checks pass, and the recorded manual-equivalent evidence supports merging and deploying the feature. Real-browser timing and assistive-technology checks are recommended before a public launch.
