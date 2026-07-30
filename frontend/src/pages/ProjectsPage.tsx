import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Search, SlidersHorizontal, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { useProjects } from "@/hooks/useApi";
import clsx from "clsx";

const TABS = ["All Videos", "Blueprints", "Shared"] as const;

export function ProjectsPage() {
  const navigate = useNavigate();
  const { data: projects, isLoading } = useProjects();
  const [tab, setTab] = useState<(typeof TABS)[number]>("All Videos");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (tab !== "All Videos") return [];
    const q = search.trim().toLowerCase();
    if (!q) return projects ?? [];
    return (projects ?? []).filter((p) => p.title.toLowerCase().includes(q));
  }, [projects, tab, search]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-text-primary">My Projects</h1>
        <Button leadingIcon={<Plus size={16} />} onClick={() => navigate("/import")} className="hidden sm:inline-flex">
          New Project
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1 rounded-xl border border-border bg-surface p-1">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={clsx(
                "rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors",
                tab === t ? "bg-surface-elevated text-text-primary" : "text-text-secondary hover:text-text-primary"
              )}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search projects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leadingIcon={<Search size={15} />}
            className="w-full sm:w-64"
          />
          <button className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-border bg-surface text-text-secondary hover:text-text-primary">
            <SlidersHorizontal size={16} />
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center text-text-secondary">
          <Loader2 className="animate-spin" size={20} />
        </div>
      ) : tab !== "All Videos" ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-20 text-center">
          <Sparkles size={24} className="text-text-secondary" />
          <p className="text-sm text-text-secondary">{tab} view is coming soon.</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border py-20 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent/10 text-accent">
            <Sparkles size={24} />
          </div>
          <div>
            <p className="text-base font-semibold text-text-primary">
              {search ? "No projects match your search" : "No projects yet"}
            </p>
            <p className="mt-1 text-sm text-text-secondary">Paste a reference video to create your first clone.</p>
          </div>
          <Button leadingIcon={<Plus size={16} />} onClick={() => navigate("/import")}>
            Create your first clone
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}

      <Button
        leadingIcon={<Plus size={20} />}
        onClick={() => navigate("/import")}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full p-0 shadow-2xl sm:hidden"
        aria-label="New project"
      />
    </div>
  );
}
