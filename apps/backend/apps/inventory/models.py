from django.db import models


class StockMovement(models.Model):
    """Registro de auditoría de cada cambio manual o automático en el stock de una variante."""

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    admin = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    delta = models.IntegerField(
        help_text="Variación de stock: positivo para ingresos, negativo para deducciones o mermas.",
    )
    resulting_stock = models.PositiveIntegerField(
        help_text="Cantidad de stock resultante tras aplicar el movimiento.",
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        default="Ajuste manual",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "stock_movements"
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["variant", "-created_at"],
                name="idx_stock_mov_var_created",
            ),
        ]

    def __str__(self) -> str:
        sign = "+" if self.delta > 0 else ""
        return f"Variante #{self.variant_id}: {sign}{self.delta} -> stock {self.resulting_stock}"
