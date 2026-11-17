from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Carrito de {self.user}"

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0"))


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_items"
        verbose_name = "Ítem de carrito"
        verbose_name_plural = "Ítems de carrito"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_cart_variant",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="check_cart_item_quantity_gt_zero",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.variant} en {self.cart}"

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.variant.product.price


class StockReservation(models.Model):
    cart_item = models.OneToOneField(
        CartItem,
        on_delete=models.CASCADE,
        related_name="reservation",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    quantity = models.PositiveIntegerField()
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stock_reservations"
        verbose_name = "Reserva de inventario"
        verbose_name_plural = "Reservas de inventario"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="check_stock_reservation_quantity_gt_zero",
            ),
        ]

    def __str__(self) -> str:
        return f"Reserva {self.quantity}x {self.variant} (expira {self.expires_at})"

    def is_active(self) -> bool:
        return self.expires_at > timezone.now()
