import { describe, expect, it } from 'vitest'
import { createOfflineSession, offlineGreeting, offlineSend } from '../offlineDemo'

describe('offline demo engine', () => {
  it('greets and asks for identifying details', () => {
    const session = createOfflineSession()
    const turn = offlineGreeting(session)
    expect(turn.reply).toContain('name, phone number, or date of birth')
    expect(turn.identified).toBe(false)
    expect(turn.authenticated).toBe(false)
  })

  it('identifies Lisa with 2-of-3 attributes and asks the secret question', () => {
    let session = createOfflineSession()
    const { session: next, turn } = offlineSend(
      session,
      "Hi, I'm Lisa. My phone is +14155552671 and my date of birth is 1990-01-15.",
    )
    session = next
    expect(turn.identified).toBe(true)
    expect(turn.authenticated).toBe(false)
    expect(turn.reply).toContain('Which is the name of my dog?')
  })

  it('identifies Lisa with a local phone format and a day-first date of birth', () => {
    const session = createOfflineSession()
    const { turn } = offlineSend(session, 'Lisa, phone 4155552671, born 15-01-1990.')
    expect(turn.identified).toBe(true)
    expect(turn.reply).toContain('Which is the name of my dog?')
  })

  it('treats a visitor’s own identity as an identity attempt instead of chitchat', () => {
    const session = createOfflineSession()
    const { session: next, turn } = offlineSend(
      session,
      'hi, Isabel Soares, 912345678, 01-01-1990',
    )
    expect(turn.reply).not.toContain('happy to chat')
    expect(turn.reply).toContain("wasn't able to verify you")
    expect(turn.identified).toBe(false)
    expect(next.identificationAttempts).toBe(1)
  })

  it('detects the ambiguous shared phone number and asks for more detail', () => {
    const session = createOfflineSession()
    const { turn } = offlineSend(session, 'My phone is +351912345678 and my name is Maria.')
    expect(turn.identified).toBe(false)
    expect(turn.reply).toContain("wasn't able to verify you")
  })

  it('authenticates with the correct secret answer and applies premium routing', () => {
    let session = createOfflineSession()
    session = offlineSend(
      session,
      "Hi, I'm Lisa. My phone is +14155552671 and my date of birth is 1990-01-15.",
    ).session
    const { session: authed, turn } = offlineSend(session, "My dog's name is Yoda.")
    expect(turn.authenticated).toBe(true)
    expect(turn.classification).toBe('premium')
    expect(turn.reply).toContain('premium patient')

    const routed = offlineSend(authed, 'I need help with a medical bill.')
    expect(routed.turn.routing_status).toBe('routed')
    expect(routed.turn.routing_intent).toBe('insurance')
    expect(routed.turn.support_department).toBe('Insurance and Billing Department')
    expect(routed.turn.reply).toContain('+18005551234')
  })

  it('routes regular patients to standard support', () => {
    let session = createOfflineSession()
    session = offlineSend(
      session,
      'John Doe, phone +12025550123, born 1978-11-03.',
    ).session
    session = offlineSend(session, 'Blue').session
    const routed = offlineSend(session, 'I want to book an appointment.')
    expect(routed.turn.authenticated).toBe(true)
    expect(routed.turn.classification).toBe('regular')
    expect(routed.turn.support_department).toBe('Standard Patient Support')
    expect(routed.turn.reply).toContain('+1112112112')
  })

  it('rejects a wrong secret answer and terminates after 3 attempts', () => {
    let session = createOfflineSession()
    session = offlineSend(
      session,
      "Hi, I'm Lisa. My phone is +14155552671 and my date of birth is 1990-01-15.",
    ).session
    for (let i = 0; i < 2; i += 1) {
      const result = offlineSend(session, 'Rex')
      session = result.session
      expect(result.turn.reply).toContain("doesn't match our records")
      expect(result.turn.terminated).toBe(false)
    }
    const final = offlineSend(session, 'Rex')
    expect(final.turn.terminated).toBe(true)
    expect(final.turn.reply).toContain("wasn't able to complete the verification")

    const after = offlineSend(final.session, 'anything')
    expect(after.turn.reply).toContain('session has ended')
  })

  it('answers chitchat conversationally without consuming an attempt', () => {
    const session = createOfflineSession()
    const { session: next, turn } = offlineSend(session, 'hello there')
    expect(turn.reply).toContain('happy to chat')
    expect(turn.identified).toBe(false)
    expect(next.identificationAttempts).toBe(0)
  })

  it('never terminates no matter how much chitchat is sent', () => {
    let session = createOfflineSession()
    for (let i = 0; i < 10; i += 1) {
      const result = offlineSend(session, 'just chatting, no identity details here')
      session = result.session
      expect(result.turn.reply).toContain('happy to chat')
      expect(result.turn.terminated).toBe(false)
    }
    expect(session.identificationAttempts).toBe(0)
  })

  it('still asks for more detail when only one attribute is provided', () => {
    const session = createOfflineSession()
    const { session: next, turn } = offlineSend(session, 'My name is Lisa.')
    expect(turn.reply).toContain("wasn't able to verify you")
    expect(next.identificationAttempts).toBe(0)
  })

  it('terminates after 3 failed identification attempts', () => {
    let session = createOfflineSession()
    let last = offlineSend(session, 'I am Zed, phone +19999999999, born 2000-01-01.')
    session = last.session
    last = offlineSend(session, 'I am Zed, phone +19999999999, born 2000-01-01.')
    session = last.session
    expect(last.turn.terminated).toBe(false)
    last = offlineSend(session, 'I am Zed, phone +19999999999, born 2000-01-01.')
    expect(last.turn.terminated).toBe(true)
    expect(last.turn.reply).toContain('not currently a client')
  })
})
