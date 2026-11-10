import type { ScenarioStep } from './types'

export const PROJECT_SUMMARY =
  'AgentFlow AI is a secure multi-agent patient-support demo. Each request moves through ' +
  'deterministic identity verification, authorization, classification, and care-team routing, ' +
  'while the model stays advisory and never grants access.'

export const SAMPLE_IDENTITY =
  "Hi, I'm Lisa — my phone is +14155552671 and my date of birth is 1990-01-15."

export const SAMPLE_SECRET_ANSWER = 'Yoda'

export const SAMPLE_REQUEST = 'Can you help me with a billing question?'

export const SCENARIO_STEPS: ScenarioStep[] = [
  {
    order: 1,
    instruction: 'Introduce yourself with the sample name plus the phone number or date of birth.',
    example: SAMPLE_IDENTITY,
  },
  {
    order: 2,
    instruction: 'Answer the security question with the sample answer.',
    example: SAMPLE_SECRET_ANSWER,
  },
  {
    order: 3,
    instruction: 'Ask for billing help to watch the request get routed.',
    example: SAMPLE_REQUEST,
  },
]

export const SAMPLE_DATA_NOTE =
  'The sample record is fictional and exists only to demonstrate the deterministic workflow. ' +
  'In a live session you can type your own details in any format; only the sample identity can ' +
  'complete verification, while other details follow the non-client outcome.'

export const LIVE_NOTE =
  'When an API backend is connected, the same steps run against the live service.'
