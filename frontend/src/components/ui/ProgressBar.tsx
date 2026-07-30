import clsx from "clsx";

export function ProgressBar({
  percent,
  showLabel = true,
  tone = "accent",
  className,
}: {
  percent: number;
  showLabel?: boolean;
  tone?: "accent" | "success";
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div className={clsx("flex items-center gap-3", className)}>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface">
        <div
          className={clsx("h-full rounded-full transition-all duration-500", tone === "accent" ? "bg-accent" : "bg-success")}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && <span className="w-10 shrink-0 text-right text-xs font-medium text-text-secondary">{Math.round(clamped)}%</span>}
    </div>
  );
}
