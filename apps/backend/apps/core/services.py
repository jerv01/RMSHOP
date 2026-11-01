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
