# Guided Mode UI Contract

**Feature**: `005-guided-demo-paths`
**Date**: 2026-11-09

This contract defines the visitor-visible behavior of guided mode. It complements `specs/004-static-chat-fallback/contracts/offline-fallback.md`; backend availability classification and live/live-fallback behavior are unchanged.

## When guided mode is shown

| Condition | Guided path UI | Editable composer |
|-----------|----------------|-------------------|
| Source is `live` | Hidden | Enabled (existing behavior) |
| Source is `offline` | Shown | Hidden or clearly non-essential |
| Source is `none`, genuine error | Hidden | Disabled (existing behavior) |
| Offline, switching to live in progress | Shown, controls disabled | Hidden |

Rules:
- Guided paths MUST appear only in the in-browser demo, never in place of a working live composer.
- The existing "Offline demo mode" notice MUST remain visible while guided mode is active.
- No guided path requires the visitor to type.

## Path picker

The demo area MUST present:

1. A heading and a short note explaining that the demo is a scripted walkthrough and that clicking advances the conversation.
2. A list of available paths, each showing its title and description.
3. Each path as an operable control reachable by keyboard (button or radio-style selection), with a visible focus indicator.
4. No raw HTTP status codes or technical error text.

## Selected path

While a path is active, the UI MUST show:

1. The path title and description.
2. Progress as "Step N of M" plus the optional step label.
3. The prepared next visitor message (read-only) so the visitor knows what will be sent.
4. A single "Next step" control that sends the prepared message unchanged.
5. A "Choose another path" control that resets the conversation and returns to the picker.
6. A restart control (or the same picker) to replay the path from the beginning.

Rules:
- The prepared message MUST NOT be editable.
- While a step is processing, the advance control MUST be disabled and duplicate sends prevented.
- The visitor MUST be able to switch paths midway; doing so resets messages, telemetry, and step progress.

## Completion

When the final step has been applied:

1. The UI MUST show a plain-language outcome derived from the final offline turn.
2. The advance control MUST be replaced or disabled so no further steps can be sent.
3. Restart and choose-another-path controls MUST be available.
4. The telemetry panel MUST reflect the final classification, routing, and termination state.

## Accessibility

- The path group MUST have an accessible name; each path control MUST expose its title and description.
- Step progress and outcome changes MUST be announced through a polite live region (`role="status"` or equivalent).
- All controls MUST be reachable and operable by keyboard.
- State MUST NOT be conveyed by color or layout alone.
- The prepared message MUST be readable by assistive technology before it is sent.

## Non-goals

- No change to backend routes, payloads, authentication, or proof handling.
- No autoplay timer or automatic progression.
- No persistence of path progress across reloads.
- No real patient data, credentials, or secret answers in path definitions.
