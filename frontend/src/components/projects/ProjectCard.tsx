import { useNavigate } from "react-router-dom";
import { MoreVertical, Pencil, Copy, Trash2, Share2, Link as LinkIcon } from "lucide-react";
import { InstagramIcon, YoutubeIcon } from "@/components/icons/BrandIcons";
import { useState } from "react";
import { StatusPill } from "@/components/ui/StatusPill";
import { Button } from "@/components/ui/Button";
import { PROJECT_STATUS_META } from "@/lib/projectStatus";
import type { ProjectOut } from "@/types/api";

function timeAgo(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

const PLATFORM_ICON = { instagram: InstagramIcon, youtube: YoutubeIcon, other: LinkIcon };
const PLATFORM_GRADIENT = {
  instagram: "from-[#E1306C]/40 to-[#833AB4]/40",
  youtube: "from-[#FF0000]/40 to-[#7a0000]/40",
  other: "from-accent/30 to-surface",
};

const KEBAB_ITEMS = [
  { label: "Rename", icon: Pencil },
  { label: "Duplicate", icon: Copy },
  { label: "Share", icon: Share2 },
  { label: "Delete", icon: Trash2 },
];

export function ProjectCard({ project }: { project: ProjectOut }) {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const statusMeta = PROJECT_STATUS_META[project.status];
  const PlatformIcon = PLATFORM_ICON[project.source_platform];

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-border bg-surface p-3">
      <div
        className={`relative flex aspect-video items-center justify-center rounded-xl bg-gradient-to-br ${PLATFORM_GRADIENT[project.source_platform]}`}
      >
        <PlatformIcon size={28} className="text-white/70" />
        <span className="absolute left-2 top-2 rounded-lg bg-black/50 px-2 py-1 text-[10px] font-semibold text-white backdrop-blur-sm">
          BLUEPRINT
        </span>
        <div className="absolute right-2 top-2">
          <div className="relative">
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="rounded-lg bg-black/50 p-1.5 text-white backdrop-blur-sm hover:bg-black/70"
              aria-label="More options"
            >
              <MoreVertical size={14} />
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-9 z-20 w-44 rounded-xl border border-border bg-surface-elevated p-1.5 shadow-xl">
                  {KEBAB_ITEMS.map((item) => (
                    <div
                      key={item.label}
                      className="flex cursor-not-allowed items-center justify-between rounded-lg px-2.5 py-2 text-xs text-text-secondary opacity-60"
                    >
                      <span className="flex items-center gap-2">
                        <item.icon size={13} />
                        {item.label}
                      </span>
                      <span className="text-[10px]">Soon</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-text-primary">{project.title}</h3>
          <p className="mt-0.5 text-xs text-text-secondary">Edited {timeAgo(project.created_at)}</p>
        </div>
        <StatusPill label={statusMeta.label} tone={statusMeta.tone} />
      </div>

      <Button variant="secondary" size="sm" fullWidth onClick={() => navigate(`/editor/${project.id}`)}>
        Edit
      </Button>
    </div>
  );
}
