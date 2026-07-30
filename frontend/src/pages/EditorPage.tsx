import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, AlertTriangle, HelpCircle, Play, Upload, FileJson, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusPill } from "@/components/ui/StatusPill";
import { AssetSlotCard } from "@/components/editor/AssetSlotCard";
import { MatchAssetsModal } from "@/components/editor/MatchAssetsModal";
import { ExportModal } from "@/components/editor/ExportModal";
import { useAssetSlots, useBlueprint, useProject, useProjectAssets, useReferenceVideoUrl } from "@/hooks/useApi";
import { PROJECT_STATUS_META, formatCameraMovement, formatTimestamp } from "@/lib/projectStatus";

export function EditorPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [modal, setModal] = useState<"match" | "export" | null>(null);

  const { data: project } = useProject(projectId);
  const { data: blueprint } = useBlueprint(projectId, { enabled: !!project });
  const blueprintReady = blueprint?.status === "completed";
  const { data: slots } = useAssetSlots(projectId, {
    enabled: !!project && ["awaiting_assets", "matching", "rendering", "completed"].includes(project.status),
  });
  const { data: assets } = useProjectAssets(projectId);
  const referenceVideo = useReferenceVideoUrl(projectId, blueprintReady);

  const assetsById = useMemo(() => new Map((assets ?? []).map((a) => [a.id, a])), [assets]);
  const matchedCount = slots?.filter((s) => s.matched_asset_id || s.gap_fill_s3_key).length ?? 0;
  const totalSlots = slots?.length ?? 0;

  const analysisConfidence = useMemo(() => {
    const scenes = blueprint?.edit_blueprint?.scenes ?? [];
    if (scenes.length === 0) return null;
    const avg = scenes.reduce((sum, s) => sum + s.camera_movement.confidence, 0) / scenes.length;
    return Math.round(avg * 100);
  }, [blueprint]);

  if (!project) {
    return (
      <div className="flex h-96 items-center justify-center text-text-secondary">
        <Loader2 className="animate-spin" size={20} />
      </div>
    );
  }

  const statusMeta = PROJECT_STATUS_META[project.status];
  const canRender = project.status === "matching" || project.status === "rendering" || project.status === "completed";

  if (project.status === "failed") {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-start gap-3">
          <button
            onClick={() => navigate("/projects")}
            className="mt-1 rounded-lg p-1.5 text-text-secondary hover:bg-surface hover:text-text-primary"
            aria-label="Back"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-text-primary sm:text-2xl">AI Blueprint Editor</h1>
            <p className="text-sm text-text-secondary">Style: {project.title}</p>
          </div>
        </div>
        <Card className="mx-auto flex max-w-[560px] flex-col items-center gap-3 py-16 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error/10 text-error">
            <AlertTriangle size={22} />
          </div>
          <h2 className="text-base font-semibold text-text-primary">Analysis failed</h2>
          <p className="text-sm text-text-secondary">
            {project.error_message || "Something went wrong while processing this reference video."}
          </p>
          <Button variant="secondary" onClick={() => navigate("/import")} className="mt-2">
            Try another URL
          </Button>
        </Card>
      </div>
    );
  }

  const downloadBlueprintJson = () => {
    if (!blueprint?.edit_blueprint) return;
    const blob = new Blob([JSON.stringify(blueprint.edit_blueprint, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${project.title.replace(/\s+/g, "-").toLowerCase()}-blueprint.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <button
            onClick={() => navigate("/projects")}
            className="mt-1 rounded-lg p-1.5 text-text-secondary hover:bg-surface hover:text-text-primary"
            aria-label="Back"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-text-primary sm:text-2xl">AI Blueprint Editor</h1>
            <p className="text-sm text-text-secondary">Style: {project.title}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusPill label={statusMeta.label} tone={statusMeta.tone} />
          <Button
            leadingIcon={<Play size={15} fill="currentColor" />}
            onClick={() => setModal(canRender ? "export" : "match")}
            disabled={!blueprintReady}
          >
            Render
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_380px]">
        {/* Left: preview + timeline */}
        <div className="flex flex-col gap-6">
          <Card className="p-0 overflow-hidden">
            <div className="aspect-video bg-black">
              {referenceVideo.data ? (
                <video src={referenceVideo.data.url} controls className="h-full w-full" />
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center gap-3 text-text-secondary">
                  <Loader2 className="animate-spin" size={22} />
                  <p className="text-sm">{statusMeta.description}</p>
                </div>
              )}
            </div>
          </Card>

          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-base font-semibold text-text-primary">Blueprint Analysis</h2>
              {analysisConfidence !== null && (
                <StatusPill label={`✦ ${analysisConfidence}% Match Accuracy`} tone="success" />
              )}
            </div>

            <div className="mt-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text-secondary">Timeline Decisions</h3>
              {blueprint?.scene_cuts && (
                <span className="text-xs text-text-secondary">{blueprint.scene_cuts.cut_count} Cuts Detected</span>
              )}
            </div>

            {blueprintReady && blueprint?.edit_blueprint ? (
              <div className="mt-3 flex gap-3 overflow-x-auto pb-2">
                {blueprint.edit_blueprint.scenes.map((scene) => (
                  <div
                    key={scene.scene_index}
                    className="flex w-36 shrink-0 flex-col gap-1 rounded-xl border border-border bg-surface p-3"
                  >
                    <span className="text-[11px] font-medium text-text-secondary">
                      {formatTimestamp(scene.start_time_seconds)} - {formatTimestamp(scene.end_time_seconds)}
                    </span>
                    <span className="text-sm font-semibold text-text-primary">
                      {formatCameraMovement(scene.camera_movement.movement_type)}
                    </span>
                    {scene.beat_alignment.is_on_beat && <StatusPill label="On beat" tone="accent" />}
                  </div>
                ))}
              </div>
            ) : (
              <Card className="mt-3 flex items-center gap-3 text-sm text-text-secondary">
                <Loader2 className="animate-spin" size={16} />
                Detecting scene cuts, camera movement, and beat sync...
              </Card>
            )}
          </div>
        </div>

        {/* Right: required assets */}
        <div className="flex flex-col gap-4 lg:sticky lg:top-8 lg:h-fit">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <h2 className="text-base font-semibold text-text-primary">Required Assets</h2>
              <HelpCircle size={14} className="text-text-secondary" />
            </div>
            {totalSlots > 0 && (
              <button onClick={() => setModal("match")} className="text-sm font-medium text-accent hover:underline">
                Auto-Match All
              </button>
            )}
          </div>

          {slots && slots.length > 0 ? (
            <>
              <p className="text-xs text-text-secondary">
                {matchedCount} of {totalSlots} scenes have footage
              </p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-2">
                {slots.map((slot) => (
                  <AssetSlotCard
                    key={slot.id}
                    projectId={projectId!}
                    slot={slot}
                    matchedAsset={slot.matched_asset_id ? assetsById.get(slot.matched_asset_id) : undefined}
                    onClick={() => setModal("match")}
                  />
                ))}
              </div>
            </>
          ) : (
            <Card className="flex items-center gap-3 text-sm text-text-secondary">
              <Loader2 className="animate-spin" size={16} />
              Waiting for the blueprint to finish before we know what footage you'll need...
            </Card>
          )}

          <div className="flex flex-col gap-2 border-t border-border pt-4 sm:flex-row">
            <Button variant="secondary" fullWidth leadingIcon={<Upload size={15} />} onClick={() => setModal("match")}>
              Upload Media
            </Button>
            <div className="group relative w-full">
              <Button
                variant="secondary"
                fullWidth
                leadingIcon={<FileJson size={15} />}
                disabled={!blueprintReady}
                onClick={downloadBlueprintJson}
              >
                Export JSON
              </Button>
              {!blueprintReady && (
                <div className="pointer-events-none absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-surface-elevated px-2.5 py-1.5 text-xs text-text-secondary opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                  Available once blueprint analysis finishes
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {projectId && (
        <>
          <MatchAssetsModal
            projectId={projectId}
            open={modal === "match"}
            onClose={() => setModal(null)}
            onProceedToRender={() => setModal("export")}
          />
          <ExportModal projectId={projectId} open={modal === "export"} onClose={() => setModal(null)} />
        </>
      )}
    </div>
  );
}
