import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Link as LinkIcon, HelpCircle, Sparkles, Scissors, Upload, Film, CheckCircle2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { PlayOverlayButton } from "@/components/ui/MediaThumbnail";
import { useAuth } from "@/context/AuthContext";
import { stockPhotos } from "@/lib/mockImages";

const STEPS = [
  {
    icon: Scissors,
    title: "Analyze Reference",
    description: "Paste a Reel or Short. Our AI extracts every cut, transition, and beat.",
  },
  {
    icon: Upload,
    title: "Match Your Footage",
    description: "Upload your own photos and clips -- AI matches them to the right scenes.",
  },
  {
    icon: Film,
    title: "Render & Export",
    description: "We stitch, color-grade, and beat-sync your footage into the final cut.",
  },
];

export function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [url, setUrl] = useState("");

  const goToImport = (e: FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      navigate("/register");
      return;
    }
    navigate(url ? `/import?url=${encodeURIComponent(url)}` : "/import");
  };

  return (
    <div>
      {/* Hero */}
      <section className="border-b border-border px-4 py-20 sm:px-6 lg:px-10">
        <div className="mx-auto flex max-w-[780px] flex-col items-center text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
            <Sparkles size={12} />
            AI-Powered Video Synthesis
          </span>
          <h1 className="mt-6 text-4xl font-bold tracking-tight text-text-primary sm:text-5xl">
            Clone Any Reel Style in Seconds
          </h1>
          <p className="mt-5 max-w-[620px] text-base text-text-secondary sm:text-lg">
            Paste a URL. Upload your footage. Our AI extracts the timing, transitions, and color grade to
            recreate the magic.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button size="md" onClick={() => navigate(isAuthenticated ? "/import" : "/register")} trailingIcon={<ArrowRight size={16} />}>
              Create Your First Clone
            </Button>
            <Button variant="secondary" size="md" onClick={() => navigate("/marketplace")}>
              Browse Blueprint Marketplace
            </Button>
          </div>

          <form onSubmit={goToImport} className="mt-10 w-full max-w-[560px]">
            <Card className="flex flex-col gap-2 text-left">
              <label className="flex items-center gap-1.5 text-xs font-medium text-text-secondary">
                Paste Reference URL
                <HelpCircle size={12} />
              </label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Input
                  className="flex-1"
                  placeholder="instagram.com/reels/..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  leadingIcon={<LinkIcon size={16} />}
                />
                <Button type="submit" className="sm:w-auto">
                  Analyze
                </Button>
              </div>
            </Card>
          </form>
        </div>
      </section>

      {/* How it works */}
      <section id="product" className="px-4 py-20 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-[1200px]">
          <div className="text-center">
            <span className="text-xs font-semibold uppercase tracking-widest text-accent">The Process</span>
            <h2 className="mt-2 text-2xl font-bold text-text-primary sm:text-3xl">How it works</h2>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <Card key={step.title} className="flex flex-col gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent">
                  <step.icon size={20} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-text-secondary">Step {i + 1}</p>
                  <h3 className="mt-1 text-base font-semibold text-text-primary">{step.title}</h3>
                  <p className="mt-1.5 text-sm text-text-secondary">{step.description}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stat band */}
      <section className="border-y border-border bg-surface px-4 py-16 sm:px-6 lg:px-10">
        <div className="mx-auto flex max-w-[1200px] flex-col items-center text-center">
          <p className="text-5xl font-bold text-accent sm:text-6xl">98%</p>
          <p className="mt-2 text-sm font-medium text-text-secondary">Average Style Match Accuracy</p>
        </div>
      </section>

      {/* Blueprint Editor Preview */}
      <section className="px-4 py-20 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-[900px]">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-text-primary sm:text-3xl">Blueprint Editor Preview</h2>
            <p className="mt-2 text-sm text-text-secondary">See exactly how the AI breaks down a reference video.</p>
          </div>
          <div className="relative mt-10 aspect-video overflow-hidden rounded-2xl border border-border">
            <img src={stockPhotos.cityDusk} alt="Blueprint preview" className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
            <div className="absolute inset-0 flex items-center justify-center">
              <PlayOverlayButton />
            </div>
            <div className="absolute bottom-4 left-4 rounded-lg bg-black/60 px-3 py-1.5 text-sm font-medium text-white backdrop-blur-sm">
              Editing: Cinematic Travel Style
            </div>
            <div className="absolute bottom-4 right-4 rounded-lg bg-black/60 px-3 py-1.5 text-sm font-medium text-white backdrop-blur-sm">
              00:12 / 00:15
            </div>
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section id="pricing" className="border-t border-border px-4 py-24 sm:px-6 lg:px-10">
        <div className="mx-auto flex max-w-[600px] flex-col items-center text-center">
          <h2 className="text-3xl font-bold text-text-primary">Ready to go viral?</h2>
          <div className="mt-8">
            <Button size="md" onClick={() => navigate(isAuthenticated ? "/import" : "/register")} trailingIcon={<ArrowRight size={16} />}>
              Get Started for Free
            </Button>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm text-text-secondary">
            <CheckCircle2 size={16} className="text-success" />
            No credit card required
          </div>
        </div>
      </section>
    </div>
  );
}
