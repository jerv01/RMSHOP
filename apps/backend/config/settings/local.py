"""Configuración de desarrollo local con Docker Compose."""

from .base import *  # noqa: F403

# DEBUG se lee de DJANGO_DEBUG en base.py.

# Los correos se envían por SMTP a Mailpit (interfaz web en http://localhost:8025).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
