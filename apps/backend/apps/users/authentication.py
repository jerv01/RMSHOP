from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .clerk import TokenVerificationFailed, verify_session_token
from .services import get_or_create_user_from_claims


class ClerkAuthentication(BaseAuthentication):
    """Autentica con el token de sesión de Clerk en `Authorization: Bearer <token>`.

    Sin cabecera no autentica y la vista decide (los permisos responden 401). Con un token
    inválido o vencido responde 401 `authentication_failed`. Devuelve `(user, claims)`, así
    que `request.auth` es el `ClerkClaims` de la petición.
    """

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != b"bearer":
            return None

        try:
            claims = verify_session_token(request)
        except TokenVerificationFailed as exc:
            raise AuthenticationFailed() from exc
        return get_or_create_user_from_claims(claims), claims

    def authenticate_header(self, request):
        # Hace que DRF responda 401 (y no 403) cuando falta la autenticación.
        return 'Bearer realm="api"'
