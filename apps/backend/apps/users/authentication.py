from rest_framework.authentication import BaseAuthentication


class ClerkAuthentication(BaseAuthentication):
    """Marcador temporal; la fase 2 implementa la verificación del token de Clerk."""

    def authenticate(self, request):
        return None

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
