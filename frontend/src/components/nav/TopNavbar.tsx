import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { Logo } from "./Logo";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";

const NAV_LINKS = [
  { label: "Product", href: "/#product" },
  { label: "Marketplace", href: "/marketplace" },
  { label: "Pricing", href: "/#pricing" },
];

export function TopNavbar() {
  const [open, setOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between px-4 sm:px-6 lg:px-10">
        <Logo />

        <nav className="hidden items-center gap-8 lg:flex">
          {NAV_LINKS.map((link) => (
            <Link key={link.label} to={link.href} className="text-sm font-medium text-text-secondary transition-colors hover:text-text-primary">
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          {isAuthenticated ? (
            <Button variant="primary" onClick={() => navigate("/projects")}>
              Go to Dashboard
            </Button>
          ) : (
            <>
              <Button variant="ghost" onClick={() => navigate("/login")}>
                Sign In
              </Button>
              <Button variant="primary" onClick={() => navigate("/register")}>
                Get Started
              </Button>
            </>
          )}
        </div>

        <button
          className="rounded-lg p-2 text-text-primary lg:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="border-t border-border bg-background px-4 pb-6 pt-2 lg:hidden">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.label}
                to={link.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-text-secondary hover:bg-surface hover:text-text-primary"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="mt-4 flex flex-col gap-2">
            {isAuthenticated ? (
              <Button variant="primary" fullWidth onClick={() => navigate("/projects")}>
                Go to Dashboard
              </Button>
            ) : (
              <>
                <Button variant="secondary" fullWidth onClick={() => navigate("/login")}>
                  Sign In
                </Button>
                <Button variant="primary" fullWidth onClick={() => navigate("/register")}>
                  Get Started
                </Button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
