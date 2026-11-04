import axe from 'axe-core'
import { screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { mockFetch, renderApp, sessionResponse } from '../test/demoHarness'

async function expectAccessibleApp() {
  mockFetch(() => sessionResponse({ reply: 'Welcome to the demo.' }))

  const { container } = renderApp()
  await screen.findByRole('banner')

  const results = await axe.run(container, {
    rules: {
      'color-contrast': { enabled: false },
    },
  })
  expect(results.violations).toEqual([])
}

describe('accessibility', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.classList.remove('dark-mode')
  })

  it('has no axe violations in dark mode (default)', async () => {
    window.localStorage.setItem('dark-mode', 'true')
    document.documentElement.classList.add('dark-mode')
    await expectAccessibleApp()
  })

  it('has no axe violations in light mode', async () => {
    window.localStorage.setItem('dark-mode', 'false')
    await expectAccessibleApp()
  })

  it('exposes labelled landmarks, a labelled nav, and a labelled theme toggle', async () => {
    mockFetch(() => sessionResponse({ reply: 'Welcome to the demo.' }))

    renderApp()
    await screen.findByRole('banner')

    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
    expect(screen.getByRole('complementary', { name: 'Agent telemetry' })).toBeInTheDocument()
    expect(
      screen.getByRole('region', { name: 'AgentFlow interactive demo' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /switch to (light|dark) mode/i })).toBeInTheDocument()
    expect(screen.getByLabelText('Message')).toBeInTheDocument()
  })
})
