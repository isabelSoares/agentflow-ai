import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp, sessionResponse } from '../test/demoHarness'

async function expectGuidance() {
  const guide = await screen.findByRole('region', { name: 'Demo guidance' })
  expect(guide).toHaveTextContent('Try this scenario')
  expect(guide).toHaveTextContent('AgentFlow AI')
  expect(guide).toHaveTextContent('+14155552671')
  expect(guide).toHaveTextContent('Yoda')
  expect(guide).toHaveTextContent('billing question')
  expect(guide).toHaveTextContent('fictional')
  return guide
}

describe('demo guidance', () => {
  it('shows the project explanation and sample scenario for a live session', async () => {
    mockFetch(() => sessionResponse({ reply: 'Welcome to the demo.' }))

    renderApp()

    await screen.findByText('Welcome to the demo.')
    await expectGuidance()
  })

  it('explains the scripted walkthrough in offline demo mode', async () => {
    mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))

    renderApp()

    await screen.findByText(/To get started, could you please tell me your name/)
    expect(screen.getByText(/scripted walkthrough/i)).toBeInTheDocument()
    expect(
      await screen.findByRole('group', { name: 'Choose a guided demo path' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Offline demo mode')
  })
})
