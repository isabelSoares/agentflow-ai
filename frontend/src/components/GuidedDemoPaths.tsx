import { PROJECT_SUMMARY } from '../demoGuidance'
import type { GuidedDemoPath, Telemetry } from '../types'

interface GuidedDemoPathsProps {
  paths: GuidedDemoPath[]
  activePath: GuidedDemoPath | null
  stepIndex: number
  busy: boolean
  telemetry: Telemetry
  onSelectPath: (pathId: string) => void
  onNextStep: () => void
  onRestart: () => void
  onChooseAnother: () => void
}

function outcomeDetails(telemetry: Telemetry): string[] {
  const details: string[] = []
  if (telemetry.classification) {
    details.push(`Classification: ${telemetry.classification}`)
  }
  if (telemetry.routingStatus === 'routed' && telemetry.supportDepartment) {
    details.push(`Routed to ${telemetry.supportDepartment}`)
  } else if (telemetry.routingStatus === 'clarification_required') {
    details.push('More identifying detail requested')
  } else if (telemetry.routingStatus === 'fallback') {
    details.push('Request not routed')
  }
  if (telemetry.terminated) {
    details.push('Verification terminated')
  }
  return details
}

export function GuidedDemoPaths({
  paths,
  activePath,
  stepIndex,
  busy,
  telemetry,
  onSelectPath,
  onNextStep,
  onRestart,
  onChooseAnother,
}: GuidedDemoPathsProps) {
  const total = activePath?.steps.length ?? 0
  const complete = activePath !== null && stepIndex >= total
  const currentStep = activePath && !complete ? activePath.steps[stepIndex] : null
  const details = complete ? outcomeDetails(telemetry) : []

  const status = (() => {
    if (!activePath) return 'Guided demo paths available.'
    if (complete) return `Path complete. ${activePath.expectedOutcome}`
    const label = currentStep?.label ?? 'Next message'
    return `Step ${stepIndex + 1} of ${total}: ${label}`
  })()

  return (
    <section className="guided-demo" aria-label="Guided demo paths">
      <p className="guided-demo-note">
        This is a scripted walkthrough. {PROJECT_SUMMARY} Pick a path and use{' '}
        <strong>Next step</strong>; you won&apos;t need to type anything.
      </p>

      <p
        className="guided-status"
        aria-live="polite"
        aria-atomic="true"
        aria-label="Guided demo status"
      >
        {status}
      </p>

      {!activePath ? (
        <div className="guided-path-list" role="group" aria-label="Choose a guided demo path">
          {paths.map((path) => (
            <button
              key={path.id}
              type="button"
              className="guided-path"
              onClick={() => onSelectPath(path.id)}
              disabled={busy}
            >
              <span className="guided-path-title">{path.title}</span>
              <span className="guided-path-description">{path.description}</span>
              <span className="guided-path-outcome">Outcome: {path.expectedOutcome}</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="guided-active">
          <div className="guided-active-header">
            <h3>{activePath.title}</h3>
            <p>{activePath.description}</p>
          </div>

          <p className="guided-progress">
            {complete ? 'Path complete' : `Step ${stepIndex + 1} of ${total}`}
          </p>

          {complete ? (
            <div className="guided-outcome">
              <strong>{activePath.expectedOutcome}</strong>
              {details.length > 0 && (
                <ul>
                  {details.map((detail) => (
                    <li key={detail}>{detail}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            currentStep && (
              <>
                <div className="guided-prepared">
                  <span className="guided-prepared-label">
                    {currentStep.label ?? 'Next message'}
                  </span>
                  <p className="guided-prepared-message" data-testid="guided-prepared-message">
                    {currentStep.message}
                  </p>
                </div>
                <button
                  type="button"
                  className="button button-primary"
                  onClick={onNextStep}
                  disabled={busy}
                >
                  Next step
                </button>
              </>
            )
          )}

          <div className="guided-controls">
            <button
              type="button"
              className="button button-ghost"
              onClick={onRestart}
              disabled={busy}
            >
              Restart
            </button>
            <button
              type="button"
              className="button button-ghost"
              onClick={onChooseAnother}
              disabled={busy}
            >
              Choose another path
            </button>
          </div>
        </div>
      )}
    </section>
  )
}
