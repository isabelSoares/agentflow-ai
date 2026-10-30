import { useEffect, useRef, useState } from 'react'
import { createConversation, resetConversation, sendMessage } from './api'
import { ChatPanel } from './components/ChatPanel'
import { TelemetryPanel } from './components/TelemetryPanel'
import {
  EMPTY_TELEMETRY,
  type ChatMessage,
  type ConversationTurn,
  type Session,
  type Telemetry,
} from './types'

const STARTER_MESSAGES: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    text: 'Start a session to watch the AgentFlow workflow identify, authorize, classify, and route a support request.',
  },
]

const PRINCIPLES = [
  {
    index: '01',
    title: 'Security by design',
    body: 'Identity matching, secret verification, authorization, and routing are deterministic and independently testable.',
  },
  {
    index: '02',
    title: 'Human oversight',
    body: 'Guardrails constrain what the model can say and do. The model never grants access or invents policy.',
  },
  {
    index: '03',
    title: 'Observability',
    body: 'Every turn exposes sanitized state, routing decisions, and agent progress without leaking customer data.',
  },
  {
    index: '04',
    title: 'Evaluation-driven',
    body: 'A large offline suite, typed contracts, and CI checks make agent behavior measurable and regression-resistant.',
  },
]

function messageId(): string {
  return crypto.randomUUID()
}

function toMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}

