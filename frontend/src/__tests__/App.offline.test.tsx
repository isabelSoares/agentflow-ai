import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp } from '../test/demoHarness'

async function completeScenario() {
  const input = await screen.findByPlaceholderText('Ask a support question...')
  expect(input).toBeEnabled()

  fireEvent.change(input, {
    target: {
      value: "Hi, I'm Lisa. My phone is +14155552671 and my date of birth is 1990-01-15.",
    },
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
}

describe('live page without a backend (405)', () => {
  it('starts the offline demo automatically without a blocking error', async () => {
    mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))

    renderApp()

    await screen.findByText(/To get started, could you please tell me your name/)
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText(/405 Method Not Allowed/)).not.toBeInTheDocument()

    await completeScenario()
  })

  it('does not start the offline demo when the backend answers with a real error', async () => {
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
    expect(screen.queryByText(/Offline demo mode/)).not.toBeInTheDocument()
  })
})
