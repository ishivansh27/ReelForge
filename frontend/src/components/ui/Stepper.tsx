import { StepBadge } from "./StepBadge";
import clsx from "clsx";

const STEPS = ["Reference", "Blueprint", "Assets"];

export function Stepper({ activeStep }: { activeStep: 1 | 2 | 3 }) {
  return (
    <div className="flex items-center justify-center gap-3 sm:gap-6">
      {STEPS.map((label, i) => {
        const stepNumber = i + 1;
        const state = stepNumber < activeStep ? "done" : stepNumber === activeStep ? "active" : "upcoming";
        return (
          <div key={label} className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <StepBadge number={stepNumber} state={state} />
              <span className={clsx("hidden text-sm font-medium sm:inline", state === "active" ? "text-text-primary" : "text-text-secondary")}>
                {stepNumber} {label}
              </span>
            </div>
            {i < STEPS.length - 1 && <div className="h-px w-8 bg-border sm:w-16" />}
          </div>
        );
      })}
    </div>
  );
}
