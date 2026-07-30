import { X } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { AssetTypeIcon, Badge, MediaThumbnail } from "@/components/ui/MediaThumbnail";
import { useAssetUrl } from "@/hooks/useApi";
import type { AssetSlotOut, UserAssetOut } from "@/types/api";

function PickerThumb({ projectId, asset }: { projectId: string; asset: UserAssetOut }) {
  const { data } = useAssetUrl(projectId, asset.id);
  if (!data) return <div className="h-full w-full animate-pulse bg-surface" />;
  return asset.asset_type === "photo" ? (
    <img src={data.url} alt="" className="h-full w-full object-cover" />
  ) : (
    <video src={data.url} muted preload="metadata" className="h-full w-full object-cover" />
  );
}

export function ManualMatchPicker({
  open,
  onClose,
  slot,
  assets,
  onAssign,
  onClear,
  projectId,
}: {
  open: boolean;
  onClose: () => void;
  slot: AssetSlotOut | null;
  assets: UserAssetOut[];
  onAssign: (assetId: string) => void;
  onClear: () => void;
  projectId: string;
}) {
  if (!slot) return null;
  const readyAssets = assets.filter((a) => a.upload_status === "ready");

  return (
    <Modal open={open} onClose={onClose} title={`Scene ${slot.slot_index + 1}`} subtitle={slot.description ?? undefined} maxWidth="600px">
      <div className="flex flex-col gap-4">
        {slot.matched_asset_id && (
          <button
            onClick={onClear}
            className="flex items-center gap-2 self-start rounded-full border border-error/30 bg-error/10 px-3 py-1.5 text-xs font-medium text-error hover:bg-error/20"
          >
            <X size={13} />
            Clear current match
          </button>
        )}

        {readyAssets.length === 0 ? (
          <p className="py-8 text-center text-sm text-text-secondary">
            No uploaded assets yet -- upload photos or clips first, then come back to assign one here.
          </p>
        ) : (
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
            {readyAssets.map((asset) => (
              <button
                key={asset.id}
                onClick={() => onAssign(asset.id)}
                className="group flex flex-col gap-1.5 text-left"
              >
                <MediaThumbnail
                  aspect="portrait"
                  alt=""
                  center={<PickerThumb projectId={projectId} asset={asset} />}
                  topLeft={
                    <Badge tone="dark">
                      <AssetTypeIcon type={asset.asset_type} />
                    </Badge>
                  }
                  className="ring-0 transition-shadow group-hover:ring-2 group-hover:ring-accent/60"
                />
                {asset.id === slot.matched_asset_id && (
                  <span className="text-[11px] font-medium text-accent">Currently assigned</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}
