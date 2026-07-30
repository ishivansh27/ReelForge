import type { HTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

export function Card({
  children,
  className,
  elevated = false,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode; elevated?: boolean }) {
  return (
    <div
      className={clsx(
        "rounded-2xl border border-border p-5",
        elevated ? "bg-surface-elevated" : "bg-surface",
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
