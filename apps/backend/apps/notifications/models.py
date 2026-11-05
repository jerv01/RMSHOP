from django.db import models


class NotificationLog(models.Model):
    """Registro de cada correo transaccional: evita duplicados y permite reintentar los fallidos.

    Hoy solo guarda correos a usuarios (HU-43). Cuando existan los pedidos se agregará `order`
    y la unicidad pasará a incluirlo (docs/arquitectura.md, sección 7.3).
    """

    class Event(models.TextChoices):
        WELCOME = "welcome", "Bienvenida"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Fallido (se reintenta)"
        UNDELIVERABLE = "undeliverable", "No entregable (no se reintenta)"

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="+")
    event = models.CharField(max_length=30, choices=Event)
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification_log"
        constraints = [
            models.UniqueConstraint(fields=["user", "event"], name="unique_user_event"),
        ]

    def __str__(self):
        return f"{self.event} -> {self.user_id}: {self.status}"
