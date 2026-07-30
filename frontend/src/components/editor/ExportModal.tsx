import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { Check, Copy, Download, Loader2, RefreshCw } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Card } from "@/components/ui/Card";
import {
  useAssetSlots,
  useBlueprint,
  useRenderDownloadUrl,
  useRenderJobs,
  useTriggerGapFill,
  useTriggerRender,
} from "@/hooks/useApi";
import type { RenderJobOut } from "@/types/api";

type Phase = "checking" | "gap-filling" | "starting-render" | "rendering" | "done" | "failed";

// The backend's real render_job.progress_percent only ever moves
// through these three ranges (see backend/app/tasks/render.py) --
// downloads 0-50%, the actual FFmpeg render 50-90%, then the S3
// upload 90-100%. Named steps below are honest labels for those real
// ranges, not an invented animation.
const STEPS = [
  { label: "Preparing footage (matched clips + gap-fills)", from: 0, to: 50 },
  { label: "Rendering: transitions, beat sync, color grade, overlays", from: 50, to: 90 },
  { label: "Uploading final video", from: 90, to: 100 },
];

function useElapsedSeconds(active: boolean) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!active) return;
    const start = Date.now();
    const id = setInterval(() => setSeconds(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(id);
  }, [active]);
  return seconds;
}

