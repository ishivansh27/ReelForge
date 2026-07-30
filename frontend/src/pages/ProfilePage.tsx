import { useState } from "react";
import {
  Settings,
  Wallet,
  History,
  ShieldCheck,
  Bell,
  LifeBuoy,
  ChevronRight,
  Check,
  Copy,
} from "lucide-react";
import { InstagramIcon, YoutubeIcon, TikTokIcon } from "@/components/icons/BrandIcons";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusPill } from "@/components/ui/StatusPill";
import { useAuth } from "@/context/AuthContext";
import { useProjects } from "@/hooks/useApi";

const SOCIALS = [
  { platform: "Instagram", icon: InstagramIcon, color: "var(--color-brand-instagram)", connected: true, handle: "@your.handle" },
  { platform: "YouTube", icon: YoutubeIcon, color: "var(--color-brand-youtube)", connected: false, handle: null },
  { platform: "TikTok", icon: TikTokIcon, color: "var(--color-brand-tiktok)", connected: false, handle: null },
];

const SETTINGS_ROWS = [
  { icon: Wallet, title: "Payout Settings", subtitle: "Manage how you receive marketplace creator earnings." },
  { icon: History, title: "Export History", subtitle: "See every video you've rendered and re-download past exports." },
  { icon: ShieldCheck, title: "Security & Privacy", subtitle: "Update your password and manage active sessions." },
  { icon: Bell, title: "Notification Preferences", subtitle: "Choose which emails and in-app alerts you receive." },
  { icon: LifeBuoy, title: "Support Center", subtitle: "Browse help articles or reach out to our team." },
];

export function ProfilePage() {
  const { user } = useAuth();
  const { data: projects } = useProjects();
  const [copied, setCopied] = useState(false);

  const initials = (user?.full_name || user?.email || "?").slice(0, 1).toUpperCase();

  const copyShareLink = async () => {
    await navigator.clipboard.writeText(window.location.origin + "/profile");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mx-auto flex max-w-[720px] flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-primary">Profile</h1>
        <button className="rounded-lg p-2 text-text-secondary hover:bg-surface hover:text-text-primary" aria-label="Settings">
          <Settings size={18} />
        </button>
      </div>

      <div className="flex flex-col items-center gap-4 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-accent text-2xl font-bold text-white">
          {initials}
        </div>
        <div>
          <h2 className="text-lg font-semibold text-text-primary">{user?.full_name || "Unnamed creator"}</h2>
          <p className="mt-1 text-sm capitalize text-text-secondary">
            {user?.subscription_tier ?? "free"} tier • {projects?.length ?? 0} Blueprints
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="group relative">
            <Button variant="primary" disabled>
              Edit Profile
            </Button>
            <div className="pointer-events-none absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-surface-elevated px-2.5 py-1.5 text-xs text-text-secondary opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
              Profile editing coming soon
            </div>
          </div>
          <Button variant="secondary" onClick={copyShareLink} leadingIcon={copied ? <Check size={15} /> : <Copy size={15} />}>
            {copied ? "Copied" : "Share"}
          </Button>
        </div>
      </div>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-text-primary">Subscription</h3>
            <p className="mt-1 text-xs text-text-secondary">Demo plan -- billing isn't wired up yet.</p>
          </div>
          <StatusPill label={user?.subscription_tier ?? "free"} tone="accent" />
        </div>
        <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
          <div className="text-sm text-text-secondary">Next billing date</div>
          <div className="text-sm font-medium text-text-primary">--</div>
        </div>
        <Button variant="secondary" size="sm" className="mt-4" disabled>
          Manage Plan
        </Button>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-text-primary">Social Integrations</h3>
        <div className="mt-4 flex flex-col divide-y divide-border">
          {SOCIALS.map((s) => (
            <div key={s.platform} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-surface-elevated" style={{ color: s.color }}>
                  <s.icon width={16} height={16} />
                </span>
                <div>
                  <p className="text-sm font-medium text-text-primary">{s.platform}</p>
                  <p className="text-xs text-text-secondary">{s.connected ? s.handle : "Not connected"}</p>
                </div>
              </div>
              <Button variant={s.connected ? "secondary" : "primary"} size="sm" disabled>
                {s.connected ? "Disconnect" : "Connect"}
              </Button>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-0">
        {SETTINGS_ROWS.map((row, i) => (
          <button
            key={row.title}
            className={`flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-surface-elevated ${i !== 0 ? "border-t border-border" : ""}`}
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-elevated text-text-secondary">
              <row.icon size={16} />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-text-primary">{row.title}</p>
              <p className="truncate text-xs text-text-secondary">{row.subtitle}</p>
            </div>
            <ChevronRight size={16} className="shrink-0 text-text-secondary" />
          </button>
        ))}
      </Card>
    </div>
  );
}
