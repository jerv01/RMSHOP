import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { useApi } from "@/shared/api/useApi";
import { env } from "@/shared/lib/env";
import { ErrorNotice, QueryFeedback, SuccessNotice } from "@/shared/ui/Feedback";
import { productPath, useAdminRefresh, useImages } from "./api";
import type { ProductImage } from "./types";

export function imageUrl(url: string): string {
  return new URL(url, `${env.apiUrl}/`).href;
}
export function validatePhoto(file: File): string | null {
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type))
    return "Selecciona una imagen JPG, PNG o WebP.";
  if (file.size > 5 * 1024 * 1024) return "La imagen no debe superar los 5 MB.";
  if (!file.size) return "La imagen está vacía.";
  return null;
}
export function ProductImages({ productId, published }: { productId: number; published: boolean }) {
  const api = useApi();
  const query = useImages(productId);
  const refresh = useAdminRefresh();
  const input = useRef<HTMLInputElement>(null);
  const [selection, setSelection] = useState<{ file: File; preview: string } | null>(null);
  const [alt, setAlt] = useState("");
  const [validation, setValidation] = useState("");
  const [message, setMessage] = useState("");
  useEffect(
    () => () => {
      if (selection) URL.revokeObjectURL(selection.preview);
    },
    [selection],
  );
  const upload = useMutation({
    mutationFn: async () => {
      if (!selection) throw new Error("Selecciona una imagen.");
      const formData = new FormData();
      formData.append("image", selection.file);
      formData.append("alt_text", alt.trim());
      return api<ProductImage>(`${productPath(productId)}/images`, { method: "POST", formData });
    },
    onSuccess: async () => {
      setSelection(null);
      setAlt("");
      if (input.current) input.current.value = "";
      setMessage("Fotografía guardada.");
      await refresh();
    },
  });
  const action = useMutation({
    mutationFn: async ({ remove, order }: { remove?: number; order?: number[] }) => {
      if (remove) return api(`${productPath(productId)}/images/${remove}`, { method: "DELETE" });
      return api(`${productPath(productId)}/images/reorder`, {
        method: "PATCH",
        json: { image_ids: order },
      });
    },
    onSuccess: async (_, variables) => {
      setMessage(variables.remove ? "Fotografía eliminada." : "Orden guardado.");
      await refresh();
    },
  });
  const busy = upload.isPending || action.isPending;
  const images = query.data ?? [];
  function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    if (!selection) {
      setValidation("Selecciona una imagen.");
      return;
    }
    setValidation("");
    upload.mutate();
  }
  function move(index: number, direction: number) {
    const ids = images.map((image) => image.id);
    [ids[index], ids[index + direction]] = [ids[index + direction], ids[index]];
    setMessage("");
    action.mutate({ order: ids });
  }
  return (
    <section className="panel space-y-5">
      <div>
        <h2>Fotografías</h2>
        <p className="muted">Hasta 3 fotos · JPG, PNG o WebP · Máximo 5 MB por archivo</p>
      </div>
      <QueryFeedback pending={query.isPending} error={query.error} retry={query.refetch} />
      <ErrorNotice error={upload.error || action.error} />
      {message && <SuccessNotice>{message}</SuccessNotice>}
      {query.isSuccess && (
        <>
          <div className="grid gap-5 sm:grid-cols-3">
            {images.map((image, index) => (
              <article key={image.id} className="space-y-3">
                {image.image_url ? (
                  <img
                    className="aspect-[3/4] w-full rounded object-cover bg-surface"
                    src={imageUrl(image.image_url)}
                    alt={image.alt_text}
                  />
                ) : (
                  <p>Imagen no disponible</p>
                )}
                <p className="text-sm">
                  {index + 1}. {image.alt_text}
                </p>
                <div className="flex flex-wrap gap-2">
                  <button
                    className="btn-secondary"
                    disabled={busy || index === 0}
                    aria-label={`Mover foto ${index + 1} antes`}
                    onClick={() => move(index, -1)}
                  >
                    ←
                  </button>
                  <button
                    className="btn-secondary"
                    disabled={busy || index === images.length - 1}
                    aria-label={`Mover foto ${index + 1} después`}
                    onClick={() => move(index, 1)}
                  >
                    →
                  </button>
                  <button
                    className="btn-danger"
                    disabled={busy || (published && images.length === 1)}
                    onClick={() => {
                      if (
                        window.confirm(
                          `¿Eliminar la fotografía ${index + 1}? Esta acción no se puede deshacer.`,
                        )
                      ) {
                        setMessage("");
                        action.mutate({ remove: image.id });
                      }
                    }}
                  >
                    Eliminar foto {index + 1}
                  </button>
                </div>
              </article>
            ))}
          </div>
          {images.length === 0 && (
            <p className="muted">Este producto todavía no tiene fotografías.</p>
          )}
          {published && images.length === 1 && (
            <p className="muted text-sm">
              La última foto de un producto publicado se conserva. Cambia a borrador antes de
              retirarla.
            </p>
          )}
          {images.length < 3 ? (
            <form onSubmit={submit} className="space-y-4 border-t border-border pt-5">
              <fieldset disabled={busy} className="space-y-4">
                <label className="field">
                  Nueva fotografía
                  <input
                    ref={input}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={(event) => {
                      setMessage("");
                      upload.reset();
                      setSelection(null);
                      const file = event.target.files?.[0];
                      if (!file) {
                        setValidation("");
                        return;
                      }
                      const error = validatePhoto(file);
                      setValidation(error ?? "");
                      if (!error) setSelection({ file, preview: URL.createObjectURL(file) });
                    }}
                    aria-describedby="photo-validation"
                  />
                </label>
                {validation && (
                  <p id="photo-validation" role="alert" className="field-error">
                    {validation}
                  </p>
                )}
                {selection && (
                  <img
                    src={selection.preview}
                    className="h-48 max-w-full rounded object-contain bg-surface"
                    alt="Vista previa de la nueva fotografía"
                  />
                )}
                <label className="field">
                  Texto alternativo
                  <input
                    value={alt}
                    maxLength={255}
                    onChange={(event) => setAlt(event.target.value)}
                    placeholder="Ej. Camiseta negra vista de frente"
                  />
                  <span className="muted text-sm">
                    Si lo dejas vacío se usará el nombre del producto. Por ahora solo se puede
                    definir al subir la foto.
                  </span>
                </label>
                <button className="btn-primary" type="submit" disabled={!selection || busy}>
                  {upload.isPending ? "Subiendo…" : "Subir fotografía"}
                </button>
              </fieldset>
            </form>
          ) : (
            <p className="notice">Has alcanzado el máximo de tres fotografías.</p>
          )}
        </>
      )}
    </section>
  );
}
