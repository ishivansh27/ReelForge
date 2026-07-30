/**
 * Curated real stock photography (Unsplash CDN, direct photo IDs --
 * verified reachable) used only by the mock-data pages/sections
 * (Marketplace, Analytics avatars, Projects sample thumbnails, Recent
 * Styles). Never used as a stand-in for real user-uploaded assets or
 * actual reference-video frames, which always come from the backend.
 */

function unsplash(id: string, w = 800, q = 80) {
  return `https://images.unsplash.com/photo-${id}?w=${w}&q=${q}&auto=format&fit=crop`;
}

export const stockPhotos = {
  cityDusk: unsplash("1519501025264-65ba15a82390"), // moody dusk cityscape, orange/blue tones
  neonNight: unsplash("1519608487953-e999c86e7455"), // neon-lit night street
  bridgeTwilight: unsplash("1518391846015-55a9cc003b25"), // bridge skyline at twilight
  beachSunset: unsplash("1507525428034-b723cf961d3e"), // golden-hour beach/coastline
  sportsCar: unsplash("1567818735868-e71b99932e29"), // car in motion -- styled retro via CSS filter
  bwPortrait: unsplash("1522075469751-3a6694fb2f61"), // black & white moody portrait
  mountains: unsplash("1454496522488-7a8e488e8606"), // mountain range, travel/adventure
  laSkyline: unsplash("1444723121867-7a241cacace9"), // night city skyline
  workspace: unsplash("1519389950473-47ba0277781c"), // creator workspace flatlay
  clothesRack: unsplash("1490481651871-ab68de25d43d"), // fashion rack
} as const;

export function creatorAvatar(seed: number) {
  return `https://i.pravatar.cc/150?img=${(seed % 70) + 1}`;
}
