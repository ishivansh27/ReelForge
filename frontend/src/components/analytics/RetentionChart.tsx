import { mockBiggestDropOff, mockRetentionCurve } from "@/mocks/analytics";

const WIDTH = 600;
const HEIGHT = 220;
const PAD = 24;

export function RetentionChart() {
  const maxSecond = mockRetentionCurve[mockRetentionCurve.length - 1].second;
  const x = (second: number) => PAD + (second / maxSecond) * (WIDTH - PAD * 2);
  const y = (pct: number) => HEIGHT - PAD - (pct / 100) * (HEIGHT - PAD * 2);

  const linePath = mockRetentionCurve
    .map((p, i) => `${i === 0 ? "M" : "L"} ${x(p.second)} ${y(p.retentionPct)}`)
    .join(" ");
  const areaPath = `${linePath} L ${x(maxSecond)} ${HEIGHT - PAD} L ${x(0)} ${HEIGHT - PAD} Z`;

  const dropPoint = mockRetentionCurve.find((p) => p.second === mockBiggestDropOff.second)!;

  return (
    <div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label="Audience retention over time">
        <defs>
          <linearGradient id="retentionFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 25, 50, 75, 100].map((pct) => (
          <line key={pct} x1={PAD} x2={WIDTH - PAD} y1={y(pct)} y2={y(pct)} stroke="var(--color-border)" strokeWidth="1" />
        ))}
        <path d={areaPath} fill="url(#retentionFill)" />
        <path d={linePath} fill="none" stroke="var(--color-accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={x(dropPoint.second)} cy={y(dropPoint.retentionPct)} r={5} fill="var(--color-accent)" stroke="var(--color-background)" strokeWidth="2" />
      </svg>
      <p className="mt-1 text-xs text-text-secondary">
        Biggest drop-off at <span className="font-medium text-text-primary">{mockBiggestDropOff.second}s</span> --{" "}
        {mockBiggestDropOff.dropPct}% of viewers leave here.
      </p>
    </div>
  );
}
