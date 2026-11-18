import { useEffect, useState } from "react";
import type { CartItem } from "./types";

export function ReservationCountdown({
  item,
  updatedAt,
  busy,
  onExpire,
  onReReserve,
}: {
  item: CartItem;
  updatedAt: number;
  busy: boolean;
  onExpire: (reservationKey: string) => void;
  onReReserve: () => void;
}) {
  const [now, setNow] = useState(() => Date.now());
  const active = item.reservation_status === "active" && item.is_reservation_active;
  // El tiempo recibido se ancla a la respuesta, no a la entrada en esta página.
  // Así se conserva al usar la caché y no depende del reloj configurado por el cliente.
  const deadline =
    item.time_remaining_seconds !== null
      ? updatedAt + item.time_remaining_seconds * 1000
      : Date.parse(item.reservation_expires_at ?? "");
  const seconds =
    active && Number.isFinite(deadline)
      ? Math.max(0, Math.ceil((deadline - Math.max(now, updatedAt)) / 1000))
      : 0;
  const expired = !active || seconds === 0;
  const reservationKey = `${item.id}:${item.reservation_expires_at}`;

  useEffect(() => {
    if (!active) return;
    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, [active]);

  useEffect(() => {
    if (active && expired && !busy) onExpire(reservationKey);
  }, [active, expired, busy, onExpire, reservationKey]);

  const time = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;

  return (
    <div className="mt-3 space-y-2 text-sm">
      <p>
        Reserva:{" "}
        <span aria-label="Tiempo restante de reserva" className="font-semibold tabular-nums">
          {time}
        </span>
      </p>
      {expired && (
        <>
          <p className="font-semibold">Tu reserva expiró</p>
          <button type="button" className="btn-secondary" disabled={busy} onClick={onReReserve}>
            Volver a reservar
          </button>
        </>
      )}
    </div>
  );
}
