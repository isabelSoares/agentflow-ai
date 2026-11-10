import { useEffect, useRef, useState, type FormEvent } from 'react'
import type { ChatMessage, DemoSource, GuidedDemoPath, Telemetry } from '../types'
import { DemoGuide } from './DemoGuide'
import { GuidedDemoPaths } from './GuidedDemoPaths'

const SUGGESTIONS = [
  'Hi there!',
  'I need help with a medical bill.',
  "Hi, I'm Lisa — my phone is +14155552671 and my date of birth is 1990-01-15.",
]

interface ChatPanelProps {
  messages: ChatMessage[]
  busy: boolean
  source: DemoSource
  sessionActive: boolean
  error: string | null
  guidedPaths: GuidedDemoPath[]
  activePath: GuidedDemoPath | null
  pathStepIndex: number
  telemetry: Telemetry
  onSend: (text: string) => Promise<void>
  onReset: () => Promise<void>
  onStart: () => Promise<void>
  onRetryLive: () => Promise<void>
  onSelectPath: (pathId: string) => void
  onNextStep: () => void
  onRestartPath: () => void
  onChooseAnotherPath: () => void
}

export function ChatPanel({
  messages,
  busy,
  source,
  sessionActive,
  error,
  guidedPaths,
  activePath,
  pathStepIndex,
  telemetry,
  onSend,
  onReset,
  onStart,
  onRetryLive,
  onSelectPath,
  onNextStep,
  onRestartPath,
  onChooseAnotherPath,
}: ChatPanelProps) {
  const [draft, setDraft] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const hasUserMessages = messages.some((message) => message.role === 'user')
  const offlineMode = source === 'offline'

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, busy])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || busy) return
    setDraft('')
    await onSend(text)
  }

  return (
    <section className="panel chat-panel" aria-label="Support conversation">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Interactive patient demo</p>
          <h2>Patient support conversation</h2>
        </div>
        <div className="chat-actions">
          {offlineMode && (
            <button
              type="button"
              className="button button-ghost"
              onClick={() => void onRetryLive()}
              disabled={busy}
            >
              {busy ? 'Connecting...' : 'Try live service'}
            </button>
          )}
          {sessionActive ? (
            <button
              type="button"
              className="button button-ghost"
              onClick={() => void onReset()}
              disabled={busy}
            >
              Reset session
            </button>
          ) : (
            <button
              type="button"
              className="button button-ghost"
              onClick={() => void onStart()}
              disabled={busy}
            >
              {busy ? 'Starting...' : 'Start session'}
            </button>
          )}
        </div>
      </div>

      {offlineMode && (
        <p className="offline-notice" role="status">
          <strong>Offline demo mode.</strong> This page is a static build without an API backend, so
          the deterministic demo scenario runs in your browser instead of against the FastAPI
          service. Use <em>Try live service</em> when a backend is available, or run the full stack
          locally for the live API flow.
        </p>
      )}

      {!offlineMode && <DemoGuide />}

      <div className="messages" aria-live="polite">
        {messages.map((message) => (
          <article key={message.id} className={`message message-${message.role}`}>
            <span className="message-role">
              {message.role === 'user' ? 'You' : 'AgentFlow AI'}
            </span>
            <p>{message.text}</p>
          </article>
        ))}

        {busy && (
          <div className="message message-assistant message-typing" aria-label="Agent is processing">
            <span className="message-role">AgentFlow AI</span>
            <span className="typing-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {error && (
        <p className="error-banner" role="alert">
          {error}
        </p>
      )}

      {offlineMode ? (
        <GuidedDemoPaths
          paths={guidedPaths}
          activePath={activePath}
          stepIndex={pathStepIndex}
          busy={busy}
          telemetry={telemetry}
          onSelectPath={onSelectPath}
          onNextStep={onNextStep}
          onRestart={onRestartPath}
          onChooseAnother={onChooseAnotherPath}
        />
      ) : (
        <>
          {!hasUserMessages && (
            <div className="suggestions">
              <p className="suggestions-label">Healthcare demo scenario</p>
              <div className="suggestion-list">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    className="suggestion"
                    onClick={() => void onSend(suggestion)}
                    disabled={busy || !sessionActive}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
              <p className="suggestion-hint">
                Chat freely — the demo evaluates the details you share against its fictional
                records. Use the sample identity above to complete verification. The full live flow
                needs a configured LLM provider; without a key, the API uses safe deterministic
                adapters.
              </p>
            </div>
          )}

          <form
            className="composer"
            onSubmit={(event) => {
              void submit(event)
            }}
          >
            <label className="sr-only" htmlFor="message-input">
              Message
            </label>
            <input
              id="message-input"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={sessionActive ? 'Ask a support question...' : 'Start a session to begin'}
              disabled={busy || !sessionActive}
              maxLength={2000}
              autoComplete="off"
            />
            <button
              type="submit"
              className="button button-primary"
              disabled={busy || !sessionActive || !draft.trim()}
            >
              Send
            </button>
          </form>
        </>
      )}
    </section>
  )
}
