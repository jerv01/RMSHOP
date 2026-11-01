"""Configuración de producción. Todavía no se ejecuta en ningún entorno."""

from .base import *  # noqa: F403
from .base import RESEND_API_KEY

# HTTPS (sección 12.1 de la arquitectura)
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Correo transaccional con Resend
EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
ANYMAIL = {"RESEND_API_KEY": RESEND_API_KEY}
