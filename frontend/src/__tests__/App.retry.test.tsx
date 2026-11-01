import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp, sessionResponse } from '../test/demoHarness'

describe('demo session failure recovery', () => {
  it('shows an actionable error and retries into an active session', async () => {
    let attempts = 0
    mockFetch(() => {
      attempts += 1
      if (attempts === 1) return Promise.reject(new TypeError('Failed to fetch'))
      return sessionResponse({ reply: 'Recovered session.' })
    })

    renderApp()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Cannot reach the AgentFlow API')
    expect(screen.getByPlaceholderText('Start a session to begin')).toBeDisabled()
    const retry = screen.getByRole('button', { name: 'Start session' })
    expect(retry).toBeEnabled()

    fireEvent.click(retry)

    await screen.findByText('Recovered session.')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask a support question...')).toBeEnabled()
  })

  it('shows an actionable route message for a 404 without a bare status code', async () => {
    mockFetch(() => Promise.resolve(new Response('Not found', { status: 404 })))

    renderApp()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('The demo service could not be reached.')
    expect(alert).not.toHaveTextContent('Request failed with status 404')
    expect(screen.getByRole('button', { name: 'Start session' })).toBeEnabled()
  })
})
