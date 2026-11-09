import type { BackendAvailability, ConversationTurn } from './types'

const PROOF_HEADER = 'X-Session-Proof'

export const STARTUP_TIMEOUT_MS = 6000

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
 * /api route, a static host rejecting POST, or a gateway reporting an
 * unavailable upstream). These are the cases where the page is served
 * without a usable backend, so the offline demo can take over.
 */
export function isBackendUnreachable(status: number): boolean {
  return (
    status === 0 ||
    status === 404 ||
    status === 405 ||
    status === 501 ||
    status === 502 ||
    status === 503 ||
    status === 504
  )
}

/**
 * Classify a failed startup attempt. Unreachable/static-host outcomes start the
 * in-browser demo; every other failure stays a genuine, visible error.
 */
export function classifyStartupFailure(error: unknown): BackendAvailability {
  if (error instanceof ApiError && isBackendUnreachable(error.status)) return 'unavailable'
  return 'error'
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
  } catch (caught) {
    const aborted = caught instanceof Error && caught.name === 'AbortError'
    throw new ApiError(
      aborted
        ? 'The demo service did not respond in time. Use the offline demo or try again.'
        : 'Cannot reach the AgentFlow API. Start the backend on port 8000 and try again.',
      0,
    )
  }

  if (!response.ok) {
    let detail =
      response.status === 404
        ? 'The demo service could not be reached. Check that the API is running and /api is routed to the backend, then try again.'
        : response.status === 405 || response.status === 501
          ? 'This page is served as a static site without an API backend, so the request was rejected (405 Method Not Allowed). Use the offline demo on this page, or run the full stack locally — see the README.'
          : `The demo service returned an unexpected error (status ${response.status}). Please try again.`
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

export function createConversation(options: { timeoutMs?: number } = {}): Promise<ApiResult> {
  const timeoutMs = options.timeoutMs ?? STARTUP_TIMEOUT_MS
  if (timeoutMs <= 0 || typeof AbortController === 'undefined') {
    return request('/conversations', { method: 'POST' })
  }
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  return request('/conversations', { method: 'POST', signal: controller.signal }).finally(() =>
    clearTimeout(timer),
  )
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
