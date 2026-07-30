import type { ReactNode } from "react";
import clsx from "clsx";
import { Film, Image as ImageIcon, Play, Sparkles } from "lucide-react";

export function MediaThumbnail({
  src,
  alt,
  aspect = "video",
  topLeft,
  topRight,
  bottomLeft,
  bottomRight,
  center,
  imgClassName,
  className,
}: {
  src?: string | null;
  alt: string;
  aspect?: "video" | "portrait" | "square";
  topLeft?: ReactNode;
  topRight?: ReactNode;
  bottomLeft?: ReactNode;
  bottomRight?: ReactNode;
  center?: ReactNode;
  imgClassName?: string;
  className?: string;
}) {
  const aspectClass = aspect === "video" ? "aspect-video" : aspect === "portrait" ? "aspect-[9/16]" : "aspect-square";

  return (
    <div className={clsx("relative overflow-hidden rounded-2xl bg-surface", aspectClass, className)}>
      {src ? (
        <img src={src} alt={alt} className={clsx("h-full w-full object-cover", imgClassName)} loading="lazy" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-text-secondary">
          <ImageIcon size={28} strokeWidth={1.5} />
        </div>
      )}
      {topLeft && <div className="absolute left-2 top-2">{topLeft}</div>}
      {topRight && <div className="absolute right-2 top-2">{topRight}</div>}
      {bottomLeft && <div className="absolute bottom-2 left-2">{bottomLeft}</div>}
      {bottomRight && <div className="absolute bottom-2 right-2">{bottomRight}</div>}
      {center && <div className="absolute inset-0 flex items-center justify-center">{center}</div>}
    </div>
  );
}

export function Badge({ children, tone = "dark" }: { children: ReactNode; tone?: "dark" | "accent" | "success" }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold backdrop-blur-sm",
        tone === "dark" && "bg-black/60 text-white",
        tone === "accent" && "bg-accent text-white",
        tone === "success" && "bg-success text-black"
      )}
    >
      {children}
    </span>
  );
}

export function PlayOverlayButton() {
  return (
    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/90 text-black shadow-lg transition-transform hover:scale-105">
      <Play size={22} fill="currentColor" className="ml-0.5" />
    </div>
  );
}

export function DashedPlaceholder({ label = "Not yet matched" }: { label?: string }) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-border text-text-secondary">
      <Sparkles size={20} strokeWidth={1.5} />
      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}

export function AssetTypeIcon({ type }: { type: "video" | "photo" }) {
  return type === "video" ? <Film size={12} /> : <ImageIcon size={12} />;
}
