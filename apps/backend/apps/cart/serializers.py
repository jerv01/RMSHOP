from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.cart.models import Cart, CartItem, StockReservation


class CartItemAddInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "El campo variant_id es requerido.",
            "invalid": "El variant_id debe ser un número entero válido.",
            "min_value": "El variant_id debe ser mayor a cero.",
        },
    )
    quantity = serializers.IntegerField(
        default=1,
        min_value=1,
        error_messages={
            "invalid": "La cantidad debe ser un número entero válido.",
            "min_value": "La cantidad debe ser mayor a cero.",
        },
    )


class CartItemUpdateInputSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        min_value=1,
        required=True,
        error_messages={
            "required": "El campo quantity es requerido.",
            "invalid": "La cantidad debe ser un número entero válido.",
            "min_value": "La cantidad debe ser mayor a cero.",
        },
    )


class CartItemOutputSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(source="variant.product_id", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    color = serializers.CharField(source="variant.color", read_only=True)
    size = serializers.CharField(source="variant.size", read_only=True)
    unit_price = serializers.DecimalField(
        source="variant.product.price",
        max_digits=12,
        decimal_places=0,
        read_only=True,
    )
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        read_only=True,
    )
    reservation_expires_at = serializers.SerializerMethodField()
    is_reservation_active = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant_id",
            "product_id",
            "product_name",
            "product_slug",
            "color",
            "size",
            "unit_price",
            "quantity",
            "subtotal",
            "reservation_expires_at",
            "is_reservation_active",
        ]

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_reservation_expires_at(self, obj: CartItem):
        try:
            return obj.reservation.expires_at
        except StockReservation.DoesNotExist, AttributeError:
            return None

    @extend_schema_field(serializers.BooleanField())
    def get_is_reservation_active(self, obj: CartItem) -> bool:
        try:
            return obj.reservation.is_active()
        except StockReservation.DoesNotExist, AttributeError:
            return False


class CartOutputSerializer(serializers.ModelSerializer):
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        read_only=True,
    )
    items = CartItemOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "total_items",
            "total_price",
            "items",
        ]
