# Demo Guidance Contract

**Feature**: `004-static-chat-fallback`
**Date**: 2026-11-09

This contract defines the on-page guidance that lets a first-time visitor understand the project and complete the demo without external documentation. Guidance is shown in both live and offline modes.

## Required content

The demo area MUST present:

1. **What the project does** — a short description of AgentFlow AI as a secure multi-agent patient-support demo covering identity verification, authorization, classification, and routing.
2. **What the demo will show** — a statement that the visitor will watch the workflow identify, verify, classify, and route a support request.
3. **A suggested scenario** — ordered steps using fictional sample values:
   - Step 1: Identify with the sample patient's name plus phone number or date of birth.
   - Step 2: Answer the sample security question with the provided sample answer.
   - Step 3: Ask a support question that demonstrates routing (for example, a billing question).
4. **A note about data** — the sample record is fictional and exists only to demonstrate the deterministic workflow.
5. **A note about live vs offline** — when a backend is connected the same steps run against the live API; otherwise they run in the browser.

## Display rules

- Guidance MUST be visible in the demo area without scrolling to external documentation.
- Guidance MUST NOT block the conversation or require dismissal.
- Sample values MUST be copyable or easy to type from the page.
- Guidance MUST NOT include real personal data, credentials, or secret answers for any real system.
- The suggested scenario MUST be usable with the sample record already present in the in-browser demo engine.

## Accessibility

- Guidance headings MUST follow the page heading hierarchy.
- Instructions MUST be readable by screen readers in document order.
- Example values MUST remain associated with their step (not conveyed only by visual layout).

## Acceptance checks

- A new visitor can complete the sample scenario using only on-page text.
- The sample security answer is discoverable on the page.
- Guidance appears identically in live and offline modes.
- No real personal data appears in guidance or examples.
