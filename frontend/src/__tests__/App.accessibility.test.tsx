import axe from 'axe-core'
import { fireEvent, screen, waitFor } from '@testing-library/react'
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

  it('exposes an accessible guided demo with no axe violations offline', async () => {
    mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))

    const { container } = renderApp()
    await screen.findByText(/To get started, could you please tell me your name/)

    expect(
      await screen.findByRole('group', { name: 'Choose a guided demo path' }),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Guided demo status')).toHaveAttribute('aria-live', 'polite')

    const pathButton = screen.getByRole('button', { name: /Premium billing journey/ })
    expect(pathButton).toBeInstanceOf(HTMLButtonElement)
    expect(pathButton).toBeEnabled()
    pathButton.focus()
    expect(pathButton).toHaveFocus()

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })
    expect(results.violations).toEqual([])
  })

  it('announces guided step progress through a polite live region', async () => {
    mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))

    renderApp()
    await screen.findByText('Guided demo paths available.')
    const status = screen.getByLabelText('Guided demo status')

    fireEvent.click(screen.getByRole('button', { name: /Premium billing journey/ }))

    await waitFor(() => expect(status).toHaveTextContent('Step 1 of 3: Share identity'))
  })
})
