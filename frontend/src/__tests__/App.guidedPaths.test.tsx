import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockFetch, renderApp } from '../test/demoHarness'

const OFFLINE_GREETING = /To get started, could you please tell me your name/

function mockOffline() {
  mockFetch(() => Promise.resolve(new Response('Method Not Allowed', { status: 405 })))
}

async function openPathPicker() {
  mockOffline()
  renderApp()
  await screen.findByText(OFFLINE_GREETING)
  await screen.findByRole('button', { name: /Premium billing journey/ })
}

function findProgress(text: string) {
  return screen.findByText(text, { selector: '.guided-progress' })
}

async function runPath(name: RegExp, steps: string[]) {
  fireEvent.click(screen.getByRole('button', { name }))
  await findProgress(`Step 1 of ${steps.length}`)
  for (let index = 0; index < steps.length; index += 1) {
    fireEvent.click(screen.getByRole('button', { name: 'Next step' }))
    if (index === steps.length - 1) {
      await findProgress('Path complete')
    } else {
      await findProgress(`Step ${index + 2} of ${steps.length}`)
    }
  }
}

describe('guided demo paths', () => {
  it('offers scripted paths instead of a free-text composer offline', async () => {
    await openPathPicker()

    expect(screen.getByRole('button', { name: /Premium billing journey/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Regular appointment journey/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ambiguous identity journey/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Failed verification journey/ })).toBeInTheDocument()
    expect(screen.getByText(/scripted walkthrough/i)).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Ask a support question...')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Send' })).not.toBeInTheDocument()
  })

  it('advances a selected path with prepared non-editable messages', async () => {
    await openPathPicker()

    fireEvent.click(screen.getByRole('button', { name: /Premium billing journey/ }))
    await findProgress('Step 1 of 3')
    expect(screen.getByTestId('guided-prepared-message')).toHaveTextContent("Hi, I'm Lisa")

    fireEvent.click(screen.getByRole('button', { name: 'Next step' }))
    await screen.findByText(/Which is the name of my dog\?/)
    expect(screen.getByText('Step 2 of 3', { selector: '.guided-progress' })).toBeInTheDocument()
    expect(screen.getByTestId('guided-prepared-message')).toHaveTextContent('Yoda')
  })

  it('restarts the current path from a clean conversation', async () => {
    await openPathPicker()
    fireEvent.click(screen.getByRole('button', { name: /Premium billing journey/ }))
    await findProgress('Step 1 of 3')

    fireEvent.click(screen.getByRole('button', { name: 'Next step' }))
    await screen.findByText(/Which is the name of my dog\?/)

    fireEvent.click(screen.getByRole('button', { name: 'Restart' }))
    await findProgress('Step 1 of 3')
    expect(screen.queryByText(/Which is the name of my dog\?/)).not.toBeInTheDocument()
  })

  it('switches paths and clears the previous conversation', async () => {
    await openPathPicker()
    fireEvent.click(screen.getByRole('button', { name: /Premium billing journey/ }))
    await findProgress('Step 1 of 3')
    fireEvent.click(screen.getByRole('button', { name: 'Next step' }))
    await screen.findByText(/Which is the name of my dog\?/)

    fireEvent.click(screen.getByRole('button', { name: 'Choose another path' }))
    await screen.findByRole('button', { name: /Regular appointment journey/ })
    expect(screen.queryByText(/Which is the name of my dog\?/)).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Regular appointment journey/ }))
    await findProgress('Step 1 of 3')
    expect(screen.getByTestId('guided-prepared-message')).toHaveTextContent('John Doe')
  })

  it('completes the premium path with a routed premium outcome', async () => {
    await openPathPicker()
    await runPath(/Premium billing journey/, ['identity', 'secret', 'request'])

    await findProgress('Path complete')
    expect(screen.getByText(/Classification: premium/)).toBeInTheDocument()
    expect(screen.getByText(/Routed to Insurance and Billing Department/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Restart' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Choose another path' })).toBeInTheDocument()
  })

  it('completes the regular path with standard support routing', async () => {
    await openPathPicker()
    await runPath(/Regular appointment journey/, ['identity', 'secret', 'request'])

    await findProgress('Path complete')
    expect(screen.getByText(/Classification: regular/)).toBeInTheDocument()
    expect(screen.getByText(/Routed to Standard Patient Support/)).toBeInTheDocument()
  })

  it('completes the ambiguous path with a clarification outcome', async () => {
    await openPathPicker()
    await runPath(/Ambiguous identity journey/, ['identity'])

    await findProgress('Path complete')
    expect(screen.getByText(/details are ambiguous/i, { selector: '.guided-outcome strong' })).toBeInTheDocument()
  })

  it('completes the failed verification path with a termination outcome', async () => {
    await openPathPicker()
    await runPath(/Failed verification journey/, ['one', 'two', 'three'])

    await findProgress('Path complete')
    expect(screen.getByText(/Verification terminated/)).toBeInTheDocument()
    expect(screen.getByText(/treated as a non-client/i, { selector: '.guided-outcome strong' })).toBeInTheDocument()
  })
})
