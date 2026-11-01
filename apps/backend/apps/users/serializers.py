from rest_framework import serializers


class MeSerializer(serializers.Serializer):
    """Perfil de la sesión actual. El rol viene del token, no de la base."""

    id = serializers.IntegerField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField(allow_null=True)
