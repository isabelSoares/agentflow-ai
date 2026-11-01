import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  jsonResponse,
  mockFetch,
  renderApp,
  requestUrl,
  sessionResponse,
  turnResponse,
} from '../test/demoHarness'

function proofHeader(init: RequestInit | undefined): string | undefined {
  return (init?.headers as Record<string, string> | undefined)?.['X-Session-Proof']
}

describe('demo conversation turns', () => {
  it('sends messages with the session proof and resets with the active proof', async () => {
    const fetchMock = mockFetch((input, init) => {
      const url = requestUrl(input)
      if (url === '/api/conversations' && init?.method === 'POST') {
        return sessionResponse({ reply: 'Welcome to the demo.' })
      }
      if (url === '/api/conversations/conversation-1/messages' && init?.method === 'POST') {
        return turnResponse({ reply: 'Here is help with your card.' }, 'proof-2')
      }
      if (url === '/api/conversations/conversation-1/reset' && init?.method === 'POST') {
        return sessionResponse({ reply: 'Session reset.' }, 'proof-3')
      }
      return jsonResponse({ status: 404 })
    })

    renderApp()
    await screen.findByText('Welcome to the demo.')

    fireEvent.change(screen.getByPlaceholderText('Ask a support question...'), {
      target: { value: 'I need help with a card payment.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    await screen.findByText('Here is help with your card.')
    expect(screen.getByText('I need help with a card payment.')).toBeInTheDocument()
    expect(proofHeader(fetchMock.mock.calls[1]?.[1])).toBe('proof-1')

    fireEvent.click(screen.getByRole('button', { name: 'Reset session' }))

    await screen.findByText('Session reset.')
    expect(requestUrl(fetchMock.mock.calls[2]?.[0] as RequestInfo)).toBe(
      '/api/conversations/conversation-1/reset',
    )
    expect(proofHeader(fetchMock.mock.calls[2]?.[1])).toBe('proof-2')
  })

  it('preserves the active session and conversation when a message send fails', async () => {
    mockFetch((input, init) => {
      const url = requestUrl(input)
      if (url === '/api/conversations' && init?.method === 'POST') {
        return sessionResponse({ reply: 'Welcome to the demo.' })
      }
      if (url.endsWith('/messages')) return Promise.reject(new TypeError('Failed to fetch'))
      return jsonResponse({ status: 404 })
    })

    renderApp()
    await screen.findByText('Welcome to the demo.')

    fireEvent.change(screen.getByPlaceholderText('Ask a support question...'), {
      target: { value: 'Are you there?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Cannot reach the AgentFlow API')
    expect(screen.getByText('Are you there?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reset session' })).toBeEnabled()
    expect(screen.getByPlaceholderText('Ask a support question...')).toBeEnabled()
  })
})