function telemetryFromTurn(turn: ConversationTurn): Telemetry {
  return {
    identified: turn.identified,
    authenticated: turn.authenticated,
    terminated: turn.terminated,
    classification: turn.classification,
    routingStatus: turn.routing_status,
    routingIntent: turn.routing_intent,
    supportDepartment: turn.support_department,
  }
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>(STARTER_MESSAGES)
  const [session, setSession] = useState<Session | null>(null)
  const [telemetry, setTelemetry] = useState<Telemetry>(EMPTY_TELEMETRY)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const started = useRef(false)

  async function startSession() {
    setBusy(true)
    setError(null)
    try {
      const { turn, proof } = await createConversation()
      setSession({ id: turn.conversation_id, proof })
      setTelemetry(EMPTY_TELEMETRY)
      setMessages([{ id: messageId(), role: 'assistant', text: turn.reply }])
    } catch (caught) {
      setError(toMessage(caught))
      setSession(null)
      setTelemetry(EMPTY_TELEMETRY)
      setMessages(STARTER_MESSAGES)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    if (started.current) return
    started.current = true
    void startSession()
  }, [])

  async function handleSend(text: string) {
    if (!session || busy) return
    setBusy(true)
    setError(null)
    setMessages((current) => [...current, { id: messageId(), role: 'user', text }])

    try {
      const { turn, proof } = await sendMessage(session.id, session.proof, text)
      if (proof) setSession({ id: turn.conversation_id, proof })
      setTelemetry(telemetryFromTurn(turn))
      setMessages((current) => [
        ...current,
        { id: messageId(), role: 'assistant', text: turn.reply },
      ])
    } catch (caught) {
      setError(toMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleReset() {
    if (!session || busy) return
    setBusy(true)
    setError(null)
    try {
      const { turn, proof } = await resetConversation(session.id, session.proof)
      setSession({ id: turn.conversation_id, proof })
      setTelemetry(EMPTY_TELEMETRY)
      setMessages([{ id: messageId(), role: 'assistant', text: turn.reply }])
    } catch (caught) {
      setError(toMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="#top" aria-label="AgentFlow AI home">
          <span className="brand-mark" aria-hidden="true">
            AF
          </span>
          <span>
            <strong>AgentFlow AI</strong>
            <small>Secure multi-agent support</small>
          </span>
        </a>
        <nav className="site-nav" aria-label="Primary">
          <a href="#demo">Demo</a>
          <a href="#principles">Principles</a>
          <a href="#architecture">Architecture</a>
          <a href="https://github.com/isabelSoares/agentflow-ai" target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API docs
          </a>
        </nav>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">Independent AI engineering project</p>
            <h1>Secure multi-agent customer support, end to end.</h1>
            <p className="hero-body">
              AgentFlow AI explores how specialized agents collaborate to deliver secure,
              context-aware support. Natural-language understanding meets deterministic identity
              verification, authorization, customer classification, and intelligent routing.
            </p>
            <div className="tech-pills" aria-label="Technology stack">
              <span>Python</span>
              <span>FastAPI</span>
              <span>LangGraph</span>
              <span>React</span>
              <span>TypeScript</span>
            </div>
          </div>
          <div className="hero-aside">
            <div className="hero-card">
              <span className="hero-card-label">Reference scenario</span>
              <strong>Banking support</strong>
              <p>
                The current demo adapter exercises identity, authorization, classification, and
                department routing with a small seed dataset.
              </p>
              <span className="hero-card-note">Core workflow stays domain-agnostic.</span>
            </div>
          </div>
        </section>

        <section className="workspace" id="demo" aria-label="AgentFlow interactive demo">
          <ChatPanel
            messages={messages}
            busy={busy}
            sessionActive={Boolean(session)}
            error={error}
            onSend={handleSend}
            onReset={handleReset}
            onStart={startSession}
          />
          <TelemetryPanel telemetry={telemetry} session={session} busy={busy} />
        </section>

        <section className="principles" id="principles">
          <div className="section-intro">
            <p className="eyebrow">Engineering principles</p>
            <h2>Responsible agents need more than a prompt.</h2>
            <p>
              The project treats orchestration, security boundaries, observability, and evaluation
              as first-class engineering concerns.
            </p>
          </div>
          <div className="principle-grid">
            {PRINCIPLES.map((principle) => (
              <article className="principle-card" key={principle.index}>
                <span className="principle-index">{principle.index}</span>
                <h3>{principle.title}</h3>
                <p>{principle.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="architecture" id="architecture">
          <div className="section-intro">
            <p className="eyebrow">Architecture</p>
            <h2>Typed contracts, explicit state, visible decisions.</h2>
            <p>
              FastAPI exposes session-scoped endpoints. LangGraph runs a stateful per-turn
              workflow. React renders the conversation and sanitized telemetry. Deterministic nodes
              own every security decision.
            </p>
          </div>
          <div className="architecture-grid">
            <article className="architecture-card">
              <span className="architecture-kicker">Orchestration</span>
              <h3>LangGraph workflow</h3>
              <p>
                Explicit nodes and routing keep multi-turn behavior reviewable, testable, and
                independent from the model provider.
              </p>
              <code>guardrails → extract → identify → authenticate → classify → route</code>
            </article>
            <article className="architecture-card">
              <span className="architecture-kicker">Trust boundary</span>
              <h3>Deterministic security core</h3>
              <p>
                Identity matching, secret answers, session proofs, and department routing are
                implemented as pure Python logic with focused tests.
              </p>
              <code>LLM advisory only · no model-granted access</code>
            </article>
            <article className="architecture-card">
              <span className="architecture-kicker">Full stack</span>
              <h3>Observable by default</h3>
              <p>
                Sanitized turn state drives the UI, while structured logs, traces, and CI checks
                make agent behavior measurable.
              </p>
              <code>FastAPI · React · TypeScript · GitHub Actions</code>
            </article>
          </div>
          <p className="architecture-note">
            Read the <a href="https://github.com/isabelSoares/agentflow-ai#readme">project README</a>{' '}
            and <a href="https://github.com/isabelSoares/agentflow-ai/tree/main/docs">architecture docs</a>{' '}
            for the full component, workflow, and security views.
          </p>
        </section>
      </main>

      <footer className="site-footer">
        <span>AgentFlow AI</span>
        <span>Independent project by Isabel Soares</span>
        <span>Built with Python, FastAPI, LangGraph, React, and TypeScript</span>
      </footer>
    </div>
  )
}

export default App
