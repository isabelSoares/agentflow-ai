# Phase 1 Data Model: Automatic Static-Site Demo Fallback

**Feature**: `004-static-chat-fallback`
**Date**: 2026-11-09

## Scope

This feature introduces no persistent storage and no backend entities. It adds client-side state that decides whether the visitor is served by the live API or the in-browser demo, plus the guidance content shown to the visitor. The deterministic demo engine and sample records already exist and are reused.

---

## Demo Source

**Represents**: Where the active conversation is being served from.

| Value | Meaning |
|-------|---------|
| `none` | No session is active yet. |
| `live` | The conversation is served by the reachable API backend. |
| `offline` | The conversation is served by the deterministic in-browser demo. |

**Validation rules**:
- A session is active only when the source is `live` or `offline`.
- The composer is enabled only when a session is active.
- The offline notice is shown only when the source is `offline`.

**State transitions**:

```text
none ──load──▶ (attempt live)
attempt live ──success──▶ live
attempt live ──backend unavailable──▶ offline
attempt live ──genuine error──▶ none (actionable error, retry offered)
offline ──"Try live service" success──▶ live
offline ──"Try live service" unavailable──▶ offline (notice remains)
live ──reset──▶ live (new session)
offline ──reset──▶ offline (fresh demo session)
```

---

## Backend Availability

**Represents**: The classification of the most recent startup attempt.

| Value | Trigger | Result |
|-------|---------|--------|
| `available` | Successful session creation | Start live session |
| `unavailable` | Network failure, `404`, `405`, `501`, or startup timeout | Start offline demo automatically |
| `error` | Other application failure (`403`, `500`, etc.) | Show actionable error; do not start offline demo |

**Validation rules**:
- `unavailable` MUST NOT surface a raw status code as the primary experience.
- `error` MUST remain visible and MUST NOT be masked by the offline demo.
- Only one startup attempt may be in flight at a time.

---

## Demo Session (client view)

**Represents**: The active conversation shown to the visitor, regardless of source.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `source` | `none` \| `live` \| `offline` | Client state | Which engine serves the conversation. |
| `id` | string | Live response or generated demo id | Conversation identifier. |
| `proof` | string or null | Live response header; `offline-local` equivalent for the demo | Ownership proof for live requests; local marker for the demo. |
| `messages` | ordered list of chat messages | Client state | Rendered conversation. |
| `telemetry` | telemetry snapshot | Turn response | Sanitized workflow state for the telemetry panel. |
| `busy` | boolean | Client state | Whether a turn is processing; prevents duplicate sends. |

**Validation rules**:
- Exactly zero or one active demo session exists at a time.
- Messages from a previous source MUST be cleared when switching between live and offline, so the conversation is coherent.
- Session proof and sample secrets MUST NOT be rendered in the UI or written to logs.

---

## Visitor Guidance

**Represents**: The on-page explanation and suggested scenario for first-time visitors.

| Field | Type | Description |
|-------|------|-------------|
| `projectSummary` | string | One or two sentences describing what AgentFlow AI does and what the demo shows. |
| `steps` | ordered list of `ScenarioStep` | The suggested path through the demo. |
| `sampleIdentity` | string | Fictional identifying details for the sample scenario. |
| `sampleSecretAnswer` | string | Fictional answer to the sample security question. |
| `sampleRequest` | string | A support request that demonstrates routing. |

### ScenarioStep

| Field | Type | Description |
|-------|------|-------------|
| `order` | number | Position in the scenario. |
| `instruction` | string | What the visitor should type or do. |
| `example` | string or null | Optional example text the visitor can reuse. |

**Validation rules**:
- Guidance MUST be visible without opening external documentation.
- Only fictional sample values may be shown.
- Guidance MUST remain available in both live and offline modes; it is not tied to the fallback.
- Guidance MUST NOT imply that the demo uses real patient data.

---

## Sample Patient Record (reused reference data)

**Represents**: The fictional record used by the existing offline engine.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable fictional identifier. |
| `name` | string | Fictional patient name. |
| `phone` | string | Fictional phone number. |
| `dateOfBirth` | string | Fictional ISO date. |
| `secretQuestion` | string | Fictional security question. |
| `secretAnswer` | string | Fictional security answer (also shown in guidance for the demo). |
| `premium` | boolean | Service tier used to demonstrate classification. |

**Validation rules**:
- Records are fictional and remain unchanged from the existing offline engine.
- Identity matching requires at least two attributes, matching the backend's deterministic rule.
- No real personal data may be substituted into this dataset.
