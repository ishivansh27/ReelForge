/** Static mock data for the Analytics page -- no analytics backend exists yet. */

export const mockStats = [
  { label: "Total Views", value: "482.6K", deltaPct: 18.2, positive: true },
  { label: "Avg. Watch Time", value: "11.4s", deltaPct: 4.7, positive: true },
  { label: "Export Count", value: "126", deltaPct: -3.1, positive: false },
  { label: "Save Rate", value: "22.8%", deltaPct: 6.4, positive: true },
];

// Retention curve: % of viewers still watching at each second. Biggest
// drop-off is called out explicitly rather than left for the viewer to spot.
export const mockRetentionCurve = [
  { second: 0, retentionPct: 100 },
  { second: 2, retentionPct: 92 },
  { second: 4, retentionPct: 86 },
  { second: 6, retentionPct: 81 },
  { second: 8, retentionPct: 68 },
  { second: 10, retentionPct: 61 },
  { second: 12, retentionPct: 57 },
  { second: 14, retentionPct: 53 },
  { second: 16, retentionPct: 49 },
  { second: 18, retentionPct: 46 },
  { second: 20, retentionPct: 43 },
];

export const mockBiggestDropOff = { second: 8, dropPct: 13 };

export const mockPlatformReach = [
  { platform: "Instagram", pct: 54, color: "var(--color-brand-instagram)" },
  { platform: "YouTube", pct: 31, color: "var(--color-brand-youtube)" },
  { platform: "TikTok", pct: 15, color: "#7dd3fc" },
];
