import type { ConversationTurn } from './types'

/**
 * Offline demo engine.
 *
 * The GitHub Pages build is a static site: there is no FastAPI backend behind
 * it, so `POST /api/...` is rejected by the static host with 405. This module
 * runs the same deterministic demo scenario in the browser so the live page
 * still works: it mirrors the seed dataset, the 2-of-3 identity matching, the
 * secret-question check, and the premium/regular routing of the backend's
 * scripted adapters (see `src/healthcare_support/data/seed.py`,
 * `core/matching.py`, `core/verification.py`, and `core/routing.py`).
 */

const MAX_ATTEMPTS = 3

const GREETING =
  "Hello! I'm your healthcare support assistant. " +
  'To get started, could you please tell me your name, phone number, or date of birth?'

const ASK_MORE_ATTRIBUTES =
  "I need a bit more information because I wasn't able to verify you. " +
  'Please provide another detail, such as your name, phone number, or date of birth.'

const SECRET_QUESTION_PREFIX =
  'Thank you. To complete verification, please answer your security question: '

const WRONG_SECRET_ANSWER = "That answer doesn't match our records. Please try again."

const TERMINATION_GENERIC =
  "I'm sorry, I wasn't able to complete the verification. " +
  'Please contact your healthcare provider for assistance.'

const TERMINATION_NON_CLIENT =
  'Thank you for reaching out. It seems that you are not currently a client. ' +
  'I recommend that you contact our patient support department directly for assistance.'

const AUTHENTICATED_CONFIRMATION =
  'Thank you, your identity has been verified. How can I help you today?'

const PREMIUM_ROUTING =
  'Thank you for reaching out regarding your healthcare request. As a premium patient, ' +
  'we value your experience and are here to assist you. For immediate support, ' +
  'please contact our dedicated support department at +1999888999.'

const REGULAR_ROUTING =
  "I'm sorry to hear that you're having trouble with your healthcare request. Since you're a " +
  'regular client, I recommend that you call our support department at +1112112112 ' +
  'for assistance.'

const CLOSED_CONVERSATION =
  'This verification session has ended. If you need further assistance, ' +
  'please start a new conversation.'

const CLARIFICATION_MESSAGE =
  "I'm not sure I understood your request correctly. Could you tell me whether " +
  'you need help with an appointment, insurance, billing, or another healthcare service?'

const UNINTERPRETABLE_MESSAGE =
  "I'm sorry, I didn't catch that. Could you rephrase what you need help with?"

interface DemoPatient {
  id: string
  name: string
  phone: string
  dateOfBirth: string
  secretQuestion: string
  secretAnswer: string
  premium: boolean
}

const PATIENTS: DemoPatient[] = [
  {
    id: 'cust-1',
    name: 'Lisa',
    phone: '+14155552671',
    dateOfBirth: '1990-01-15',
    secretQuestion: 'Which is the name of my dog?',
    secretAnswer: 'Yoda',
    premium: true,
  },
  {
    id: 'cust-2',
    name: 'Maria Silva',
    phone: '+351912345678',
    dateOfBirth: '1985-07-22',
    secretQuestion: "What is your mother's maiden name?",
    secretAnswer: 'Santos',
    premium: false,
  },
  {
    id: 'cust-3',
    name: 'Maria Souza',
    phone: '+351912345678',
    dateOfBirth: '1987-03-12',
    secretQuestion: 'What was your first car?',
    secretAnswer: 'Gol',
    premium: false,
  },
  {
    id: 'cust-4',
    name: 'John Doe',
    phone: '+12025550123',
    dateOfBirth: '1978-11-03',
    secretQuestion: 'What is your favorite color?',
    secretAnswer: 'Blue',
    premium: false,
  },
]

interface Department {
  key: string
  displayName: string
  contact: string
  specializations: string[]
}

const DEPARTMENTS: Department[] = [
  {
    key: 'standard_support',
    displayName: 'Standard Patient Support',
    contact: '+1112112112',
    specializations: [],
  },
  {
    key: 'premium_support',
    displayName: 'Premium Patient Support',
    contact: '+1999888999',
    specializations: [],
  },
  {
    key: 'insurance_billing',
    displayName: 'Insurance and Billing Department',
    contact: '+18005551234',
    specializations: ['specialist_referral', 'insurance_billing'],
  },
]

type DemoStatus = 'collecting' | 'identified' | 'authenticated' | 'terminated'

export interface OfflineSession {
  conversationId: string
  status: DemoStatus
  matchedPatientId: string | null
  identificationAttempts: number
  secretAnswerAttempts: number
}

function normalizeName(value: string): string {
  return value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .split(/\s+/)
    .join(' ')
}

function namePartsMatch(provided: string, registered: string): boolean {
  const providedNorm = normalizeName(provided)
  const registeredNorm = normalizeName(registered)
  if (!providedNorm || !registeredNorm) return false
  if (providedNorm === registeredNorm) return true
  const registeredParts = new Set(registeredNorm.split(' '))
  const providedParts = providedNorm.split(' ')
  return providedParts.length === 1 && registeredParts.has(providedParts[0])
}

