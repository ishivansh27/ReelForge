import { mockPlatformReach } from "@/mocks/analytics";

const SIZE = 160;
const STROKE = 22;
const RADIUS = (SIZE - STROKE) / 2;
const CIRC = 2 * Math.PI * RADIUS;

export function PlatformReachChart() {
  let offset = 0;

  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:justify-center">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label="Platform reach breakdown">
        <g transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}>
          <circle cx={SIZE / 2} cy={SIZE / 2} r={RADIUS} fill="none" stroke="var(--color-surface)" strokeWidth={STROKE} />
          {mockPlatformReach.map((slice) => {
            const dash = (slice.pct / 100) * CIRC;
            const el = (
              <circle
                key={slice.platform}
                cx={SIZE / 2}
                cy={SIZE / 2}
                r={RADIUS}
                fill="none"
                stroke={slice.color}
                strokeWidth={STROKE}
                strokeDasharray={`${dash} ${CIRC - dash}`}
                strokeDashoffset={-offset}
              />
            );
            offset += dash;
            return el;
          })}
        </g>
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="fill-text-primary text-lg font-bold">
          100%
        </text>
      </svg>

      <div className="flex flex-col gap-2.5">
        {mockPlatformReach.map((slice) => (
          <div key={slice.platform} className="flex items-center gap-2.5 text-sm">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: slice.color }} />
            <span className="text-text-primary">{slice.platform}</span>
            <span className="text-text-secondary">{slice.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
