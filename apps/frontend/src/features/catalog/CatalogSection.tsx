import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import { formatCOP } from "@/shared/lib/formatCOP";
import { wolfLogoUrl } from "@/shared/ui/BrandLogo";
import {
  filterPublishedCatalogProducts,
  hasValidDiscount,
  isProductInStock,
  resolveCatalogImageUrl,
  useCatalogProducts,
} from "./api";
import { CATALOG_CATEGORIES, type CatalogProduct, type CategoryFilterOption } from "./types";

function matchesCategory(product: CatalogProduct, option: CategoryFilterOption): boolean {
  if (!option.slug) return true;
  const prodSlug = product.category?.slug?.toLowerCase().trim();
  const prodName = product.category?.name?.toLowerCase().trim();
  return prodSlug === option.slug.toLowerCase() || prodName === option.label.toLowerCase();
}

export function CatalogSection() {
  const { slug: routeCategorySlug } = useParams<{ slug?: string }>();
  const [selectedSlug, setSelectedSlug] = useState<string | null | undefined>(undefined);
  const { data, isPending, isError } = useCatalogProducts();

  const effectiveSlug = selectedSlug !== undefined ? selectedSlug : (routeCategorySlug ?? null);

  const publishedProducts = useMemo(() => filterPublishedCatalogProducts(data ?? []), [data]);

  const activeCategory = useMemo(
    () =>
      CATALOG_CATEGORIES.find((cat) => cat.slug === effectiveSlug) ??
      (effectiveSlug
        ? { label: effectiveSlug, slug: effectiveSlug }
        : { label: "Todos", slug: null }),
    [effectiveSlug],
  );

  const visibleProducts = useMemo(
    () => publishedProducts.filter((product) => matchesCategory(product, activeCategory)),
    [publishedProducts, activeCategory],
  );

  return (
    <div className="space-y-8">
      {/* Hero Monocromático */}
      <section className="rounded-[2px] border border-border bg-surface p-6 sm:p-10">
        <span className="inline-block rounded-[2px] border border-border-strong bg-background px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-foreground">
          Colección Valle del Cauca
        </span>
        <h1 className="mt-3 text-3xl font-bold tracking-tight uppercase text-foreground sm:text-4xl">
          RM Shop · Catálogo Oficial
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted sm:text-base">
          Prendas urbanas de diseño exclusivo y alto contraste. Explora nuestras colecciones con
          envíos a Cali, Palmira, Jamundí y Yumbo.
        </p>
      </section>

      {/* Filtros por categoría (HU-2) */}
      <section aria-label="Filtrar por categoría" className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted">Categorías</h2>
          {!isPending && !isError && (
            <span className="text-xs font-medium text-muted">
              {visibleProducts.length === 1 ? "1 prenda" : `${visibleProducts.length} prendas`}
            </span>
          )}
        </div>

        <div
          role="group"
          aria-label="Categorías de prendas"
          className="flex flex-wrap items-center gap-2"
        >
          {CATALOG_CATEGORIES.map((category) => {
            const isActive = category.slug === activeCategory.slug;
            return (
              <button
                key={category.label}
                type="button"
                aria-pressed={isActive}
                onClick={() => setSelectedSlug(category.slug)}
                className={`inline-flex min-h-11 min-w-11 items-center justify-center rounded-[2px] border px-4 py-2 text-sm font-semibold transition-colors ${
                  isActive
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-background text-foreground hover:border-border-strong hover:bg-surface-alt"
                }`}
              >
                {category.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* Estados de carga, error, vacío o cuadrícula (HU-1, HU-2) */}
      {isPending && (
        <div
          role="status"
          className="rounded-[2px] border border-border bg-surface-alt p-8 text-center text-sm text-muted"
        >
          Cargando catálogo de prendas…
        </div>
      )}

      {isError && (
        <div
          role="alert"
          className="rounded-[2px] border border-accent-sale bg-background p-6 text-sm font-medium text-accent-sale"
        >
          No pudimos cargar el catálogo en este momento. Intenta recargar la página.
        </div>
      )}

      {!isPending && !isError && activeCategory.slug === null && publishedProducts.length === 0 && (
        <div
          role="status"
          className="rounded-[2px] border border-border bg-surface-alt p-10 text-center"
        >
          <p className="text-base font-semibold text-foreground">
            No hay productos disponibles por el momento
          </p>
          <p className="mt-1 text-sm text-muted">
            Pronto publicaremos nuevos diseños en nuestro catálogo.
          </p>
        </div>
      )}

      {!isPending && !isError && activeCategory.slug !== null && visibleProducts.length === 0 && (
        <div
          role="status"
          className="rounded-[2px] border border-border bg-surface-alt p-10 text-center"
        >
          <p className="text-base font-semibold text-foreground">
            No hay productos en esta categoría
          </p>
          <p className="mt-1 text-sm text-muted">
            Prueba seleccionando otra categoría o vuelve a ver todo el catálogo.
          </p>
          <button
            type="button"
            onClick={() => setSelectedSlug(null)}
            className="mt-4 inline-flex min-h-11 items-center justify-center rounded-[2px] border border-border-strong bg-background px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-surface"
          >
            Ver todos los productos
          </button>
        </div>
      )}

      {!isPending && !isError && visibleProducts.length > 0 && (
        <section aria-label="Listado de productos">
          <ul className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {visibleProducts.map((product) => {
              const sortedImages = [...(product.images ?? [])].sort(
                (a, b) => a.position - b.position,
              );
              const primaryImage = sortedImages[0];
              const imgSrc = resolveCatalogImageUrl(primaryImage?.image_url) ?? wolfLogoUrl;
              const imgAlt = primaryImage?.alt_text?.trim() || product.name;
              const inStock = isProductInStock(product);
              const discounted = hasValidDiscount(product.price, product.previous_price);

              return (
                <li key={product.id ?? product.slug} className="flex">
                  <article className="group flex w-full flex-col rounded-[2px] border border-border bg-background transition-colors hover:border-border-strong">
                    <Link
                      to={`/producto/${product.slug}`}
                      aria-label={`Ver detalle de ${product.name}`}
                      className="flex flex-1 flex-col"
                    >
                      <div className="relative aspect-4/5 w-full overflow-hidden border-b border-border bg-surface">
                        <img
                          src={imgSrc}
                          alt={imgAlt}
                          width={600}
                          height={750}
                          loading="lazy"
                          className="h-full w-full object-cover object-center transition-transform duration-200 group-hover:scale-[1.02]"
                        />
                        <div className="absolute top-3 left-3 flex flex-wrap gap-1.5">
                          {!inStock && (
                            <span className="rounded-[2px] bg-muted px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-primary-foreground">
                              Agotado
                            </span>
                          )}
                          {inStock && product.is_new && (
                            <span className="rounded-[2px] bg-primary px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-primary-foreground">
                              Nuevo
                            </span>
                          )}
                          {discounted && (
                            <span className="rounded-[2px] bg-accent-sale px-2.5 py-1 text-xs font-semibold uppercase tracking-wider text-primary-foreground">
                              Oferta
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-1 flex-col justify-between p-4">
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wider text-muted">
                            {product.category?.name}
                          </p>
                          <h3 className="mt-1 text-base font-bold text-foreground">
                            {product.name}
                          </h3>
                        </div>

                        <div className="mt-3 flex flex-wrap items-baseline gap-2">
                          <span className="text-base font-bold text-foreground">
                            {formatCOP(Number(product.price))}
                          </span>
                          {discounted && product.previous_price && (
                            <span className="text-sm text-muted line-through">
                              {formatCOP(Number(product.previous_price))}
                            </span>
                          )}
                        </div>
                      </div>
                    </Link>
                  </article>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
