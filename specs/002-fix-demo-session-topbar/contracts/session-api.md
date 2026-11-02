# Session API Contract

**Feature**: `002-fix-demo-session-topbar`
**Date**: 2026-11-01

## Routing Contract

The browser client and the API deployment MUST agree on a single request prefix.

| Environment | Browser request base | Gateway behavior |
|-------------|----------------------|------------------|
| Local development | `/api` | Vite dev server proxies `/api/*` to `http://127.0.0.1:8000/*` |
| Local production build preview | `/api` | Vite preview proxy mirrors the dev proxy |
| Production static hosting | `/api` | Reverse proxy routes `/api/*` to the backend root |
| Direct-origin override | `VITE_API_BASE_URL` value | Browser calls the configured origin directly |

Rules:
- When `VITE_API_BASE_URL` is unset or empty, the browser base MUST be `/api`.
- The backend route paths remain `/conversations`, `/conversations/{id}/messages`, `/conversations/{id}/reset`, and `/health`.
- A session-start request MUST NOT reach the static frontend host when the API gateway is configured.
- A missing gateway route is a deployment error and MUST be documented.

---

## `POST /api/conversations`

Creates a demo session.

**Request headers**: `Accept: application/json`

**Request body**: none

**Success**: `201 Created`

**Response headers**:
- `X-Session-Proof: <opaque string>` — required on every later session-scoped request.
- `Access-Control-Expose-Headers: X-Session-Proof` — when the browser calls a different origin.

**Response body**:

```json
{
  "conversation_id": "uuid",
  "reply": "string",
  "identified": false,
  "authenticated": false,
  "terminated": false,
  "classification": null,
  "routing_status": null,
  "routing_intent": null,
  "support_department": null
}
```

**Errors**:
- `5xx` — service failure; the visitor sees an actionable error and may retry.
- `404` — MUST NOT occur when the `/api` gateway is correctly configured.
- Network failure — surfaced as an unreachable-service error with retry.

---

## `POST /api/conversations/{conversation_id}/messages`

Sends a visitor message.

**Request headers**:
- `Content-Type: application/json`
- `X-Session-Proof: <proof>` — required.

**Request body**:

```json
{
  "text": "non-empty string, maximum 2000 characters"
}
```

**Success**: `200 OK` with the same turn-response shape as session creation.

**Errors**:
- `401` — missing, malformed, unknown, or inactive proof; uniform `{"detail": "Session access denied."}`.
- `422` — invalid or empty message body.
- Network failure — actionable client error; the existing session remains available for retry.

---

## `POST /api/conversations/{conversation_id}/reset`

Resets the conversation and rotates the ownership proof.

**Request headers**: `X-Session-Proof: <proof>` — required.

**Success**: `200 OK` with a new `X-Session-Proof` response header and cleared workflow state.

**Errors**:
- `401` — missing or invalid proof.
- Network failure — actionable client error; the previous session remains displayed.

---

## `GET /api/health`

Reports service liveness and requires no proof. Used by deployment checks, not by the demo page.

**Success**: `200 OK`

```json
{
  "status": "ok"
}
```

---

## Compatibility Rules

- Response schemas are unchanged; the browser continues to consume the existing fields.
- The ownership-proof header name is unchanged.
- CORS methods and allowed headers are unchanged.
- No endpoint accepts a conversation identifier as proof of ownership.
- No response exposes patient PII.
