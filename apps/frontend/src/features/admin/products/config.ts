// 0002_seed_categories usa get_or_create sin fijar IDs. Estos son los IDs esperados
// en una base recién migrada; se permite indicar otro ID si la base ya tenía categorías.
export const initialCategories = [
  { id: 1, name: "Camisetas / Tops" },
  { id: 2, name: "Buzos / Sacos" },
  { id: 3, name: "Pantalones / Jeans" },
  { id: 4, name: "Conjuntos" },
];
export const statusLabels = { draft: "Borrador", published: "Publicado", archived: "Archivado" };
