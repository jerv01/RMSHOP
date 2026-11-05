from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .clerk import verify_webhook
from .permissions import IsCustomer, IsRMAdmin
from .selectors import list_administrators
from .serializers import AdministratorSerializer, MeSerializer
from .services import handle_clerk_event, invite_administrator, remove_administrator


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


class AdministratorListCreateView(APIView):
    """Lista e invita administradores (HU-12). Solo administradores."""

    permission_classes = [IsRMAdmin]

    def get(self, request):
        administrators = list_administrators(current_clerk_user_id=request.user.clerk_user_id)
        return Response(AdministratorSerializer(administrators, many=True).data)

    def post(self, request):
        raw_email = request.data.get("email") if hasattr(request.data, "get") else None
        email = invite_administrator(actor=request.user, email=raw_email)
        return Response({"status": "invited", "email": email}, status=status.HTTP_201_CREATED)


class AdministratorDetailView(APIView):
    permission_classes = [IsRMAdmin]

    def delete(self, request, clerk_user_id):
        remove_administrator(actor=request.user, target_clerk_user_id=clerk_user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
