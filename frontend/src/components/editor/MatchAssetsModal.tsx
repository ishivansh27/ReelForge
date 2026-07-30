import { useRef, useState } from "react";
import { Sparkles, Upload, AlertTriangle } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { AssetSlotCard } from "./AssetSlotCard";
import { ManualMatchPicker } from "./ManualMatchPicker";
import {
  useAssetSlots,
  useOverrideAssetSlot,
  useProject,
  useProjectAssets,
  useTriggerMatchAssets,
  useUploadAsset,
} from "@/hooks/useApi";
import type { AssetSlotOut } from "@/types/api";

export function MatchAssetsModal({
  projectId,
  open,
  onClose,
  onProceedToRender,
}: {
  projectId: string;
  open: boolean;
  onClose: () => void;
  onProceedToRender?: () => void;
}) {
  const { data: project } = useProject(projectId);
  const { data: slots } = useAssetSlots(projectId, { enabled: open });
  const { data: assets } = useProjectAssets(projectId);
  const uploadAsset = useUploadAsset(projectId);
  const triggerMatch = useTriggerMatchAssets(projectId);
  const overrideSlot = useOverrideAssetSlot(projectId);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeSlot, setActiveSlot] = useState<AssetSlotOut | null>(null);
  const [uploadingCount, setUploadingCount] = useState(0);

  const assetsById = new Map((assets ?? []).map((a) => [a.id, a]));
  const totalSlots = slots?.length ?? 0;
  const matchedCount = slots?.filter((s) => s.matched_asset_id).length ?? 0;
  const percent = totalSlots > 0 ? (matchedCount / totalSlots) * 100 : 0;
  const readyAssetCount = (assets ?? []).filter((a) => a.upload_status === "ready").length;

  const onFilesSelected = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploadingCount(files.length);
    try {
      await Promise.all(Array.from(files).map((file) => uploadAsset.mutateAsync(file)));
    } finally {
      setUploadingCount(0);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <>
      <Modal
        open={open}
        onClose={onClose}
        title="Match Assets"
        subtitle={project ? `Blueprint: ${project.title}` : undefined}
      >
        <div className="flex flex-col gap-5">
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-secondary">
              {matchedCount} of {totalSlots} assets matched
            </span>
            <span className="font-medium text-text-primary">{Math.round(percent)}%</span>
          </div>
          <ProgressBar percent={percent} showLabel={false} tone={percent === 100 ? "success" : "accent"} />

          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text-primary">Required Assets</h3>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              multiple
              hidden
              onChange={(e) => onFilesSelected(e.target.files)}
            />
            <Button
              variant="secondary"
              size="sm"
              leadingIcon={<Upload size={14} />}
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingCount > 0}
            >
              {uploadingCount > 0 ? `Uploading ${uploadingCount}...` : "Upload Media"}
            </Button>
          </div>

          {!slots || slots.length === 0 ? (
            <p className="py-8 text-center text-sm text-text-secondary">Loading scene requirements...</p>
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {slots.map((slot) => (
                <AssetSlotCard
                  key={slot.id}
                  projectId={projectId}
                  slot={slot}
                  matchedAsset={slot.matched_asset_id ? assetsById.get(slot.matched_asset_id) : undefined}
                  sceneLabel={`Scene ${slot.slot_index + 1}`}
                  onClick={() => setActiveSlot(slot)}
                />
              ))}
            </div>
          )}

          {matchedCount < totalSlots && (
            <div className="flex items-start gap-2 rounded-xl border border-accent/30 bg-accent/10 px-3 py-2.5 text-xs text-accent">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              Unmatched scenes will get an AI-generated animated text placeholder instead of your own footage.
            </div>
          )}

          <div className="flex flex-col gap-3 border-t border-border pt-5 sm:flex-row">
            <Button
              variant="secondary"
              fullWidth
              leadingIcon={<Sparkles size={15} />}
              disabled={readyAssetCount === 0 || triggerMatch.isPending}
              onClick={() => triggerMatch.mutate()}
            >
              {triggerMatch.isPending ? "Matching..." : "Auto-Match AI"}
            </Button>
            <Button
              variant="primary"
              fullWidth
              disabled={totalSlots === 0}
              onClick={() => {
                onClose();
                onProceedToRender?.();
              }}
            >
              Render Output
            </Button>
          </div>
        </div>
      </Modal>

      <ManualMatchPicker
        open={!!activeSlot}
        onClose={() => setActiveSlot(null)}
        slot={activeSlot}
        assets={assets ?? []}
        projectId={projectId}
        onAssign={(assetId) => {
          if (activeSlot) overrideSlot.mutate({ slotId: activeSlot.id, assetId });
          setActiveSlot(null);
        }}
        onClear={() => {
          if (activeSlot) overrideSlot.mutate({ slotId: activeSlot.id, assetId: null });
          setActiveSlot(null);
        }}
      />
    </>
  );
}
