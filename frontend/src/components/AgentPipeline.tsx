import type { Telemetry } from '../types'

type StageState = 'complete' | 'active' | 'idle' | 'on'

interface Stage {
  name: string
  detail: string
  state: StageState
}

const STATE_LABELS: Record<StageState, string> = {
  complete: 'Done',
  active: 'Running',
  idle: 'Waiting',
  on: 'Always on',
}

function buildStages(telemetry: Telemetry, busy: boolean): Stage[] {
  const identityComplete = telemetry.identified || telemetry.authenticated
  const routingComplete = Boolean(
    telemetry.routingStatus || telemetry.routingIntent || telemetry.supportDepartment,
  )

  return [
    {
      name: 'Intake & input guardrails',
      detail: 'Policy checks before any model call',
      state: 'on',
    },
    {
      name: 'Identity',
      detail: 'Deterministic 2-of-3 matching',
      state: identityComplete ? 'complete' : busy ? 'active' : 'idle',
    },
    {
      name: 'Authorization',
      detail: 'Secret-answer verification',
      state: telemetry.authenticated
        ? 'complete'
        : busy && telemetry.identified
          ? 'active'
          : 'idle',
    },
    {
      name: 'Classification',
      detail: 'Customer relationship resolution',
      state: telemetry.classification
        ? 'complete'
        : busy && telemetry.authenticated
          ? 'active'
          : 'idle',
    },
    {
      name: 'Routing',
      detail: 'Intent and department selection',
      state: routingComplete ? 'complete' : busy && telemetry.authenticated ? 'active' : 'idle',
    },
    {
      name: 'Output guardrails',
      detail: 'Safe response boundary',
      state: 'on',
    },
  ]
}

interface AgentPipelineProps {
  telemetry: Telemetry
  busy: boolean
}

export function AgentPipeline({ telemetry, busy }: AgentPipelineProps) {
  const stages = buildStages(telemetry, busy)

  return (
    <ol className="pipeline">
      {stages.map((stage) => (
        <li key={stage.name} className={`pipeline-step is-${stage.state}`}>
          <span className="pipeline-dot" aria-hidden="true" />
          <div className="pipeline-copy">
            <div className="pipeline-name">
              <span>{stage.name}</span>
              <span className="pipeline-state">{STATE_LABELS[stage.state]}</span>
            </div>
            <p>{stage.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  )
}
