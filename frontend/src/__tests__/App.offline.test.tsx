import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp } from '../test/demoHarness'

async function completePremiumPath() {
  fireEvent.click(await screen.findByRole('button', { name: /Premium billing journey/ }))
  await screen.findByText('Step 1 of 3')

  fireEvent.click(screen.getByRole('button', { name: 'Next step' }))
  await screen.findByText(/Which is the name of my dog\?/)

  fireEvent.click(screen.getByRole('button', { name: 'Next step' }))
  await screen.findByText(/As a premium patient/)

  fireEvent.click(screen.getByRole('button', { name: 'Next step' }))
  await screen.findByText(/I'll connect you with the Insurance and Billing Department/)

  expect(screen.getByText('Routed')).toBeInTheDocument()
  expect(screen.getByText(/Insurance And Billing Department/)).toBeInTheDocument()
}

describe('live page without a backend (405)', () => {
  it('starts the offline guided demo automatically without a blocking error', async () => {
    mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))

    renderApp()

    await screen.findByText(/To get started, could you please tell me your name/)
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText(/405 Method Not Allowed/)).not.toBeInTheDocument()
    expect(await screen.findByRole('group', { name: 'Choose a guided demo path' })).toBeInTheDocument()

    await completePremiumPath()
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
