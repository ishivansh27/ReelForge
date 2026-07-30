import { Share2, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { MediaThumbnail, Badge } from "@/components/ui/MediaThumbnail";
import { RetentionChart } from "@/components/analytics/RetentionChart";
import { PlatformReachChart } from "@/components/analytics/PlatformReachChart";
import { mockStats } from "@/mocks/analytics";
import { mockBlueprints } from "@/mocks/marketplace";

const topBlueprints = mockBlueprints.slice(0, 4);

export function AnalyticsPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Creator Analytics</h1>
          <p className="mt-1 text-sm text-text-secondary">How your rendered videos are performing across platforms</p>
        </div>
        <button className="rounded-lg border border-border p-2 text-text-secondary hover:text-text-primary" aria-label="Share">
          <Share2 size={16} />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {mockStats.map((stat) => (
          <Card key={stat.label}>
            <p className="text-xs text-text-secondary">{stat.label}</p>
            <p className="mt-2 text-2xl font-bold text-text-primary">{stat.value}</p>
            <div className={`mt-2 flex items-center gap-1 text-xs font-medium ${stat.positive ? "text-success" : "text-error"}`}>
              {stat.positive ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
              {Math.abs(stat.deltaPct)}%
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Card>
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-text-primary">Audience Retention</h2>
            <select className="rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs text-text-secondary">
              <option>Last 30 Days</option>
              <option>Last 7 Days</option>
              <option>Last 90 Days</option>
            </select>
          </div>
          <div className="mt-4">
            <RetentionChart />
          </div>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold text-text-primary">Platform Reach</h2>
          <div className="mt-6">
            <PlatformReachChart />
          </div>
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">Top Performing Blueprints</h2>
          <a href="/marketplace" className="text-sm font-medium text-accent hover:underline">
            Marketplace
          </a>
        </div>
        <div className="mt-4 flex flex-col divide-y divide-border rounded-2xl border border-border bg-surface">
          {topBlueprints.map((bp) => (
            <div key={bp.id} className="flex items-center gap-4 p-4">
              <MediaThumbnail src={bp.thumbnail} alt={bp.title} className="w-20 shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-text-primary">{bp.title}</p>
                <p className="text-xs text-text-secondary">Exported 2d ago</p>
              </div>
              <div className="hidden shrink-0 gap-6 text-right sm:flex">
                <div>
                  <p className="text-xs text-text-secondary">Views</p>
                  <p className="text-sm font-medium text-text-primary">{(bp.usesCount * 3).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-text-secondary">Engagement</p>
                  <p className="text-sm font-medium text-text-primary">{bp.engagementRate}%</p>
                </div>
              </div>
              <Badge tone="success">{bp.platform}</Badge>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
