import type { ConversationTurn } from './types'

const PROOF_HEADER = 'X-Session-Proof'

export function resolveApiBase(raw: string | undefined = import.meta.env.VITE_API_BASE_URL): string {
  const configured = raw?.trim() ?? ''
  if (!configured) return '/api'
  return configured.replace(/\/+$/, '')
}

const API_BASE = resolveApiBase()

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * True when the API could not be reached at all (network failure, missing
 * /api route, or a static host rejecting POST with 405/501). These are the
 * cases where the page is served without a backend, so the offline demo can
 * take over.
 */
export function isBackendUnreachable(status: number): boolean {
  return status === 0 || status === 404 || status === 405 || status === 501
}

export interface ApiResult {
  turn: ConversationTurn
  proof: string | null
}

type RequestHeaders = Record<string, string>

async function request(path: string, init: RequestInit & { headers?: RequestHeaders } = {}) {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...init.headers,
      },
    })
  } catch {
    throw new ApiError(
      'Cannot reach the AgentFlow API. Start the backend on port 8000 and try again.',
      0,
    )
  }

  if (!response.ok) {
    let detail =
      response.status === 404
        ? 'The demo service could not be reached. Check that the API is running and /api is routed to the backend, then try again.'
        : response.status === 405 || response.status === 501
          ? 'This page is served as a static site without an API backend, so the request was rejected (405 Method Not Allowed). Use the offline demo on this page, or run the full stack locally — see the README.'
          : `Request failed with status ${response.status}.`
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (
        typeof body.detail === 'string' &&
        response.status !== 404 &&
        response.status !== 405 &&
        response.status !== 501
      ) {
        detail = body.detail
      }
    } catch {
      // Keep the actionable message when the body is not JSON.
    }
    throw new ApiError(detail, response.status)
  }

  return {
    turn: (await response.json()) as ConversationTurn,
    proof: response.headers.get(PROOF_HEADER),
  }
}

export function createConversation(): Promise<ApiResult> {
  return request('/conversations', { method: 'POST' })
}

export function sendMessage(
  conversationId: string,
  proof: string | null,
  text: string,
): Promise<ApiResult> {
  return request(`/conversations/${encodeURIComponent(conversationId)}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(proof ? { [PROOF_HEADER]: proof } : {}),
    },
    body: JSON.stringify({ text }),
  })
}

export function resetConversation(conversationId: string, proof: string | null): Promise<ApiResult> {
  return request(`/conversations/${encodeURIComponent(conversationId)}/reset`, {
    method: 'POST',
    headers: proof ? { [PROOF_HEADER]: proof } : {},
  })
}
