import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp } from '../test/demoHarness'

describe('live page without a backend (405)', () => {
  it('explains the 405 and runs the offline demo end to end', async () => {
    mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))

    renderApp()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('405 Method Not Allowed')
    expect(alert).toHaveTextContent('static site without an API backend')
    expect(alert).not.toHaveTextContent('Request failed with status 405')

    fireEvent.click(screen.getByRole('button', { name: 'Run offline demo' }))

    await screen.findByText(/To get started, could you please tell me your name/)
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')

    const input = screen.getByPlaceholderText('Ask a support question...')
    fireEvent.change(input, {
      target: { value: "Hi, I'm Lisa. My phone is +14155552671 and my date of birth is 1990-01-15." },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByText(/Which is the name of my dog\?/)

    fireEvent.change(input, { target: { value: "My dog's name is Yoda." } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByText(/As a premium patient/)

    fireEvent.change(input, { target: { value: 'I need help with a medical bill.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByText(/I'll connect you with the Insurance and Billing Department/)
    expect(screen.getByText('Routed')).toBeInTheDocument()
    expect(screen.getByText(/Insurance And Billing Department/)).toBeInTheDocument()
  })

  it('does not offer the offline demo when the backend answers with a real error', async () => {
    mockFetch(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: 'Session proof missing.' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    renderApp()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Session proof missing.')
    expect(screen.queryByRole('button', { name: 'Run offline demo' })).not.toBeInTheDocument()
  })
})
