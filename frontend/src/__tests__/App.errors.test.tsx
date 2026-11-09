import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp, sessionResponse } from '../test/demoHarness'

function forbidden() {
  return Promise.resolve(
    new Response(JSON.stringify({ detail: 'Session proof missing.' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}

function serverError() {
  return Promise.resolve(new Response('Internal error', { status: 500 }))
}

async function expectGenuineError(expectedMessage: string | RegExp) {
  renderApp()

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent(expectedMessage)
  expect(screen.queryByText(/Offline demo mode/)).not.toBeInTheDocument()
  expect(screen.getByPlaceholderText('Start a session to begin')).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Start session' })).toBeEnabled()
}

describe('genuine service errors', () => {
  it('does not start the offline demo for a 403 and shows the server detail', async () => {
    mockFetch(forbidden)

    await expectGenuineError('Session proof missing.')
  })

  it('does not start the offline demo for a 500 and asks the visitor to retry', async () => {
    mockFetch(serverError)

    await expectGenuineError('Please try again')
  })

  it('retries into a live session after a genuine error', async () => {
    let attempts = 0
    mockFetch(() => {
      attempts += 1
      if (attempts === 1) return forbidden()
      return sessionResponse({ reply: 'Recovered session.' })
    })

    renderApp()

    await screen.findByRole('alert')
    fireEvent.click(screen.getByRole('button', { name: 'Start session' }))

    await screen.findByText('Recovered session.')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask a support question...')).toBeEnabled()
  })
})
