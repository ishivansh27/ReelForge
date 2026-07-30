import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { Home, Store, FolderKanban, BarChart3, User, Menu, X, LogOut } from "lucide-react";
import clsx from "clsx";
import { Logo } from "./Logo";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS = [
  { label: "Home", to: "/import", icon: Home },
  { label: "Marketplace", to: "/marketplace", icon: Store },
  { label: "Projects", to: "/projects", icon: FolderKanban },
  { label: "Analytics", to: "/analytics", icon: BarChart3 },
  { label: "Profile", to: "/profile", icon: User },
];

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-1 flex-col gap-1 px-3">
      {NAV_ITEMS.map(({ label, to, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          onClick={onNavigate}
          className={({ isActive }) =>
            clsx(
              "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
              isActive ? "bg-accent/10 text-accent" : "text-text-secondary hover:bg-surface hover:text-text-primary"
            )
          }
        >
          <Icon size={18} strokeWidth={2} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

function AccountMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const initials = (user?.full_name || user?.email || "?").slice(0, 1).toUpperCase();

  return (
    <div className="flex items-center gap-3 border-t border-border px-3 pt-4">
      <button
        onClick={() => navigate("/profile")}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-elevated text-sm font-semibold text-text-primary"
      >
        {initials}
      </button>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-text-primary">{user?.full_name || "Your account"}</p>
        <p className="truncate text-xs text-text-secondary">{user?.email}</p>
      </div>
      <button
        onClick={async () => {
          await logout();
          navigate("/");
        }}
        aria-label="Log out"
        className="shrink-0 rounded-lg p-2 text-text-secondary hover:bg-surface hover:text-text-primary"
      >
        <LogOut size={16} />
      </button>
    </div>
  );
}

export function Sidebar() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <>
      {/* Desktop / tablet sidebar */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-background py-5 md:flex">
        <div className="px-4">
          <Logo />
        </div>
        <div className="mt-8 flex flex-1 flex-col">
          <NavItems />
          <AccountMenu />
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border bg-background px-4 md:hidden">
        <Logo />
        <button onClick={() => setDrawerOpen(true)} aria-label="Open menu" className="rounded-lg p-2 text-text-primary">
          <Menu size={22} />
        </button>
      </header>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="absolute inset-0 bg-black/70" onClick={() => setDrawerOpen(false)} />
          <div className="relative flex h-full w-72 flex-col border-r border-border bg-background py-5">
            <div className="flex items-center justify-between px-4">
              <Logo />
              <button onClick={() => setDrawerOpen(false)} aria-label="Close menu" className="rounded-lg p-2 text-text-primary">
                <X size={20} />
              </button>
            </div>
            <div className="mt-8 flex flex-1 flex-col">
              <NavItems onNavigate={() => setDrawerOpen(false)} />
              <AccountMenu />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
