const steps = [
  "validating specification",
  "preparing geometry",
  "applying materials",
  "applying label",
  "rendering views",
  "exporting model",
  "saving outputs",
];

export function StatusTimeline({ currentStep, complete }: { currentStep: string; complete?: boolean }) {
  const active = complete ? steps.length - 1 : Math.max(0, steps.indexOf(currentStep));
  return (
    <div aria-label="Render status" aria-live="polite">
      {steps.map((step, index) => (
        <div className="stage" key={step}>
          <span className={`dot ${index <= active ? "active" : ""}`} aria-hidden="true" />
          <span>{step}</span>
          <span className="stage-state">{index < active || complete ? "complete" : index === active ? "current" : "waiting"}</span>
        </div>
      ))}
    </div>
  );
}
