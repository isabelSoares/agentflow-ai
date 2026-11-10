import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp, sessionResponse } from '../test/demoHarness'

const OFFLINE_GREETING = /To get started, could you please tell me your name/

describe('live backend preference', () => {
  it('uses the live service without an offline notice when the API is reachable', async () => {
    mockFetch(() => sessionResponse({ reply: 'Live session ready.' }))

    renderApp()

    await screen.findByText('Live session ready.')
    expect(screen.queryByText(/Offline demo mode/)).not.toBeInTheDocument()
  })

  it('switches from the offline demo to the live service on retry', async () => {
    let attempts = 0
    mockFetch(() => {
      attempts += 1
      if (attempts === 1) return Promise.resolve(new Response('Method Not Allowed', { status: 405 }))
      return Promise.resolve(sessionResponse({ reply: 'Live session ready.' }))
    })

    renderApp()

    await screen.findByText(OFFLINE_GREETING)
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')

    fireEvent.click(screen.getByRole('button', { name: 'Try live service' }))

    await screen.findByText('Live session ready.')
    expect(screen.queryByText(/Offline demo mode/)).not.toBeInTheDocument()
    expect(screen.queryByText(OFFLINE_GREETING)).not.toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Choose a guided demo path' })).not.toBeInTheDocument()
    expect(screen.queryByText(/scripted walkthrough/i)).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask a support question...')).toBeEnabled()
  })

  it('stays offline without an error when the live retry is still unavailable', async () => {
    mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))

    renderApp()

    await screen.findByText(OFFLINE_GREETING)
    fireEvent.click(screen.getByRole('button', { name: 'Try live service' }))

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Try live service' })).toBeEnabled(),
    )
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('shows a genuine error during retry and keeps the offline demo usable', async () => {
    let attempts = 0
    mockFetch(() => {
      attempts += 1
      if (attempts === 1) return Promise.resolve(new Response('Method Not Allowed', { status: 405 }))
      return Promise.resolve(
        new Response(JSON.stringify({ detail: 'Session proof missing.' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    })

    renderApp()

    await screen.findByText(OFFLINE_GREETING)
    fireEvent.click(screen.getByRole('button', { name: 'Try live service' }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Session proof missing.')
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')
    expect(screen.getByRole('group', { name: 'Choose a guided demo path' })).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Ask a support question...')).not.toBeInTheDocument()
  })
})
