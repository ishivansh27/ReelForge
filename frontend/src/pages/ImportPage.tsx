import { useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Link as LinkIcon, HelpCircle, Sparkles, AlertCircle } from "lucide-react";
import { InstagramIcon, YoutubeIcon } from "@/components/icons/BrandIcons";
import { Stepper } from "@/components/ui/Stepper";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { MediaThumbnail } from "@/components/ui/MediaThumbnail";
import { useCreateProject } from "@/hooks/useApi";
import { mockBlueprints } from "@/mocks/marketplace";
import { isAxiosError } from "axios";

export function ImportPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [url, setUrl] = useState(searchParams.get("url") ?? "");
  const [error, setError] = useState<string | null>(null);
  const createProject = useCreateProject();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const project = await createProject.mutateAsync(url);
      navigate(`/editor/${project.id}`);
    } catch (err) {
      const detail = isAxiosError(err) ? err.response?.data?.detail : null;
      setError(detail || "Couldn't start analysis for that URL. Double-check the link and try again.");
    }
  };

  return (
    <div className="flex flex-col gap-10">
      <Stepper activeStep={1} />

      <div className="mx-auto flex w-full max-w-[640px] flex-col gap-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">Import Reference</h1>
          <p className="mt-2 text-sm text-text-secondary">
            Paste a link to the video style you want to replicate. We'll analyze the cuts, timing, and effects.
          </p>
        </div>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <Card className="flex flex-col gap-2 text-left">
            <label className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
              Reference URL
              <HelpCircle size={12} />
            </label>
            <Input
              placeholder="https://www.instagram.com/reels/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              leadingIcon={<LinkIcon size={16} />}
              required
            />
          </Card>

          <div className="flex items-center justify-center gap-6 text-xs text-text-secondary">
            <span className="flex items-center gap-1.5">
              <InstagramIcon width={14} height={14} style={{ color: "var(--color-brand-instagram)" }} />
              Instagram Reels
            </span>
            <span className="flex items-center gap-1.5">
              <YoutubeIcon width={14} height={14} style={{ color: "var(--color-brand-youtube)" }} />
              YouTube Shorts
            </span>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-error/30 bg-error/10 px-3 py-2 text-sm text-error">
              <AlertCircle size={16} className="shrink-0" />
              {error}
            </div>
          )}

          <Button type="submit" fullWidth disabled={createProject.isPending} leadingIcon={<Sparkles size={16} />}>
            {createProject.isPending ? "Starting analysis..." : "Analyze Video"}
          </Button>
        </form>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">Recent Styles</h2>
          <button onClick={() => navigate("/marketplace")} className="text-sm font-medium text-accent hover:underline">
            View Gallery
          </button>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {mockBlueprints.slice(0, 5).map((bp) => (
            <button key={bp.id} onClick={() => navigate("/marketplace")} className="text-left">
              <MediaThumbnail src={bp.thumbnail} alt={bp.title} />
              <p className="mt-2 truncate text-xs font-medium text-text-primary">{bp.title}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
