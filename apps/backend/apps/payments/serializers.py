from rest_framework import serializers

from apps.orders.serializers import OrderSerializer
from apps.payments.models import Payment, PaymentMethod

_PSE_REQUIRED_FIELDS = [
    "financial_institution",
    "entity_type",
    "identification_type",
    "identification_number",
    "phone_area_code",
    "phone_number",
    "zip_code",
    "street_number",
    "neighborhood",
]


class StartPaymentInputSerializer(serializers.Serializer):
    """Datos para iniciar el pago. Para tarjeta débito solo llega el token del Card Payment Brick,
    nunca el número de la tarjeta (HU-19)."""

    method = serializers.ChoiceField(choices=PaymentMethod.choices)

    # Tarjeta débito (Card Payment Brick)
    token = serializers.CharField(max_length=64, required=False)
    payment_method_id = serializers.CharField(max_length=30, required=False)
    payment_type = serializers.CharField(max_length=30, required=False, default="debit_card")

    # Datos del pagador (opcionales en tarjeta, obligatorios en PSE)
    first_name = serializers.CharField(max_length=60, required=False)
    last_name = serializers.CharField(max_length=60, required=False)
    identification_type = serializers.CharField(max_length=10, required=False)
    identification_number = serializers.CharField(max_length=20, required=False)

    # PSE (HU-20)
    financial_institution = serializers.CharField(max_length=20, required=False)
    entity_type = serializers.ChoiceField(
        choices=[("individual", "Persona natural"), ("association", "Persona jurídica")],
        required=False,
    )
    phone_area_code = serializers.RegexField(r"^[0-9]{1,4}$", required=False)
    phone_number = serializers.RegexField(r"^[0-9 -]{7,15}$", required=False)
    zip_code = serializers.RegexField(r"^[0-9]{4,10}$", required=False)
    street_number = serializers.CharField(max_length=20, required=False)
    neighborhood = serializers.CharField(max_length=60, required=False)

    def validate(self, attrs):
        required = (
            ["token", "payment_method_id"]
            if attrs["method"] == PaymentMethod.DEBIT_CARD
            else _PSE_REQUIRED_FIELDS
        )
        missing = {name: ["Este campo es obligatorio."] for name in required if not attrs.get(name)}
        if missing:
            raise serializers.ValidationError(missing)
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "method",
            "status",
            "status_label",
            "status_detail",
            "amount",
            "redirect_url",
            "created_at",
        ]


class PaymentResultSerializer(serializers.Serializer):
    order = OrderSerializer()
    payment = PaymentSerializer(allow_null=True)


class PseBankSerializer(serializers.Serializer):
    id = serializers.CharField()
    description = serializers.CharField()
