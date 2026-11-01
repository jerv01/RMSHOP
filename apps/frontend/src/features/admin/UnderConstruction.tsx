export function UnderConstruction({ title }: { title: string }) {
  return (
    <>
      <h1 className="text-2xl font-bold">{title}</h1>
      <p className="mt-2">En construcción</p>
    </>
  );
}
