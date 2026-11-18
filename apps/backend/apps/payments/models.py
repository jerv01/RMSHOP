import uuid

from django.db import models


class PaymentMethod(models.TextChoices):
    DEBIT_CARD = "debit_card", "Tarjeta débito"
    PSE = "pse", "PSE"


class PaymentStatus(models.TextChoices):
    INITIATED = "initiated", "Iniciado"
    PROCESSING = "processing", "En proceso"
    ACTION_REQUIRED = "action_required", "Esperando acción del cliente"
    APPROVED = "approved", "Aprobado"
    REJECTED = "rejected", "Rechazado"
    ERROR = "error", "Error de comunicación"


# Un pago en estos estados bloquea un nuevo intento sobre el mismo pedido (AC-HU-21-3).
ACTIVE_PAYMENT_STATUSES = [
    PaymentStatus.INITIATED,
    PaymentStatus.PROCESSING,
    PaymentStatus.ACTION_REQUIRED,
    PaymentStatus.APPROVED,
]


class Payment(models.Model):
    """Intento de pago de un pedido en MercadoPago. Nunca guarda datos ni tokens de tarjeta."""

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="payments")
    provider = models.CharField(max_length=30, default="mercadopago")
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED
    )
    status_detail = models.CharField(max_length=60, blank=True)
    # Identificadores de MercadoPago (orden y transacción). Únicos para aplicar cada
    # respuesta una sola vez.
    mp_order_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    mp_payment_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    # Se envía como X-Idempotency-Key: reintentar la misma petición no crea un segundo cobro.
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # URL del banco para completar un pago PSE.
    redirect_url = models.URLField(max_length=1000, blank=True)
    # Última respuesta de MercadoPago, saneada (sin tokens).
    raw_response = models.JSONField(default=dict, blank=True)
    # Pago aprobado cuando el pedido ya no estaba pendiente (p. ej. cancelado por tiempo).
    needs_review = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["order"],
                condition=models.Q(status__in=ACTIVE_PAYMENT_STATUSES),
                name="uniq_active_payment_per_order",
            ),
        ]

    def __str__(self) -> str:
        return f"Pago {self.get_method_display()} de {self.order} ({self.status})"
