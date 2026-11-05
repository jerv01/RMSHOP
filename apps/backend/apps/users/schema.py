from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ClerkAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.users.authentication.ClerkAuthentication"
    name = "BearerAuth"

    def get_security_requirement(self, auto_schema):
        return {self.name: []}

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "Token JWT de sesión de Clerk. Se envía en el encabezado "
                "Authorization: Bearer <token>."
            ),
        }
