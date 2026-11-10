# Phase 1 Data Model: Guided Demo Paths

**Feature**: `005-guided-demo-paths`
**Date**: 2026-11-09

## Scope

No persistent storage and no backend entities are introduced. This feature adds client-side definitions for guided demo paths and client state that tracks the active path and step. The existing deterministic offline engine, sample records, and conversation-turn model are reused unchanged.

---

## Guided Demo Path

**Represents**: A named, selectable scripted scenario available in the in-browser demo.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier used for selection and tests. |
| `title` | string | Short visitor-facing name, e.g. "Premium billing journey". |
| `description` | string | One sentence describing what the path demonstrates. |
| `expectedOutcome` | string | Plain-language description of the result shown before starting. |
| `steps` | ordered list of `GuidedStep` | Fixed sequence of pre-written visitor messages; at least one. |

**Validation rules**:
- `id` MUST be unique across all paths.
- `title` and `description` MUST be non-empty.
- `steps` MUST contain at least one step and preserve declaration order.
- A path MUST NOT require the visitor to type free-form text.
- All content MUST use fictional sample data only.

---

## Guided Step

**Represents**: A single pre-written visitor message within a path.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier, unique within its path. |
| `message` | string | Exact text sent to the offline engine; not editable by the visitor. |
| `label` | string or null | Optional short description of the step for the UI, e.g. "Share identity". |

**Validation rules**:
- `message` MUST be non-empty and sent verbatim.
- `id` MUST be unique within the path.
- The message MUST be valid input for the existing deterministic engine (it must not rely on undocumented parsing behavior for correctness; tests assert the expected turn).

---

## Guided Path Progress

**Represents**: How far the visitor has advanced through the selected path.

| Field | Type | Description |
|-------|------|-------------|
| `pathId` | string or null | Active path, or `null` when no path is selected. |
| `stepIndex` | number | Zero-based index of the next step to send; equals `steps.length` when complete. |
| `status` | `idle` \| `active` \| `complete` | Progress state. |

**Validation rules**:
- `status` is `idle` when `pathId` is `null`.
- `status` is `active` when `0 <= stepIndex < steps.length`.
- `status` is `complete` when `stepIndex >= steps.length`.
- `stepIndex` MUST NOT decrease except through an explicit restart or path switch.
- Only one path may be active at a time.

**State transitions**:

```text
idle ──select path──▶ active (stepIndex = 0, fresh session)
active ──next step (not last)──▶ active (stepIndex + 1)
active ──next step (last)──▶ complete
complete ──restart──▶ active (stepIndex = 0, fresh session)
any ──select different path──▶ active (stepIndex = 0, fresh session)
any ──switch to live service──▶ idle (guided state cleared, live composer available)
active / complete ──reset──▶ idle (or restart current path, per control)
```

---

## Demo Source

**Represents**: Where the active conversation is served from. Existing type extended in meaning only.

| Value | Meaning | Guided UI |
|-------|---------|-----------|
| `none` | No session is active yet. | Hidden |
| `live` | The conversation is served by the API backend. | Hidden; editable composer shown |
| `offline` | The conversation is served by the in-browser demo. | Path picker and step controls shown; editable composer hidden/disabled |

**Validation rules**:
- Guided paths are presented only when `source === 'offline'`.
- The live source MUST keep the editable free-text composer.
- Switching between live and offline MUST clear messages so conversations do not mix.

---

## Demo Session (client view)

**Represents**: The active conversation shown to the visitor, regardless of source. Existing state reused.

| Field | Type | Description |
|-------|------|-------------|
| `source` | `none` \| `live` \| `offline` | Which engine serves the conversation. |
| `id` | string | Conversation identifier. |
| `proof` | string or null | Ownership proof for live requests; local marker for the demo. |
| `messages` | ordered chat messages | Rendered conversation, including pre-written visitor messages. |
| `telemetry` | telemetry snapshot | Sanitized workflow state for the telemetry panel. |
| `busy` | boolean | Whether a step or request is processing; prevents duplicate sends. |
| `activePath` | `GuidedDemoPath` or null | Selected path while offline. |
| `pathStepIndex` | number | Next step to send while offline. |

**Validation rules**:
- Exactly zero or one active demo session exists at a time.
- A pre-written visitor message is appended unchanged when its step is applied.
- While `busy`, path switching and repeated advancement MUST be prevented.
- Session proof and sample secrets MUST NOT be rendered in the UI or written to logs.

---

## Demo Outcome

**Represents**: The displayed result at the end of a path.

| Field | Source | Description |
|-------|--------|-------------|
| `classification` | Final `ConversationTurn.classification` | `premium`, `regular`, or `null`. |
| `routingStatus` | Final `ConversationTurn.routing_status` | `routed`, `clarification_required`, `fallback`, or `null`. |
| `routingIntent` | Final `ConversationTurn.routing_intent` | Classified intent, e.g. `insurance`. |
| `supportDepartment` | Final `ConversationTurn.support_department` | Department name or `null`. |
| `terminated` | Final `ConversationTurn.terminated` | Whether verification ended unsuccessfully. |

**Validation rules**:
- Outcome MUST be derived from the final engine turn, not hand-authored independently.
- The displayed outcome MUST match the path's declared `expectedOutcome` in tests.
- A terminating outcome MUST offer restart or another path.

---

## Sample Patient Record (reused reference data)

**Represents**: The fictional records already used by `offlineDemo.ts`.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable fictional identifier. |
| `name` | string | Fictional patient name. |
| `phone` | string | Fictional phone number. |
| `dateOfBirth` | string | Fictional ISO date. |
| `secretQuestion` | string | Fictional security question. |
| `secretAnswer` | string | Fictional security answer. |
| `premium` | boolean | Service tier used to demonstrate classification. |

**Validation rules**:
- Records remain fictional and unchanged.
- Identity matching still requires at least two attributes, matching the deterministic engine.
- No real personal data may be substituted into this dataset.
