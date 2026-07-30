/**
 * Static mock data for the Marketplace page and the Landing/Import
 * "Recent Styles" rails. There is no marketplace backend yet -- see
 * the note on ProfilePage/MarketplacePage for what's real vs. mocked.
 */
import { stockPhotos } from "@/lib/mockImages";

export interface MockBlueprint {
  id: string;
  title: string;
  creator: string;
  creatorSeed: number;
  thumbnail: string;
  durationSeconds: number;
  platform: "Reel" | "Shorts";
  category: string;
  usesCount: number;
  engagementRate: number;
}

export const mockBlueprints: MockBlueprint[] = [
  {
    id: "bp-1",
    title: "Neon Urban Kinetic",
    creator: "mika.codes",
    creatorSeed: 3,
    thumbnail: stockPhotos.neonNight,
    durationSeconds: 14,
    platform: "Reel",
    category: "Fast-Cut",
    usesCount: 2840,
    engagementRate: 12.4,
  },
  {
    id: "bp-2",
    title: "Minimalist Travel Vlog",
    creator: "wanderlens",
    creatorSeed: 8,
    thumbnail: stockPhotos.beachSunset,
    durationSeconds: 22,
    platform: "Shorts",
    category: "Vlog",
    usesCount: 5310,
    engagementRate: 9.1,
  },
  {
    id: "bp-3",
    title: "Hyper-Speed Fashion",
    creator: "studio.rae",
    creatorSeed: 15,
    thumbnail: stockPhotos.clothesRack,
    durationSeconds: 11,
    platform: "Reel",
    category: "Fast-Cut",
    usesCount: 1920,
    engagementRate: 15.7,
  },
  {
    id: "bp-4",
    title: "Retro Grain Cinematic",
    creator: "olddial.films",
    creatorSeed: 22,
    thumbnail: stockPhotos.sportsCar,
    durationSeconds: 18,
    platform: "Reel",
    category: "Cinematic",
    usesCount: 3475,
    engagementRate: 11.2,
  },
  {
    id: "bp-5",
    title: "Golden Hour Portraits",
    creator: "duskframe",
    creatorSeed: 31,
    thumbnail: stockPhotos.bwPortrait,
    durationSeconds: 16,
    platform: "Shorts",
    category: "Cinematic",
    usesCount: 2103,
    engagementRate: 10.5,
  },
  {
    id: "bp-6",
    title: "Skyline Nightdrive",
    creator: "afterhours.ai",
    creatorSeed: 44,
    thumbnail: stockPhotos.bridgeTwilight,
    durationSeconds: 20,
    platform: "Reel",
    category: "Instagram Reels",
    usesCount: 4290,
    engagementRate: 13.8,
  },
  {
    id: "bp-7",
    title: "Peak Adventure Cut",
    creator: "trailrun.studio",
    creatorSeed: 52,
    thumbnail: stockPhotos.mountains,
    durationSeconds: 25,
    platform: "Shorts",
    category: "YouTube Shorts",
    usesCount: 1587,
    engagementRate: 8.9,
  },
  {
    id: "bp-8",
    title: "Downtown Pulse",
    creator: "citylights.co",
    creatorSeed: 61,
    thumbnail: stockPhotos.laSkyline,
    durationSeconds: 13,
    platform: "Reel",
    category: "Trending",
    usesCount: 6120,
    engagementRate: 14.6,
  },
];

export const mockCategories = [
  "Trending",
  "Instagram Reels",
  "YouTube Shorts",
  "Cinematic",
  "Fast-Cut",
  "Vlog",
];

export const mockTopCreators = mockBlueprints.map((bp) => ({ name: bp.creator, seed: bp.creatorSeed }));
