import os

from clerk_backend_api import Clerk
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Genera un enlace de acceso mágico para iniciar sesión como Administrador en Clerk."

    def handle(self, *args, **options):
        secret_key = settings.CLERK_SECRET_KEY or os.environ.get("CLERK_SECRET_KEY")
        if not secret_key:
            self.stderr.write("CLERK_SECRET_KEY no está configurada en apps/backend/.env")
            return

        client = Clerk(bearer_auth=secret_key)
        users = client.users.list()

        admin_user = None
        for u in users:
            metadata = getattr(u, "public_metadata", {}) or {}
            if metadata.get("role") == "admin":
                admin_user = u
                break

        if not admin_user:
            self.stderr.write(
                "No se encontró ningún usuario con role='admin' en Clerk. "
                "Consulta docs/clerk-setup.md (sección 7) para asignar el rol."
            )
            return

        email = ""
        if admin_user.email_addresses:
            email = admin_user.email_addresses[0].email_address

        res = client.sign_in_tokens.create(request={"user_id": admin_user.id})
        sign_in_url = getattr(res, "url", None)

        self.stdout.write(
            self.style.SUCCESS(f"\nAdministrador encontrado: {email} ({admin_user.id})")
        )
        self.stdout.write("\nPara autenticarte y probar la API en Swagger UI:")
        self.stdout.write(
            f"1. Abre este enlace de acceso rápido en tu navegador:\n   {sign_in_url}\n"
        )
        self.stdout.write(
            "2. En http://localhost:5173, pulsa 'Copiar token para Swagger UI' "
            "(o ejecuta en consola F12: await window.Clerk.session.getToken())."
        )
        self.stdout.write(
            "3. En Swagger (http://localhost:8000/api/v1/docs/), pulsa el botón verde 'Authorize'."
        )
        self.stdout.write(
            "4. Pega el token y pulsa 'Authorize'. ¡Listo para probar los endpoints!\n"
        )
