from django.db import DatabaseError, connection


def is_database_healthy() -> bool:
    """Ejecuta una consulta trivial para comprobar que la base responde."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return False
    return True


def run_scheduled_tasks() -> dict[str, int]:
    """Tareas periódicas (cada minuto vía pg_cron): reservas vencidas y pedidos sin pago (HU-24)."""
    # Importación diferida: core es la app base y no debe depender de las demás al cargar.
    from apps.cart.services import release_expired_reservations
    from apps.payments.services import cancel_expired_orders

    return {
        "released_reservations": release_expired_reservations(),
        "cancelled_orders": cancel_expired_orders(),
    }
