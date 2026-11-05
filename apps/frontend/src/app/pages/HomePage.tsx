import { DevApiStatus } from "@/app/DevApiStatus";
import { CatalogSection } from "@/features/catalog/CatalogSection";

export function HomePage() {
  return (
    <div className="space-y-10">
      <CatalogSection />
      {import.meta.env.DEV && <DevApiStatus />}
    </div>
  );
}
