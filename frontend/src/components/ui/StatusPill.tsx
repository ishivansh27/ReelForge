import clsx from "clsx";

export type PillTone = "success" | "neutral" | "accent" | "error";

const TONE_CLASSES: Record<PillTone, string> = {
  success: "bg-success/10 text-success border-success/30",
  neutral: "bg-transparent text-text-secondary border-border",
  accent: "bg-accent/10 text-accent border-accent/30",
  error: "bg-error/10 text-error border-error/30",
};

export function StatusPill({ label, tone = "neutral" }: { label: string; tone?: PillTone }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium capitalize",
        TONE_CLASSES[tone]
      )}
    >
      {label}
    </span>
  );
}
