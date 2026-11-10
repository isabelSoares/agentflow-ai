import type { GuidedDemoPath } from './types'

/**
 * Guided demo paths.
 *
 * The offline demo used to interpret free-form typing, which made the outcome
 * depend on how a visitor phrased things. These paths instead supply fixed,
 * non-editable messages to the same deterministic `offlineSend` engine, so
 * every visitor sees the workflow branches the demo is meant to show.
 *
 * All values are fictional. Keep prepared messages in sync with the seed
 * records in `offlineDemo.ts`.
 */
export const GUIDED_DEMO_PATHS: GuidedDemoPath[] = [
  {
    id: 'premium-billing',
    title: 'Premium billing journey',
    description:
      'Verify a premium patient and route a billing request to the billing department.',
    expectedOutcome:
      'The patient is verified, classified as premium, and routed to the Insurance and Billing Department.',
    steps: [
      {
        id: 'premium-identity',
        label: 'Share identity',
        message:
          "Hi, I'm Lisa — my phone is +14155552671 and my date of birth is 1990-01-15.",
      },
      {
        id: 'premium-secret',
        label: 'Answer the security question',
        message: 'Yoda',
      },
      {
        id: 'premium-request',
        label: 'Ask for billing help',
        message: 'Can you help me with a billing question?',
      },
    ],
  },
  {
    id: 'regular-appointment',
    title: 'Regular appointment journey',
    description:
      'Verify a regular patient and route an appointment request to standard support.',
    expectedOutcome:
      'The patient is verified, classified as regular, and routed to Standard Patient Support.',
    steps: [
      {
        id: 'regular-identity',
        label: 'Share identity',
        message: 'John Doe, phone +12025550123, born 1978-11-03.',
      },
      {
        id: 'regular-secret',
        label: 'Answer the security question',
        message: 'Blue',
      },
      {
        id: 'regular-request',
        label: 'Ask for an appointment',
        message: 'I want to book an appointment.',
      },
    ],
  },
  {
    id: 'clarification',
    title: 'Ambiguous identity journey',
    description:
      'Share details that match more than one fictional record and watch the demo ask for more.',
    expectedOutcome:
      'The details are ambiguous, so the demo asks for another identifying detail instead of guessing.',
    steps: [
      {
        id: 'clarification-identity',
        label: 'Share an ambiguous identity',
        message: 'My name is Maria and my phone is +351912345678.',
      },
    ],
  },
  {
    id: 'failed-verification',
    title: 'Failed verification journey',
    description:
      'Use an unknown identity three times to show the guardrail that ends verification.',
    expectedOutcome:
      'After three failed identity attempts, verification ends and the visitor is treated as a non-client.',
    steps: [
      {
        id: 'failed-attempt-1',
        label: 'Attempt 1 with an unknown identity',
        message:
          "I'm Daniel Costa. My phone is +15550001111 and I was born 1992-06-04.",
      },
      {
        id: 'failed-attempt-2',
        label: 'Attempt 2 with the same identity',
        message:
          "I'm Daniel Costa. My phone is +15550001111 and I was born 1992-06-04.",
      },
      {
        id: 'failed-attempt-3',
        label: 'Attempt 3 with the same identity',
        message:
          "I'm Daniel Costa. My phone is +15550001111 and I was born 1992-06-04.",
      },
    ],
  },
]

export function findGuidedPath(pathId: string): GuidedDemoPath | undefined {
  return GUIDED_DEMO_PATHS.find((path) => path.id === pathId)
}
