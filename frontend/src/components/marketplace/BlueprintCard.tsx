import { InstagramIcon, YoutubeIcon } from "@/components/icons/BrandIcons";
import { Badge, MediaThumbnail } from "@/components/ui/MediaThumbnail";
import { Button } from "@/components/ui/Button";
import { creatorAvatar } from "@/lib/mockImages";
import type { MockBlueprint } from "@/mocks/marketplace";

function formatDuration(seconds: number) {
  return `0:${seconds.toString().padStart(2, "0")}`;
}

export function BlueprintCard({ blueprint, onUseStyle }: { blueprint: MockBlueprint; onUseStyle?: () => void }) {
  return (
    <div className="flex flex-col gap-3">
      <MediaThumbnail
        src={blueprint.thumbnail}
        alt={blueprint.title}
        topLeft={
          <Badge tone="dark">
            {blueprint.platform === "Reel" ? <InstagramIcon width={11} height={11} /> : <YoutubeIcon width={11} height={11} />}
            {blueprint.platform}
          </Badge>
        }
        topRight={<Badge tone="dark">{formatDuration(blueprint.durationSeconds)}</Badge>}
      />
      <div>
        <h3 className="text-sm font-semibold text-text-primary">{blueprint.title}</h3>
        <p className="mt-0.5 text-xs text-text-secondary">by {blueprint.creator}</p>
        <div className="mt-1 flex items-center gap-2 text-xs text-text-secondary">
          <img src={creatorAvatar(blueprint.creatorSeed)} alt="" className="h-4 w-4 rounded-full" />
          {blueprint.usesCount.toLocaleString()} uses
        </div>
      </div>
      <Button variant="secondary" size="sm" fullWidth onClick={onUseStyle}>
        Use Style
      </Button>
    </div>
  );
}
