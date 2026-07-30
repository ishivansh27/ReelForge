import clsx from "clsx";
import { Check } from "lucide-react";

export function StepBadge({
  number,
  state,
}: {
  number: number;
  state: "done" | "active" | "upcoming";
}) {
  return (
    <div
      className={clsx(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
        state === "done" && "bg-success text-black",
        state === "active" && "bg-accent text-white",
        state === "upcoming" && "border border-border bg-surface text-text-secondary"
      )}
    >
      {state === "done" ? <Check size={16} strokeWidth={3} /> : number}
    </div>
  );
}
