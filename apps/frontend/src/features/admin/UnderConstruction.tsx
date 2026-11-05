export function UnderConstruction({ title }: { title: string }) {
  return (
    <section className="rounded-[2px] border border-border bg-surface-alt p-6 shadow-(--shadow-soft)">
      <span className="inline-block rounded-[2px] border border-accent-warning bg-background px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-accent-warning">
        Próximamente
      </span>
      <h1 className="mt-3 text-2xl font-bold text-foreground">{title}</h1>
      <p className="mt-2 text-sm text-muted">En construcción</p>
    </section>
  );
}
