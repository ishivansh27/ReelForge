import { Outlet } from "react-router-dom";
import { TopNavbar } from "@/components/nav/TopNavbar";
import { Footer } from "@/components/nav/Footer";

export function MarketingLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <TopNavbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
