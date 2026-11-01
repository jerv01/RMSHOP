from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .clerk import verify_webhook
from .permissions import IsCustomer
from .serializers import MeSerializer
from .services import handle_clerk_event


class MeView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        user = request.user
        data = {
            "id": user.pk,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": request.auth.role,
        }
        return Response(MeSerializer(data).data)


class ClerkWebhookView(APIView):
    """Recibe los eventos de Clerk. Público, protegido por la firma de Svix."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        # El cuerpo crudo se lee antes de tocar request.data: la firma se calcula sobre él.
        event = verify_webhook(request.body, request.headers)
        handle_clerk_event(event)
        return Response({"received": True})
