from rest_framework import serializers

from apps.catalog.serializers import ProductVariantSerializer
from apps.inventory.models import StockMovement
from apps.users.models import User


class StockAdjustmentInputSerializer(serializers.Serializer):
    """Payload para ajuste manual de stock por variante (HU-37)."""

    delta = serializers.IntegerField(
        required=True,
        help_text="Cantidad a sumar (positivo) o restar (negativo) al stock actual.",
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        default="Ajuste manual",
        help_text="Motivo del ajuste (ej.: ingreso de mercancía, merma, corrección).",
    )

    def validate_delta(self, value: int) -> int:
        if value == 0:
            raise serializers.ValidationError("El cambio de stock (delta) no puede ser cero.")
        return value


class StockMovementAdminSerializer(serializers.ModelSerializer):
    """Representación mínima del administrador que realizó el ajuste."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class StockMovementSerializer(serializers.ModelSerializer):
    """Representación de un movimiento de inventario / historial de auditoría."""

    admin = StockMovementAdminSerializer(read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "variant_id",
            "delta",
            "resulting_stock",
            "reason",
            "admin",
            "created_at",
        ]


class StockAdjustmentResponseSerializer(serializers.Serializer):
    """Respuesta tras realizar un ajuste manual de stock."""

    variant = ProductVariantSerializer(read_only=True)
    movement = StockMovementSerializer(read_only=True)
