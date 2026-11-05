import { DevApiStatus } from "@/app/DevApiStatus";

export function HomePage() {
  return (
    <div className="space-y-6">
      <section className="rounded-[2px] border border-border bg-surface p-6 sm:p-8">
        <span className="inline-block rounded-[2px] border border-border-strong bg-background px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-foreground">
          Colección Valle del Cauca
        </span>
        <h1 className="mt-3 text-3xl font-bold tracking-tight uppercase text-foreground">
          RM Shop
        </h1>
        <p className="mt-2 max-w-xl text-sm text-muted">
          Prendas urbanas de diseño exclusivo con envíos a Cali, Palmira, Jamundí y Yumbo.
        </p>
      </section>
      {import.meta.env.DEV && <DevApiStatus />}
    </div>
  );
}
