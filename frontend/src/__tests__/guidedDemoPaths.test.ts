import { describe, expect, it } from 'vitest'
import { GUIDED_DEMO_PATHS } from '../guidedDemoPaths'
import { createOfflineSession, offlineSend } from '../offlineDemo'
import type { ConversationTurn, GuidedDemoPath } from '../types'

function applyPath(path: GuidedDemoPath): ConversationTurn {
  let session = createOfflineSession()
  let turn: ConversationTurn | null = null
  for (const step of path.steps) {
    const result = offlineSend(session, step.message)
    session = result.session
    turn = result.turn
  }
  if (!turn) throw new Error(`Guided path ${path.id} has no steps`)
  return turn
}

describe('guided demo path definitions', () => {
  it('has unique path ids and well-formed steps', () => {
    const pathIds = GUIDED_DEMO_PATHS.map((path) => path.id)
    expect(new Set(pathIds).size).toBe(pathIds.length)

    for (const path of GUIDED_DEMO_PATHS) {
      expect(path.title.length).toBeGreaterThan(0)
      expect(path.description.length).toBeGreaterThan(0)
      expect(path.expectedOutcome.length).toBeGreaterThan(0)
      expect(path.steps.length).toBeGreaterThan(0)

      const stepIds = path.steps.map((step) => step.id)
      expect(new Set(stepIds).size).toBe(stepIds.length)
      for (const step of path.steps) {
        expect(step.message.trim().length).toBeGreaterThan(0)
      }
    }
  })

  it('routes the premium path to billing with a premium classification', () => {
    const path = GUIDED_DEMO_PATHS.find((entry) => entry.id === 'premium-billing')
    expect(path).toBeDefined()

    const turn = applyPath(path as GuidedDemoPath)
    expect(turn.authenticated).toBe(true)
    expect(turn.classification).toBe('premium')
    expect(turn.routing_status).toBe('routed')
    expect(turn.support_department).toBe('Insurance and Billing Department')
  })

  it('routes the regular path to standard support', () => {
    const path = GUIDED_DEMO_PATHS.find((entry) => entry.id === 'regular-appointment')
    expect(path).toBeDefined()

    const turn = applyPath(path as GuidedDemoPath)
    expect(turn.authenticated).toBe(true)
    expect(turn.classification).toBe('regular')
    expect(turn.routing_status).toBe('routed')
    expect(turn.support_department).toBe('Standard Patient Support')
  })

  it('asks for more detail on the ambiguous path', () => {
    const path = GUIDED_DEMO_PATHS.find((entry) => entry.id === 'clarification')
    expect(path).toBeDefined()

    const turn = applyPath(path as GuidedDemoPath)
    expect(turn.identified).toBe(false)
    expect(turn.authenticated).toBe(false)
    expect(turn.reply).toContain("wasn't able to verify you")
  })

  it('terminates the failed verification path as a non-client', () => {
    const path = GUIDED_DEMO_PATHS.find((entry) => entry.id === 'failed-verification')
    expect(path).toBeDefined()

    const turn = applyPath(path as GuidedDemoPath)
    expect(turn.terminated).toBe(true)
    expect(turn.reply).toContain('not currently a client')
  })
})
