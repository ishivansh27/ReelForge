import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import clsx from "clsx";
import { Input } from "@/components/ui/Input";
import { BlueprintCard } from "@/components/marketplace/BlueprintCard";
import { creatorAvatar } from "@/lib/mockImages";
import { mockBlueprints, mockCategories, mockTopCreators } from "@/mocks/marketplace";

export function MarketplacePage() {
  const navigate = useNavigate();
  const [category, setCategory] = useState("Trending");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let items = mockBlueprints;
    if (category !== "Trending") {
      items = items.filter((bp) => bp.category === category);
    }
    const q = search.trim().toLowerCase();
    if (q) {
      items = items.filter(
        (bp) => bp.title.toLowerCase().includes(q) || bp.creator.toLowerCase().includes(q)
      );
    }
    return items;
  }, [category, search]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Blueprint Marketplace</h1>
        <p className="mt-1 text-sm text-text-secondary">Trending editing styles & community blueprints</p>
      </div>

      <Input
        placeholder="Search styles, creators, or platforms"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        leadingIcon={<Search size={16} />}
        className="w-full sm:max-w-md"
      />

      <div className="flex flex-wrap gap-2">
        {mockCategories.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={clsx(
              "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors",
              category === c ? "border-accent bg-accent/10 text-accent" : "border-border text-text-secondary hover:text-text-primary"
            )}
          >
            {c}
          </button>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">Featured Blueprints</h2>
          <button onClick={() => setCategory("Trending")} className="text-sm font-medium text-accent hover:underline">
            See All
          </button>
        </div>
        {filtered.length === 0 ? (
          <p className="mt-6 text-sm text-text-secondary">No blueprints match that search.</p>
        ) : (
          <div className="mt-5 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((bp) => (
              <BlueprintCard key={bp.id} blueprint={bp} onUseStyle={() => navigate("/import")} />
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-text-primary">Top Creators</h2>
        <div className="mt-5 flex flex-wrap gap-6">
          {mockTopCreators.map((creator) => (
            <div key={creator.name} className="flex w-16 flex-col items-center gap-2 text-center">
              <img src={creatorAvatar(creator.seed)} alt={creator.name} className="h-14 w-14 rounded-full border border-border" />
              <span className="truncate text-xs text-text-secondary">{creator.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
