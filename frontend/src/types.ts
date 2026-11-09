export interface ConversationTurn {
  conversation_id: string
  reply: string
  identified: boolean
  authenticated: boolean
  terminated: boolean
  classification: string | null
  routing_status: string | null
  routing_intent: string | null
  support_department: string | null
}

export interface Session {
  id: string
  proof: string | null
}

export interface ChatMessage {
  id: string
  role: 'assistant' | 'user' | 'system'
  text: string
}

export type DemoSource = 'none' | 'live' | 'offline'

export type BackendAvailability = 'available' | 'unavailable' | 'error'

export interface ScenarioStep {
  order: number
  instruction: string
  example: string | null
}

export interface Telemetry {
  identified: boolean
  authenticated: boolean
  terminated: boolean
  classification: string | null
  routingStatus: string | null
  routingIntent: string | null
  supportDepartment: string | null
}

export const EMPTY_TELEMETRY: Telemetry = {
  identified: false,
  authenticated: false,
  terminated: false,
  classification: null,
  routingStatus: null,
  routingIntent: null,
  supportDepartment: null,
}
