import { CheckCircle2, PenLine } from "lucide-react";
import { AssetTypeIcon, Badge, DashedPlaceholder, MediaThumbnail } from "@/components/ui/MediaThumbnail";
import { useAssetUrl, useGapFillUrl } from "@/hooks/useApi";
import { formatTimestamp } from "@/lib/projectStatus";
import type { AssetSlotOut, UserAssetOut } from "@/types/api";

function SlotPreview({
  projectId,
  slot,
  matchedAsset,
}: {
  projectId: string;
  slot: AssetSlotOut;
  matchedAsset?: UserAssetOut;
}) {
  const assetUrl = useAssetUrl(projectId, matchedAsset?.id);
  const gapFillUrl = useGapFillUrl(projectId, slot.id, !matchedAsset && !!slot.gap_fill_s3_key);

  if (matchedAsset && assetUrl.data) {
    return matchedAsset.asset_type === "photo" ? (
      <img src={assetUrl.data.url} alt="" className="h-full w-full object-cover" />
    ) : (
      <video src={assetUrl.data.url} muted preload="metadata" className="h-full w-full object-cover" />
    );
  }

  if (!matchedAsset && slot.gap_fill_s3_key && gapFillUrl.data) {
    return <video src={gapFillUrl.data.url} muted preload="metadata" className="h-full w-full object-cover" />;
  }

  return <DashedPlaceholder label={matchedAsset || slot.gap_fill_s3_key ? "Loading..." : "Not yet matched"} />;
}

export function AssetSlotCard({
  projectId,
  slot,
  matchedAsset,
  sceneLabel,
  onClick,
}: {
  projectId: string;
  slot: AssetSlotOut;
  matchedAsset?: UserAssetOut;
  sceneLabel?: string;
  onClick?: () => void;
}) {
  const isFilled = !!slot.matched_asset_id || !!slot.gap_fill_s3_key;
  const expectedType = slot.slot_type === "photo" ? "photo" : "video";

  return (
    <button onClick={onClick} className="group flex flex-col gap-2 text-left" disabled={!onClick}>
      <MediaThumbnail
        aspect="portrait"
        alt={slot.description || `Scene ${slot.slot_index + 1}`}
        src={undefined}
        center={<SlotPreview projectId={projectId} slot={slot} matchedAsset={matchedAsset} />}
        topLeft={
          <Badge tone="dark">
            <AssetTypeIcon type={expectedType} />
            {expectedType === "photo" ? "IMAGE" : "VIDEO"}
          </Badge>
        }
        topRight={<Badge tone="dark">{formatTimestamp(slot.duration_seconds)}</Badge>}
        bottomRight={
          isFilled ? (
            <Badge tone={slot.is_manual ? "accent" : "success"}>
              {slot.is_manual ? <PenLine size={11} /> : <CheckCircle2 size={11} />}
              {slot.is_manual ? "Manual" : "Matched"}
            </Badge>
          ) : undefined
        }
        className={onClick ? "ring-0 transition-shadow group-hover:ring-2 group-hover:ring-accent/50" : undefined}
      />
      <div>
        <p className="text-xs font-medium text-text-primary">{sceneLabel || `Scene ${slot.slot_index + 1}`}</p>
        <p className="truncate text-[11px] text-text-secondary">{slot.description}</p>
      </div>
    </button>
  );
}
