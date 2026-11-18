from rest_framework import serializers

from apps.orders.models import Order, OrderItem, OrderStatusHistory


class CheckoutInputSerializer(serializers.Serializer):
    """Datos mínimos de envío para crear el pedido (checkout provisional, HU-19 a HU-21)."""

    municipality = serializers.CharField(max_length=100)
    address_line = serializers.CharField(max_length=255)
    recipient_name = serializers.CharField(max_length=120)
    phone = serializers.RegexField(
        regex=r"^\+?[0-9 ]{7,20}$",
        max_length=20,
        error_messages={"invalid": "Ingresa un teléfono válido (solo números)."},
    )


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "variant_id",
            "product_name",
            "color",
            "size",
            "unit_price",
            "quantity",
            "subtotal",
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    to_status_label = serializers.CharField(source="get_to_status_display", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ["from_status", "to_status", "to_status_label", "note", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    """Detalle del pedido. `status_label` muestra el estado en texto, no solo con color (HU-21)."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_number",
            "status",
            "status_label",
            "subtotal",
            "shipping_cost",
            "total",
            "municipality",
            "address_line",
            "recipient_name",
            "phone",
            "payment_expires_at",
            "created_at",
            "updated_at",
            "items",
            "status_history",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = ["order_number", "status", "status_label", "total", "created_at"]
