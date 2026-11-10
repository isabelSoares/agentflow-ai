import { describe, expect, it } from 'vitest'
import { GUIDED_DEMO_PATHS } from '../guidedDemoPaths'
import { createOfflineSession, offlineSend } from '../offlineDemo'
import type { ConversationTurn, GuidedDemoPath } from '../types'

const FICTIONAL_PHONES = new Set([
  '+14155552671',
  '+12025550123',
  '+351912345678',
  '+15550001111',
])

const FICTIONAL_DATES = new Set(['1990-01-15', '1978-11-03', '1992-06-04'])

const FORBIDDEN_PATH_PATTERNS = [
  /password/i,
  /api[_-]?key/i,
  /secret[_-]?key/i,
  /bearer\s/i,
  /sk-[A-Za-z0-9_-]{20,}/,
  /AKIA[0-9A-Z]{16}/,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
  /\b[45]\d\d\b/,
  /[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/,
]

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

  it('uses only fictional demo data with no credentials or raw status codes', () => {
    const values = GUIDED_DEMO_PATHS.flatMap((path) => [
      path.id,
      path.title,
      path.description,
      path.expectedOutcome,
      ...path.steps.flatMap((step) => [step.id, step.label ?? '', step.message]),
    ])

    for (const value of values) {
      for (const pattern of FORBIDDEN_PATH_PATTERNS) {
        expect(value).not.toMatch(pattern)
      }
    }
  })

  it('references only the documented fictional phone numbers and dates of birth', () => {
    for (const path of GUIDED_DEMO_PATHS) {
      for (const step of path.steps) {
        for (const phone of step.message.match(/\+\d{6,}/g) ?? []) {
          expect(FICTIONAL_PHONES.has(phone)).toBe(true)
        }
        for (const date of step.message.match(/\b\d{4}-\d{2}-\d{2}\b/g) ?? []) {
          expect(FICTIONAL_DATES.has(date)).toBe(true)
        }
      }
    }
  })
})
