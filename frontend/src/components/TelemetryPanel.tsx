import type { DemoSource, Session, Telemetry } from '../types'
import { AgentPipeline } from './AgentPipeline'

interface TelemetryPanelProps {
  telemetry: Telemetry
  session: Session | null
  source: DemoSource
  busy: boolean
}

function formatValue(value: string | null): string {
  if (!value) return '—'
  return value.replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase())
}

export function TelemetryPanel({ telemetry, session, source, busy }: TelemetryPanelProps) {
  const statusClass = busy
    ? 'is-busy'
    : source === 'offline'
      ? 'is-offline'
      : source === 'live'
        ? 'is-live'
        : 'is-idle'
  const statusLabel = busy
    ? 'Processing'
    : source === 'offline'
      ? 'Offline demo'
      : source === 'live'
        ? 'Session live'
        : 'Idle'

  return (
    <aside className="panel telemetry-panel" aria-label="Agent telemetry">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Live trace</p>
          <h2>Agent telemetry</h2>
        </div>
        <span className={`status-pill ${statusClass}`}>{statusLabel}</span>
      </div>

      <div className="security-grid">
        <div className="security-item">
          <span className="security-label">Session proof</span>
          <strong className={session?.proof ? 'is-good' : 'is-warn'}>
            {session?.proof ? 'Active' : 'Missing'}
          </strong>
        </div>
        <div className="security-item">
          <span className="security-label">Patient identity</span>
          <strong className={telemetry.identified ? 'is-good' : 'is-warn'}>
            {telemetry.identified ? 'Matched' : 'Pending'}
          </strong>
        </div>
        <div className="security-item">
          <span className="security-label">Verification</span>
          <strong className={telemetry.authenticated ? 'is-good' : 'is-warn'}>
            {telemetry.authenticated ? 'Verified' : 'Pending'}
          </strong>
        </div>
        <div className="security-item">
          <span className="security-label">Session state</span>
          <strong className={telemetry.terminated ? 'is-bad' : session ? 'is-good' : 'is-warn'}>
            {telemetry.terminated ? 'Terminated' : session ? 'Open' : 'Closed'}
          </strong>
        </div>
      </div>

      <dl className="telemetry-table">
        <div>
          <dt>Patient class</dt>
          <dd>{formatValue(telemetry.classification)}</dd>
        </div>
        <div>
          <dt>Routing status</dt>
          <dd>{formatValue(telemetry.routingStatus)}</dd>
        </div>
        <div>
          <dt>Support intent</dt>
          <dd>{formatValue(telemetry.routingIntent)}</dd>
        </div>
        <div>
          <dt>Department</dt>
          <dd>{formatValue(telemetry.supportDepartment)}</dd>
        </div>
      </dl>

      <div className="pipeline-section">
        <div className="section-heading">
          <h3>Workflow</h3>
          <span>LangGraph</span>
        </div>
        <AgentPipeline telemetry={telemetry} busy={busy} />
      </div>

      <p className="telemetry-note">
        Security decisions stay deterministic. The language model can interpret a request, but
        it never grants access.
      </p>
    </aside>
  )
}
