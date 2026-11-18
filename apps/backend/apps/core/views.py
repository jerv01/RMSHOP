import hmac

from django.conf import settings
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import build_error
from .services import is_database_healthy, run_scheduled_tasks


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


class ScheduledTasksView(APIView):
    """Ejecuta las tareas periódicas. Lo llama pg_cron cada minuto con X-Cron-Secret (HU-24)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        secret = settings.CRON_SECRET
        received = request.headers.get("X-Cron-Secret", "")
        if not secret or not hmac.compare_digest(secret.encode(), received.encode()):
            raise exceptions.PermissionDenied()
        return Response(run_scheduled_tasks())
