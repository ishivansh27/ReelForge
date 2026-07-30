import type { ProjectStatus } from "@/types/api";
import type { PillTone } from "@/components/ui/StatusPill";

export const PROJECT_STATUS_META: Record<ProjectStatus, { label: string; description: string; tone: PillTone }> = {
  pending: { label: "Queued", description: "Waiting to start downloading the reference video.", tone: "neutral" },
  downloading: { label: "Downloading", description: "Downloading the reference video.", tone: "accent" },
  analyzing: {
    label: "Analyzing",
    description: "Detecting scenes, camera movement, beats, and on-screen text.",
    tone: "accent",
  },
  blueprint_ready: { label: "Blueprint Ready", description: "Assembling the required-asset list.", tone: "accent" },
  awaiting_assets: { label: "Awaiting Assets", description: "Upload your photos and clips to fill the scenes.", tone: "neutral" },
  matching: { label: "Matched", description: "Assets matched -- ready to render.", tone: "success" },
  rendering: { label: "Rendering", description: "Stitching your final video together.", tone: "accent" },
  completed: { label: "Completed", description: "Your video is ready.", tone: "success" },
  failed: { label: "Failed", description: "Something went wrong during processing.", tone: "error" },
};

export function formatCameraMovement(type: string | null | undefined) {
  if (!type) return "Unknown";
  return type
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export function formatTimestamp(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
