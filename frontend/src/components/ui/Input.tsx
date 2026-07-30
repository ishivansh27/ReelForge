import { type InputHTMLAttributes, type ReactNode, forwardRef } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { leadingIcon, trailingIcon, className, ...rest },
  ref
) {
  return (
    <div
      className={clsx(
        "flex h-12 items-center gap-3 rounded-2xl border border-border bg-surface px-4",
        "focus-within:border-accent/60 focus-within:ring-1 focus-within:ring-accent/60",
        className
      )}
    >
      {leadingIcon && <span className="shrink-0 text-text-secondary">{leadingIcon}</span>}
      <input
        ref={ref}
        className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-secondary focus:outline-none"
        {...rest}
      />
      {trailingIcon && <span className="shrink-0 text-text-secondary">{trailingIcon}</span>}
    </div>
  );
});
