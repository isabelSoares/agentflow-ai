import { useEffect, useRef, useState, type FormEvent } from 'react'
import type { ChatMessage } from '../types'

const SUGGESTIONS = [
  "Hi, I'm Lisa. My phone is +14155552671 and my date of birth is 1990-01-15.",
  "My dog's name is Yoda.",
  'I need help with a medical bill.',
]

interface ChatPanelProps {
  messages: ChatMessage[]
  busy: boolean
  sessionActive: boolean
  error: string | null
  offlineMode: boolean
  offlineAvailable: boolean
  onSend: (text: string) => Promise<void>
  onReset: () => Promise<void>
  onStart: () => Promise<void>
  onStartOffline: () => void
}

export function ChatPanel({
  messages,
  busy,
  sessionActive,
  error,
  offlineMode,
  offlineAvailable,
  onSend,
  onReset,
  onStart,
  onStartOffline,
}: ChatPanelProps) {
  const [draft, setDraft] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const hasUserMessages = messages.some((message) => message.role === 'user')

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
          <p className="eyebrow">Interactive demo</p>
          <h2>Support conversation</h2>
        </div>
        <div className="chat-actions">
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
            <>
              <button
                type="button"
                className="button button-ghost"
                onClick={() => void onStart()}
                disabled={busy}
              >
                {busy ? 'Starting...' : 'Start session'}
              </button>
              {offlineAvailable && (
                <button
                  type="button"
                  className="button button-ghost"
                  onClick={onStartOffline}
                  disabled={busy}
                >
                  Run offline demo
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {offlineMode && (
        <p className="suggestion-hint" role="status">
          Offline demo mode: this page is a static build without an API backend, so the
          deterministic demo scenario runs in your browser instead of against the FastAPI
          service. Run the full stack locally for the live API flow.
        </p>
      )}

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
            The full live flow needs a configured LLM provider. Without a key, the API uses safe
            deterministic adapters.
          </p>
        </div>
      )}

      {error && (
        <p className="error-banner" role="alert">
          {error}
        </p>
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
    </section>
  )
}
