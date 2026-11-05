import { Link, Outlet } from "react-router";
import { SessionControls } from "@/features/auth/SessionControls";
import { BrandLogo } from "@/shared/ui/BrandLogo";

export function StoreLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link
            to="/"
            aria-label="RM Shop"
            className="inline-flex min-h-11 items-center rounded-[2px]"
          >
            <BrandLogo subtitle="Moda urbana · Valle del Cauca" />
          </Link>
          <SessionControls />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
