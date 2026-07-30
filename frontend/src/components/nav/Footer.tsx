import { Link } from "react-router-dom";
import { Logo } from "./Logo";
import { InstagramIcon, YoutubeIcon, TwitterIcon } from "@/components/icons/BrandIcons";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { label: "Import Reference", href: "/import" },
      { label: "Marketplace", href: "/marketplace" },
      { label: "Analytics", href: "/analytics" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Pricing", href: "/#pricing" },
      { label: "How it works", href: "/#product" },
    ],
  },
  {
    title: "Account",
    links: [
      { label: "Sign In", href: "/login" },
      { label: "Get Started", href: "/register" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-[1440px] px-4 py-14 sm:px-6 lg:px-10">
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-4">
          <div className="col-span-2 sm:col-span-1">
            <Logo />
            <p className="mt-4 max-w-[220px] text-sm text-text-secondary">
              Clone any reel's editing style with your own footage, in minutes.
            </p>
            <div className="mt-5 flex items-center gap-3 text-text-secondary">
              <InstagramIcon width={18} height={18} className="transition-colors hover:text-text-primary" />
              <YoutubeIcon width={18} height={18} className="transition-colors hover:text-text-primary" />
              <TwitterIcon width={18} height={18} className="transition-colors hover:text-text-primary" />
            </div>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-text-primary">{col.title}</h4>
              <ul className="mt-4 flex flex-col gap-3">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link to={link.href} className="text-sm text-text-secondary hover:text-text-primary">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 border-t border-border pt-6 text-xs text-text-secondary">
          © {new Date().getFullYear()} ReelClone AI. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
