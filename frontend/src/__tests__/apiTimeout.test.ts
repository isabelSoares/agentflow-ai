import { describe, expect, it, vi } from 'vitest'
import { classifyStartupFailure, createConversation } from '../api'

function abortableFetch() {
  const fetchMock = vi.fn(
    (_input: RequestInfo | URL, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => {
          reject(new DOMException('Aborted', 'AbortError'))
        })
      }),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

async function captureFailure(run: () => Promise<unknown>): Promise<unknown> {
  try {
    await run()
  } catch (error) {
    return error
  }
  return undefined
}

describe('startup availability', () => {
  it('treats a timed-out startup as unavailable', async () => {
    abortableFetch()

    const failure = await captureFailure(() => createConversation({ timeoutMs: 10 }))

    expect(failure).toBeInstanceOf(Error)
    expect(classifyStartupFailure(failure)).toBe('unavailable')
  })

  it('treats a gateway-unavailable failure as unavailable', async () => {
    vi.stubGlobal('fetch', () => Promise.resolve(new Response('Bad gateway', { status: 502 })))

    const failure = await captureFailure(() => createConversation())

    expect(classifyStartupFailure(failure)).toBe('unavailable')
  })

  it('treats a genuine application failure as an error', async () => {
    vi.stubGlobal('fetch', () =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: 'Session proof missing.' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    const failure = await captureFailure(() => createConversation())

    expect(classifyStartupFailure(failure)).toBe('error')
  })

  it('treats a successful creation as available', async () => {
    vi.stubGlobal('fetch', () =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            conversation_id: 'conversation-1',
            reply: 'Welcome.',
            identified: false,
            authenticated: false,
            terminated: false,
            classification: null,
            routing_status: null,
            routing_intent: null,
            support_department: null,
          }),
          { status: 201, headers: { 'Content-Type': 'application/json', 'X-Session-Proof': 'proof-1' } },
        ),
      ),
    )

    const result = await createConversation()

    expect(result.turn.conversation_id).toBe('conversation-1')
    expect(result.proof).toBe('proof-1')
  })
})