function normalizePhone(value: string): string | null {
  const digits = value.replace(/[^\d+]/g, '')
  if (!/^\+\d{6,15}$/.test(digits)) return null
  return digits
}

function normalizeDateOfBirth(value: string): string | null {
  const match = /^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/.exec(value.trim())
  if (!match) return null
  const [, year, month, day] = match
  const parsed = new Date(Number(year), Number(month) - 1, Number(day))
  if (
    parsed.getFullYear() !== Number(year) ||
    parsed.getMonth() !== Number(month) - 1 ||
    parsed.getDate() !== Number(day)
  ) {
    return null
  }
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
}

function normalizeAnswer(value: string): string | null {
  const answer = value.trim().toLowerCase()
  return answer ? answer : null
}

function extractAttributes(text: string): { name: string | null; phone: string | null; dob: string | null } {
  const phoneMatch = /\+\d[\d\s().-]{5,}\d/.exec(text)
  const phone = phoneMatch ? normalizePhone(phoneMatch[0]) : null

  const dobMatch = /\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b/.exec(text)
  const dob = dobMatch ? normalizeDateOfBirth(dobMatch[1]) : null

  const words = normalizeName(text).split(' ')
  let name: string | null = null
  for (const patient of PATIENTS) {
    const parts = normalizeName(patient.name).split(' ')
    if (parts.every((part) => words.includes(part))) {
      name = patient.name
      break
    }
    const token = words.find((word) => parts.includes(word))
    if (token) {
      name = token
      break
    }
  }

  return { name, phone, dob }
}

function evaluateMatch(attributes: {
  name: string | null
  phone: string | null
  dob: string | null
}): { outcome: 'unique' | 'no_match' | 'ambiguous' | 'insufficient'; patient: DemoPatient | null } {
  const evaluated = [attributes.name, attributes.phone, attributes.dob].filter(Boolean).length
  if (evaluated < 2) return { outcome: 'insufficient', patient: null }

  const matches = PATIENTS.filter((patient) => {
    let score = 0
    if (attributes.name && namePartsMatch(attributes.name, patient.name)) score += 1
    if (attributes.phone && normalizePhone(patient.phone) === attributes.phone) score += 1
    if (attributes.dob && normalizeDateOfBirth(patient.dateOfBirth) === attributes.dob) score += 1
    return score >= 2
  })

  if (matches.length === 1) return { outcome: 'unique', patient: matches[0] }
  if (matches.length > 1) return { outcome: 'ambiguous', patient: null }
  return { outcome: 'no_match', patient: null }
}

function extractSecretAnswer(text: string): string {
  const trimmed = text.trim().replace(/[.!?]+$/, '')
  const prefixed = /^(?:it(?:'| i)s|the answer is|my [\w' -]+ is|it is|answer:)\s+(.+)$/i.exec(trimmed)
  return prefixed ? prefixed[1] : trimmed
}

function classifyIntent(text: string): { intent: string; needsClarification: boolean } {
  const normalized = normalizeName(text)
  if (!normalized) return { intent: 'uninterpretable', needsClarification: false }
  if (/\b(bill|billing|invoice|insurance|coverage|reimburs|claim|pay|payment)\b/.test(normalized)) {
    return { intent: 'insurance', needsClarification: false }
  }
  if (/\b(appointment|schedule|reschedul|book|visit|checkup|consultation)\b/.test(normalized)) {
    return { intent: 'appointment_assistance', needsClarification: false }
  }
  if (/\b(referral|specialist|cardiolog|dermatolog|orthoped|doctor)\b/.test(normalized)) {
    return { intent: 'specialist_referral', needsClarification: false }
  }
  if (/\b(prescription|medication|lab result|test result|symptom)\b/.test(normalized)) {
    return { intent: 'general_healthcare', needsClarification: false }
  }
  if (/^(hi|hello|hey|thanks|thank you)\b/.test(normalized)) {
    return { intent: 'ambiguous', needsClarification: true }
  }
  return { intent: 'other_specialized', needsClarification: false }
}

function routedMessage(department: Department): string {
  return (
    `I'll connect you with the ${department.displayName} at ${department.contact}. ` +
    "They'll be able to assist you with your request."
  )
}

