from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import build_error
from .services import is_database_healthy


class HealthView(APIView):
    """Estado de la API y de la base de datos. Público y sin Clerk."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        if is_database_healthy():
            return Response({"status": "ok", "database": "ok"})
        body = {"status": "error", "database": "error"}
        body |= build_error("service_unavailable", "La base de datos no responde.")
        return Response(body, status=status.HTTP_503_SERVICE_UNAVAILABLE)
