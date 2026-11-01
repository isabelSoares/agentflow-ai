import { render } from '@testing-library/react'
import { vi } from 'vitest'
import App from '../App'
import type { ConversationTurn } from '../types'

export function makeTurn(overrides: Partial<ConversationTurn> = {}): ConversationTurn {
  return {
    conversation_id: 'conversation-1',
    reply: 'Start a session to watch the AgentFlow workflow.',
    identified: false,
    authenticated: false,
    terminated: false,
    classification: null,
    routing_status: null,
    routing_intent: null,
    support_department: null,
    ...overrides,
  }
}

interface JsonResponseOptions {
  status?: number
  proof?: string | null
  body?: unknown
}

export function jsonResponse({
  status = 200,
  proof = null,
  body = {},
}: JsonResponseOptions = {}): Response {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  if (proof) headers.set('X-Session-Proof', proof)
  return new Response(JSON.stringify(body), { status, headers })
}

export function sessionResponse(
  overrides: Partial<ConversationTurn> = {},
  proof: string | null = 'proof-1',
): Response {
  return jsonResponse({ status: 201, proof, body: makeTurn(overrides) })
}

export function turnResponse(
  overrides: Partial<ConversationTurn> = {},
  proof: string | null = null,
): Response {
  return jsonResponse({ status: 200, proof, body: makeTurn(overrides) })
}

type FetchHandler = (input: RequestInfo | URL, init?: RequestInit) => Response | Promise<Response>

export function mockFetch(handler: FetchHandler) {
  const fetchMock = vi.fn(handler)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export function renderApp() {
  return render(<App />)
}

export function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input
  if (input instanceof URL) return input.toString()
  return input.url
}
