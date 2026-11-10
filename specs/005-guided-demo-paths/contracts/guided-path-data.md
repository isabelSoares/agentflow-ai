# Guided Path Data Contract

**Feature**: `005-guided-demo-paths`
**Date**: 2026-11-09

This contract defines the shape and guarantees of the guided demo path definitions. It is consumed by the demo UI and by automated tests. It does not change the session API contract in `specs/002-fix-demo-session-topbar/contracts/session-api.md` or the offline fallback contract in `specs/004-static-chat-fallback/contracts/offline-fallback.md`.

## Definition shape

Each path MUST provide:

```text
GuidedDemoPath {
  id: string                 // unique across all paths
  title: string              // visitor-facing name
  description: string        // one-sentence purpose
  expectedOutcome: string    // plain-language final result
  steps: GuidedStep[]        // ordered, length >= 1
}

GuidedStep {
  id: string                 // unique within the path
  message: string            // sent verbatim to the offline engine
  label?: string | null      // optional short step description
}
```

## Guarantees

1. Path definitions are static data with no network dependency.
2. Steps are ordered and sent verbatim; the visitor cannot edit them.
3. Every path uses only fictional sample data.
4. Every path's step sequence is valid input for the existing deterministic offline engine.
5. Every path's final turn matches its declared `expectedOutcome` (verified by tests).
6. Adding or adjusting a path requires editing only the path data module, not conversation logic.
7. Paths do not read or write persistent storage.

## Required initial path coverage

| Path | Demonstrates | Expected final signal |
|------|--------------|-----------------------|
| Premium support journey | Successful identity, verification, premium classification, department routing | `authenticated=true`, `classification="premium"`, `routing_status="routed"` |
| Regular support journey | Successful identity, verification, regular classification, standard routing | `authenticated=true`, `classification="regular"`, `support_department="Standard Patient Support"` |
| Clarification journey | Ambiguous identity that requires more detail | `routing_status="clarification_required"` or an explicit ask-for-more-attributes reply |
| Failed verification journey | Bounded attempts and guardrail termination | `terminated=true` |

## Data rules

- No step message may contain real personal data, credentials, or secret answers for any real system.
- Step messages MUST be human-readable and complete on their own, because they are shown to the visitor as their own messages.
- Path ids and step ids MUST be stable so tests can reference them.
- Path content MUST NOT include raw HTTP status codes.