function routeRequest(patient: DemoPatient, intent: string, needsClarification: boolean): {
  reply: string
  routingStatus: string
  routingIntent: string
  supportDepartment: string | null
} {
  if (needsClarification) {
    return {
      reply: CLARIFICATION_MESSAGE,
      routingStatus: 'clarification_required',
      routingIntent: intent,
      supportDepartment: null,
    }
  }
  if (intent === 'uninterpretable') {
    return {
      reply: UNINTERPRETABLE_MESSAGE,
      routingStatus: 'fallback',
      routingIntent: intent,
      supportDepartment: null,
    }
  }
  if (intent === 'insurance' || intent === 'specialist_referral') {
    const department = DEPARTMENTS.find((entry) =>
      entry.specializations.includes(intent === 'insurance' ? 'insurance_billing' : 'specialist_referral'),
    )
    if (department) {
      return {
        reply: routedMessage(department),
        routingStatus: 'routed',
        routingIntent: intent,
        supportDepartment: department.displayName,
      }
    }
  }
  const tier = patient.premium ? 'premium_support' : 'standard_support'
  const department = DEPARTMENTS.find((entry) => entry.key === tier)
  if (department) {
    return {
      reply: routedMessage(department),
      routingStatus: 'routed',
      routingIntent: intent,
      supportDepartment: department.displayName,
    }
  }
  return {
    reply: UNINTERPRETABLE_MESSAGE,
    routingStatus: 'fallback',
    routingIntent: intent,
    supportDepartment: null,
  }
}

function toTurn(session: OfflineSession, reply: string, overrides: Partial<ConversationTurn> = {}): ConversationTurn {
  return {
    conversation_id: session.conversationId,
    reply,
    identified: session.status === 'identified' || session.status === 'authenticated',
    authenticated: session.status === 'authenticated',
    terminated: session.status === 'terminated',
    classification: null,
    routing_status: null,
    routing_intent: null,
    support_department: null,
    ...overrides,
  }
}

export function createOfflineSession(): OfflineSession {
  return {
    conversationId: `offline-${crypto.randomUUID()}`,
    status: 'collecting',
    matchedPatientId: null,
    identificationAttempts: 0,
    secretAnswerAttempts: 0,
  }
}

export function offlineGreeting(session: OfflineSession): ConversationTurn {
  return toTurn(session, GREETING)
}

export function offlineSend(session: OfflineSession, text: string): { session: OfflineSession; turn: ConversationTurn } {
  if (session.status === 'terminated') {
    return { session, turn: toTurn(session, CLOSED_CONVERSATION) }
  }

  if (session.status === 'collecting') {
    const attributes = extractAttributes(text)
    const result = evaluateMatch(attributes)
    if (result.outcome === 'unique' && result.patient) {
      const next: OfflineSession = {
        ...session,
        status: 'identified',
        matchedPatientId: result.patient.id,
      }
      return {
        session: next,
        turn: toTurn(next, `${SECRET_QUESTION_PREFIX}${result.patient.secretQuestion}`),
      }
    }
    if (result.outcome === 'ambiguous' || result.outcome === 'insufficient') {
      return { session, turn: toTurn(session, ASK_MORE_ATTRIBUTES) }
    }
    const attempts = session.identificationAttempts + 1
    if (attempts >= MAX_ATTEMPTS) {
      const next: OfflineSession = { ...session, status: 'terminated', identificationAttempts: attempts }
      return { session: next, turn: toTurn(next, TERMINATION_NON_CLIENT) }
    }
    return {
      session: { ...session, identificationAttempts: attempts },
      turn: toTurn(session, ASK_MORE_ATTRIBUTES),
    }
  }

  if (session.status === 'identified') {
    const patient = PATIENTS.find((entry) => entry.id === session.matchedPatientId)
    if (!patient) {
      return { session, turn: toTurn(session, ASK_MORE_ATTRIBUTES) }
    }
    const provided = extractSecretAnswer(text)
    if (normalizeAnswer(provided) === normalizeAnswer(patient.secretAnswer)) {
      const next: OfflineSession = { ...session, status: 'authenticated' }
      const classification = patient.premium ? 'premium' : 'regular'
      return {
        session: next,
        turn: toTurn(next, patient.premium ? PREMIUM_ROUTING : REGULAR_ROUTING, {
          classification,
        }),
      }
    }
    const attempts = session.secretAnswerAttempts + 1
    if (attempts >= MAX_ATTEMPTS) {
      const next: OfflineSession = { ...session, status: 'terminated', secretAnswerAttempts: attempts }
      return { session: next, turn: toTurn(next, TERMINATION_GENERIC) }
    }
    return {
      session: { ...session, secretAnswerAttempts: attempts },
      turn: toTurn(session, WRONG_SECRET_ANSWER),
    }
  }

  const patient = PATIENTS.find((entry) => entry.id === session.matchedPatientId)
  if (!patient) {
    return { session, turn: toTurn(session, AUTHENTICATED_CONFIRMATION) }
  }
  const { intent, needsClarification } = classifyIntent(text)
  const routing = routeRequest(patient, intent, needsClarification)
  return {
    session,
    turn: toTurn(session, routing.reply, {
      classification: patient.premium ? 'premium' : 'regular',
      routing_status: routing.routingStatus,
      routing_intent: routing.routingIntent,
      support_department: routing.supportDepartment,
    }),
  }
}
