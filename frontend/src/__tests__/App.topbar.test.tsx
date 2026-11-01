import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp, sessionResponse } from '../test/demoHarness'

describe('topbar structure', () => {
  it('renders the brand and primary navigation inside the site header', async () => {
    mockFetch(() => sessionResponse({ reply: 'Welcome to the demo.' }))

    renderApp()

    const header = await screen.findByRole('banner')
    expect(header).toHaveClass('site-header')
    expect(within(header).getByRole('link', { name: /AgentFlow AI home/i })).toBeInTheDocument()

    const navigation = within(header).getByRole('navigation', { name: 'Primary' })
    for (const name of ['Demo', 'Principles', 'Architecture', 'GitHub', 'API docs']) {
      expect(within(navigation).getByRole('link', { name })).toBeInTheDocument()
    }
  })
})
