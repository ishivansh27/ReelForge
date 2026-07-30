import { Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import clsx from "clsx";

export function Logo({ className }: { className?: string }) {
  return (
    <Link to="/" className={clsx("flex items-center gap-2", className)}>
      <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent text-white">
        <Sparkles size={16} strokeWidth={2.5} />
      </span>
      <span className="text-base font-bold tracking-tight text-text-primary">ReelClone AI</span>
    </Link>
  );
}
