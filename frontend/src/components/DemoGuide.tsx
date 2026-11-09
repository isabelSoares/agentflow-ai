import { LIVE_NOTE, PROJECT_SUMMARY, SAMPLE_DATA_NOTE, SCENARIO_STEPS } from '../demoGuidance'

export function DemoGuide() {
  return (
    <section className="demo-guide" aria-label="Demo guidance">
      <h3>Try this scenario</h3>
      <p className="demo-guide-summary">{PROJECT_SUMMARY}</p>
      <ol className="demo-guide-steps">
        {SCENARIO_STEPS.map((step) => (
          <li key={step.order}>
            <span>{step.instruction}</span>
            {step.example && <code>{step.example}</code>}
          </li>
        ))}
      </ol>
      <p className="demo-guide-note">
        {SAMPLE_DATA_NOTE} {LIVE_NOTE}
      </p>
    </section>
  )
}
