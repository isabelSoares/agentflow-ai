import { screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  mockFetch,
  renderApp,
  requestUrl,
  sessionResponse,
} from '../test/demoHarness'

describe('demo session start', () => {
  it('starts a session automatically through the /api base and enables the composer', async () => {
    const fetchMock = mockFetch(() => sessionResponse({ reply: 'Welcome to the secure demo.' }))

    renderApp()

    await screen.findByText('Welcome to the secure demo.')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [input, init] = fetchMock.mock.calls[0]
    expect(requestUrl(input)).toBe('/api/conversations')
    expect(init?.method).toBe('POST')
    expect(screen.getByPlaceholderText('Ask a support question...')).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Reset session' })).toBeEnabled()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Start session' })).not.toBeInTheDocument()
    expect(
      screen.queryByRole('group', { name: 'Choose a guided demo path' }),
    ).not.toBeInTheDocument()
    expect(screen.queryByText(/scripted walkthrough/i)).not.toBeInTheDocument()
  })

  it('keeps the session starting state single-flight while the request is pending', async () => {
    let resolveSession: ((response: Response) => void) | undefined
    const pending = new Promise<Response>((resolve) => {
      resolveSession = resolve
    })
    const fetchMock = mockFetch(() => pending)

    renderApp()

    const starting = await screen.findByRole('button', { name: 'Starting...' })
    expect(starting).toBeDisabled()
    expect(screen.getByPlaceholderText('Start a session to begin')).toBeDisabled()
    expect(fetchMock).toHaveBeenCalledTimes(1)

    resolveSession?.(sessionResponse({ reply: 'Session ready.' }))
    await screen.findByText('Session ready.')

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(screen.getByPlaceholderText('Ask a support question...')).toBeEnabled()
  })
})
