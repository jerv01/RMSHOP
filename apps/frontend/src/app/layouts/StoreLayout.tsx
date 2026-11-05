import { Link, NavLink, Outlet } from "react-router";
import { SessionControls } from "@/features/auth/SessionControls";
import { BrandLogo } from "@/shared/ui/BrandLogo";

export function StoreLayout() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
      {/* Barra de anuncio superior monocromática */}
      <div
        role="region"
        aria-label="Anuncio de envíos"
        className="bg-primary px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-primary-foreground"
      >
        Envíos en el Valle del Cauca: Cali $ 5.000 · Palmira, Jamundí y Yumbo $ 10.000
      </div>

      <header className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-6">
            <Link
              to="/"
              aria-label="RM Shop"
              className="inline-flex min-h-11 items-center rounded-[2px]"
            >
              <BrandLogo subtitle="Moda urbana · Valle del Cauca" />
            </Link>
            <nav aria-label="Navegación principal">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `inline-flex min-h-11 items-center rounded-[2px] border px-3.5 py-2 text-sm font-semibold transition-colors ${
                    isActive
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-transparent text-foreground hover:bg-surface-alt"
                  }`
                }
              >
                Catálogo
              </NavLink>
            </nav>
          </div>
          <SessionControls />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>
    </div>
  );
}
