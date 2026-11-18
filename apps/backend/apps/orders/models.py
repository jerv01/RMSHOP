from django.conf import settings
from django.db import models


class OrderStatus(models.TextChoices):
    """Estados del pedido (arquitectura §5). La etiqueta es el texto que ve el cliente (HU-21)."""

    PENDING_PAYMENT = "pending_payment", "Pendiente de Pago"
    PAYMENT_APPROVED = "payment_approved", "Pago aprobado"
    PAYMENT_REJECTED = "payment_rejected", "Pago rechazado"
    IN_PREPARATION = "in_preparation", "En preparación"
    SHIPPED = "shipped", "Enviado"
    DELIVERED = "delivered", "Entregado"
    CANCELLED = "cancelled", "Cancelado"


class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT,
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=0)
    total = models.DecimalField(max_digits=12, decimal_places=0)
    # Copia fija de la dirección de envío al momento de la compra.
    municipality = models.CharField(max_length=100)
    address_line = models.CharField(max_length=255)
    recipient_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    # Límite para recibir respuesta del pago; después aplica la cancelación de HU-24.
    payment_expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="idx_orders_status_created"),
            models.Index(fields=["user", "-created_at"], name="idx_orders_user_created"),
        ]

    def __str__(self) -> str:
        return self.order_number or f"Pedido #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
    )
    # Copias fijas: el pedido no cambia si luego se edita o borra el producto.
    product_name = models.CharField(max_length=255)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=20)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)

    class Meta:
        db_table = "order_items"
        verbose_name = "Ítem de pedido"
        verbose_name_plural = "Ítems de pedido"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="check_order_item_quantity_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_name} ({self.color}/{self.size})"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    # Vacío en la entrada de creación del pedido.
    from_status = models.CharField(max_length=20, choices=OrderStatus.choices, blank=True)
    to_status = models.CharField(max_length=20, choices=OrderStatus.choices)
    # Nulo cuando el cambio lo hace el sistema (pasarela, tareas programadas).
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_history"
        verbose_name = "Historial de estado de pedido"
        verbose_name_plural = "Historial de estados de pedido"
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.order}: {self.from_status} -> {self.to_status}"