export function ExportModal({ projectId, open, onClose }: { projectId: string; open: boolean; onClose: () => void }) {
  const [phase, setPhase] = useState<Phase>("checking");
  const [jobId, setJobId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const startedRef = useRef(false);

  const { data: slots, refetch: refetchSlots } = useAssetSlots(projectId, { enabled: open });
  const { data: blueprint } = useBlueprint(projectId, { enabled: open });
  const { data: renderJobs } = useRenderJobs(projectId);
  const triggerGapFill = useTriggerGapFill(projectId);
  const triggerRender = useTriggerRender(projectId);

  const job: RenderJobOut | undefined = renderJobs?.find((j) => j.id === jobId);
  const downloadUrl = useRenderDownloadUrl(projectId, job?.status === "completed" ? jobId ?? undefined : undefined);
  const elapsed = useElapsedSeconds(open && phase !== "done" && phase !== "failed");

  const startNewRender = async () => {
    setStartError(null);
    setPhase("starting-render");
    try {
      const created = await triggerRender.mutateAsync();
      setJobId(created.id);
      setPhase("rendering");
    } catch (err) {
      const detail = axios.isAxiosError(err) ? (err.response?.data as { detail?: string } | undefined)?.detail : undefined;
      setStartError(detail ?? "Could not start the render.");
      setPhase("failed");
    }
  };

  useEffect(() => {
    if (!open) {
      startedRef.current = false;
      setPhase("checking");
      setJobId(null);
      setStartError(null);
      return;
    }
    // renderJobs is undefined until its first fetch resolves -- wait for
    // that so an already-completed render (from a past session) can be
    // detected before deciding to kick off a brand new one.
    if (startedRef.current || !slots || renderJobs === undefined) return;
    startedRef.current = true;

    const latestJob = renderJobs[0];
    if (latestJob?.status === "completed") {
      setJobId(latestJob.id);
      setPhase("done");
      return;
    }

    const run = async () => {
      const unresolved = slots.some((s) => !s.matched_asset_id && !s.gap_fill_s3_key);
      if (unresolved) {
        setPhase("gap-filling");
        await triggerGapFill.mutateAsync();
        // Poll until every previously-unresolved slot has a gap-fill clip.
        let stillUnresolved = true;
        while (stillUnresolved) {
          await new Promise((r) => setTimeout(r, 2000));
          const { data: fresh } = await refetchSlots();
          stillUnresolved = (fresh ?? []).some((s) => !s.matched_asset_id && !s.gap_fill_s3_key);
        }
      }

      await startNewRender();
    };

    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, slots, renderJobs, triggerGapFill, refetchSlots]);

  useEffect(() => {
    if (job?.status === "completed") setPhase("done");
    if (job?.status === "failed") {
      setStartError(null);
      setPhase("failed");
    }
  }, [job?.status]);

  const percent = phase === "done" ? 100 : phase === "gap-filling" ? 8 : phase === "starting-render" ? 12 : job?.progress_percent ?? 0;
  const isRendering = phase !== "done" && phase !== "failed";

  const copyLink = async () => {
    if (!downloadUrl.data) return;
    await navigator.clipboard.writeText(downloadUrl.data.url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Modal open={open} onClose={onClose} title="Exporting Video" closeDisabled={false}>
      <div className="flex flex-col gap-6">
        <div className="aspect-video overflow-hidden rounded-2xl border border-border bg-black">
          {phase === "done" && downloadUrl.data ? (
            <video src={downloadUrl.data.url} controls className="h-full w-full" />
          ) : (
            <div className="flex h-full w-full flex-col items-center justify-center gap-3 text-text-secondary">
              {phase === "failed" ? (
                <p className="text-sm text-error">
                  Render failed{job?.error_message || startError ? `: ${job?.error_message ?? startError}` : "."}
                </p>
              ) : (
                <>
                  <Loader2 className="animate-spin" size={24} />
                  <p className="text-sm">Rendering...</p>
                </>
              )}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-text-primary">{phase === "done" ? "Complete" : phase === "failed" ? "Failed" : "Rendering..."}</span>
            <span className="text-text-secondary">{Math.round(percent)}%</span>
          </div>
          <ProgressBar percent={percent} showLabel={false} tone={phase === "done" ? "success" : "accent"} className="mt-2" />
        </div>

        <div className="flex flex-col gap-2">
          {STEPS.map((step) => {
            const stepDone = percent >= step.to || phase === "done";
            const stepActive = isRendering && percent >= step.from && percent < step.to;
            return (
              <div key={step.label} className="flex items-center gap-3 rounded-xl border border-border bg-surface px-3 py-2.5">
                {stepDone ? (
                  <Check size={16} className="shrink-0 text-success" />
                ) : stepActive ? (
                  <Loader2 size={16} className="shrink-0 animate-spin text-accent" />
                ) : (
                  <div className="h-4 w-4 shrink-0 rounded-full border border-border" />
                )}
                <span className={`flex-1 text-sm ${stepDone ? "text-text-primary" : "text-text-secondary"}`}>{step.label}</span>
                {(stepDone || stepActive) && <span className="text-xs text-text-secondary">{elapsed}s</span>}
              </div>
            );
          })}
        </div>

        <Card>
          <h3 className="text-sm font-semibold text-text-primary">Export Settings</h3>
          <p className="mt-1 text-xs text-text-secondary">Matches your reference video's format automatically.</p>
          <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
            <div>
              <p className="text-xs text-text-secondary">Resolution</p>
              <p className="font-medium text-text-primary">
                {blueprint?.resolution_width ?? "--"}×{blueprint?.resolution_height ?? "--"}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-secondary">Frame Rate</p>
              <p className="font-medium text-text-primary">{blueprint?.fps ? `${Math.round(blueprint.fps)} fps` : "--"}</p>
            </div>
            <div>
              <p className="text-xs text-text-secondary">Format</p>
              <p className="font-medium text-text-primary">MP4</p>
            </div>
          </div>
        </Card>

        {phase === "failed" ? (
          <Button fullWidth leadingIcon={<RefreshCw size={15} />} onClick={startNewRender}>
            Try Again
          </Button>
        ) : (
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button
              fullWidth
              leadingIcon={<Download size={15} />}
              disabled={phase !== "done" || !downloadUrl.data}
              onClick={() => downloadUrl.data && window.open(downloadUrl.data.url, "_blank")}
            >
              Download Video
            </Button>
            <Button variant="secondary" disabled={phase !== "done" || !downloadUrl.data} onClick={copyLink} leadingIcon={copied ? <Check size={15} /> : <Copy size={15} />}>
              {copied ? "Copied" : "Share"}
            </Button>
          </div>
        )}
        {phase === "done" && (
          <button
            onClick={startNewRender}
            className="flex items-center justify-center gap-1.5 text-center text-sm text-text-secondary hover:text-text-primary"
          >
            <RefreshCw size={13} />
            Re-render this project
          </button>
        )}

        <button onClick={onClose} className="text-center text-sm text-text-secondary hover:text-text-primary">
          ← Back to Editor
        </button>
      </div>
    </Modal>
  );
}
