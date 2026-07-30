/**
 * lucide-react dropped brand/logo glyphs (trademark reasons), so the
 * handful this app needs (Instagram, YouTube, X/Twitter, TikTok) are
 * small hand-drawn outline SVGs instead of pulling in a whole
 * brand-icon package for four marks.
 */
import type { SVGProps } from "react";

export function InstagramIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function YoutubeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="2" y="5" width="20" height="14" rx="4" />
      <path d="M10 9.5v5l4.5-2.5z" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function TwitterIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M18.9 3H21.6L15.6 10.1L22.7 21H17.1L12.7 14.7L7.6 21H4.9L11.3 13.4L4.5 3H10.3L14.3 8.8L18.9 3ZM17.9 19.3H19.5L9.3 4.6H7.6L17.9 19.3Z" />
    </svg>
  );
}

export function TikTokIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M16.6 3h-3.2v12.4a2.6 2.6 0 1 1-2.6-2.6c.24 0 .47.03.7.08V9.6a5.8 5.8 0 1 0 5.1 5.76V9.3a7.6 7.6 0 0 0 4.3 1.33V7.4a4.4 4.4 0 0 1-4.3-4.4z" />
    </svg>
  );
}
