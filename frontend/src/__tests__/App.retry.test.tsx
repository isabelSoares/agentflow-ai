import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp, sessionResponse } from '../test/demoHarness'

describe('demo session failure recovery', () => {
  it('shows an actionable error for a genuine failure and retries into a live session', async () => {
    let attempts = 0
    mockFetch(() => {
      attempts += 1
      if (attempts === 1) {
        return Promise.resolve(new Response('Internal error', { status: 500 }))
      }
      return sessionResponse({ reply: 'Recovered session.' })
    })

    renderApp()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Please try again')
    expect(screen.getByPlaceholderText('Start a session to begin')).toBeDisabled()
    const retry = screen.getByRole('button', { name: 'Start session' })
    expect(retry).toBeEnabled()

    fireEvent.click(retry)

    await screen.findByText('Recovered session.')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask a support question...')).toBeEnabled()
  })

  it('treats a missing API route as unavailable and starts the offline demo', async () => {
    mockFetch(() => Promise.resolve(new Response('Not found', { status: 404 })))

    renderApp()

    await screen.findByText(/To get started, could you please tell me your name/)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')
    expect(screen.queryByText(/Request failed with status 404/)).not.toBeInTheDocument()
  })
})
