import { useState, type FormEvent } from "react";

export function ProductLookup({ onSelect }: { onSelect: (id: number) => void }) {
  const [id, setId] = useState("");
  function submit(event: FormEvent) {
    event.preventDefault();
    const value = Number(id);
    if (Number.isSafeInteger(value) && value > 0) onSelect(value);
  }
  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
      <label className="field">
        ID del producto
        <input
          required
          type="number"
          min="1"
          max={Number.MAX_SAFE_INTEGER}
          step="1"
          value={id}
          onChange={(event) => setId(event.target.value)}
        />
      </label>
      <button className="btn-secondary" type="submit">
        Consultar producto
      </button>
    </form>
  );
}
