import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import { formatCOP } from "@/shared/lib/formatCOP";
import { hasValidDiscount, resolveCatalogImageUrl, useCatalogProductDetail } from "./api";

export function ProductDetailPage() {
  const { slug = "" } = useParams<{ slug: string }>();
  const { data: product, isPending, isError } = useCatalogProductDetail(slug);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);

  const variants = useMemo(() => product?.variants ?? [], [product?.variants]);
  const images = useMemo(
    () =>
      [...(product?.images ?? [])]
        .filter((img) => Boolean(img.image_url))
        .sort((a, b) => a.position - b.position),
    [product?.images],
  );

  const colors = useMemo(() => Array.from(new Set(variants.map((v) => v.color))), [variants]);
  const sizes = useMemo(() => Array.from(new Set(variants.map((v) => v.size))), [variants]);

  // Preseleccionar la primera variante disponible o la primera existente (AC-HU-4-3)
  const defaultVariant = useMemo(
    () => variants.find((v) => v.stock_quantity > 0) ?? variants[0] ?? null,
    [variants],
  );

  const activeColor = selectedColor ?? defaultVariant?.color ?? null;
  const activeSize = selectedSize ?? defaultVariant?.size ?? null;

  const selectedVariant = useMemo(
    () => variants.find((v) => v.color === activeColor && v.size === activeSize) ?? null,
    [variants, activeColor, activeSize],
  );

  if (isPending) {
    return (
      <div
        role="status"
        className="rounded-[2px] border border-border bg-surface-alt p-8 text-center text-sm text-muted"
      >
        Cargando ficha del producto…
      </div>
    );
  }

  const isUnavailable =
    isError ||
    !product ||
    (product.status && product.status !== "published") ||
    (Array.isArray(product.variants) && product.variants.length === 0);

  if (isUnavailable) {
    return (
      <section className="mx-auto max-w-lg rounded-[2px] border border-border bg-surface-alt p-8 text-center shadow-(--shadow-soft)">
        <h1 className="text-2xl font-bold text-foreground">Producto no disponible</h1>
        <p className="mt-2 text-sm text-muted">
          La prenda que buscas ya no se encuentra publicada en nuestro catálogo.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex min-h-11 items-center justify-center rounded-[2px] bg-primary px-5 py-2.5 text-sm font-semibold uppercase tracking-wider text-primary-foreground transition-colors hover:bg-foreground/90"
        >
          Volver al catálogo
        </Link>
      </section>
    );
  }

  const discounted = hasValidDiscount(product.price, product.previous_price);
  const designLabel = product.design?.trim() || `Diseño exclusivo RM · ${product.category.name}`;
  const variantInStock = (selectedVariant?.stock_quantity ?? 0) > 0;

  return (
    <article className="space-y-6">
      <div>
        <Link
          to="/"
          className="inline-flex min-h-11 items-center gap-2 rounded-[2px] border border-border-strong bg-background px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-surface-alt"
        >
          ← Volver al catálogo
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Galería de fotografías sin espacios vacíos (AC-HU-3-3) */}
        <section aria-label="Fotografías del producto" className="lg:col-span-7">
          {images.length === 0 ? (
            <div className="flex aspect-4/5 w-full items-center justify-center rounded-[2px] border border-border bg-surface p-6 text-center text-sm text-muted">
              Sin fotografía disponible
            </div>
          ) : (
            <div
              className={
                images.length === 1
                  ? "grid grid-cols-1 gap-4"
                  : "grid grid-cols-1 gap-4 sm:grid-cols-2"
              }
            >
              {images.map((image, index) => {
                const src = resolveCatalogImageUrl(image.image_url) ?? "";
                const alt = image.alt_text?.trim() || product.name;
                const isHeroImage = images.length === 3 && index === 0;
                return (
                  <figure
                    key={image.id ?? image.position}
                    className={`overflow-hidden rounded-[2px] border border-border bg-surface ${
                      isHeroImage ? "sm:col-span-2" : ""
                    }`}
                  >
                    <img
                      src={src}
                      alt={alt}
                      width={800}
                      height={1000}
                      className="aspect-4/5 h-full w-full object-cover object-center"
                    />
                  </figure>
                );
              })}
            </div>
          )}
        </section>

        {/* Atributos y selector de variantes (AC-HU-3-1, HU-4, HU-5) */}
        <section
          aria-label="Información de la prenda"
          className="flex flex-col justify-between space-y-6 lg:col-span-5"
        >
          <div className="space-y-5">
            <header className="border-b border-border pb-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                {product.category.name}
              </p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                {product.name}
              </h1>

              <div className="mt-3 flex flex-wrap items-baseline gap-3">
                <span className="text-2xl font-bold text-foreground">
                  {formatCOP(Number(product.price))}
                </span>
                {discounted && product.previous_price && (
                  <span className="text-base text-muted line-through">
                    {formatCOP(Number(product.previous_price))}
                  </span>
                )}
              </div>
            </header>

            <p className="text-sm leading-relaxed text-foreground">{product.description}</p>

            <dl className="grid grid-cols-1 gap-3 rounded-[2px] border border-border bg-surface-alt p-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Material
                </dt>
                <dd className="mt-0.5 font-medium text-foreground">{product.material}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Diseño
                </dt>
                <dd className="mt-0.5 font-medium text-foreground">{designLabel}</dd>
              </div>
            </dl>

            {/* Selector de Color */}
            {colors.length > 0 && (
              <div className="space-y-2">
                <span className="block text-xs font-semibold uppercase tracking-wider text-foreground">
                  Color: <span className="font-normal text-muted">{activeColor}</span>
                </span>
                <div role="group" aria-label="Seleccionar color" className="flex flex-wrap gap-2">
                  {colors.map((color) => {
                    const isSelected = color === activeColor;
                    const colorHasStock = variants.some(
                      (v) => v.color === color && v.stock_quantity > 0,
                    );
                    return (
                      <button
                        key={color}
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => setSelectedColor(color)}
                        className={`inline-flex min-h-11 min-w-11 items-center justify-center rounded-[2px] border px-3.5 py-2 text-sm font-medium transition-colors ${
                          isSelected
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border-strong bg-background text-foreground hover:bg-surface-alt"
                        }`}
                      >
                        <span>{color}</span>
                        {!colorHasStock && (
                          <span className="ml-1.5 text-xs opacity-75">(Agotado)</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Selector de Talla */}
            {sizes.length > 0 && (
              <div className="space-y-2">
                <span className="block text-xs font-semibold uppercase tracking-wider text-foreground">
                  Talla: <span className="font-normal text-muted">{activeSize}</span>
                </span>
                <div role="group" aria-label="Seleccionar talla" className="flex flex-wrap gap-2">
                  {sizes.map((size) => {
                    const isSelected = size === activeSize;
                    const variantForSize = variants.find(
                      (v) => v.color === activeColor && v.size === size,
                    );
                    const sizeHasStock = (variantForSize?.stock_quantity ?? 0) > 0;
                    return (
                      <button
                        key={size}
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => setSelectedSize(size)}
                        className={`inline-flex min-h-11 min-w-11 items-center justify-center rounded-[2px] border px-3.5 py-2 text-sm font-semibold transition-colors ${
                          isSelected
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border-strong bg-background text-foreground hover:bg-surface-alt"
                        }`}
                      >
                        <span>{size}</span>
                        {!sizeHasStock && (
                          <span className="ml-1.5 text-xs font-normal opacity-75">(Agotado)</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Estado de disponibilidad de la combinación seleccionada */}
            <div aria-live="polite" className="pt-1">
              {variantInStock ? (
                <span className="inline-flex items-center rounded-[2px] border border-accent-success bg-background px-3 py-1 text-xs font-semibold uppercase tracking-wider text-accent-success">
                  Disponible · {selectedVariant?.stock_quantity}{" "}
                  {selectedVariant?.stock_quantity === 1 ? "unidad" : "unidades"}
                </span>
              ) : (
                <span className="inline-flex items-center rounded-[2px] bg-muted px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary-foreground">
                  Agotado
                </span>
              )}
            </div>
          </div>

          <div className="pt-4">
            <button
              type="button"
              disabled={!variantInStock}
              className="inline-flex min-h-11 w-full items-center justify-center rounded-[2px] bg-primary px-6 py-3 text-sm font-semibold uppercase tracking-wider text-primary-foreground transition-colors hover:bg-foreground/90 disabled:cursor-not-allowed disabled:bg-surface disabled:text-muted"
            >
              {variantInStock ? "Agregar al carrito" : "Agotado"}
            </button>
          </div>
        </section>
      </div>
    </article>
  );
}
