"""Configuración base de RM Shop.

Todas las variables de entorno se leen en este archivo; `local.py` y `production.py`
solo ajustan el comportamiento según el entorno.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if value is None or (required and value == ""):
        raise ImproperlyConfigured(
            f"Falta la variable de entorno {name}. "
            "Copia apps/backend/.env.example a apps/backend/.env y complétala."
        )
    return value


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


# Núcleo
SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

# Sin admin, auth, sessions ni messages: la API se autentica solo con token Bearer de Clerk
# y el panel de administración vive en el frontend.
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "apps.core",
    "apps.users",
    "apps.catalog",
    "apps.inventory",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

DATABASES = {"default": dj_database_url.parse(env("DATABASE_URL", required=True))}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Internacionalización
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# Archivos estáticos (servidos por WhiteNoise)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Archivos de medios subidos por usuarios
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": env(
            "DEFAULT_FILE_STORAGE_BACKEND",
            "django.core.files.storage.FileSystemStorage",
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

# CORS y CSRF
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
# Sin efecto mientras no exista el middleware CSRF; se conserva por la arquitectura (sección 8.4).
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Django REST Framework: seguro por defecto; las vistas públicas declaran AllowAny.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.users.authentication.ClerkAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "RM Shop API",
    "DESCRIPTION": "API REST de la tienda en línea RM Shop",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"BearerAuth": []}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": ("Token JWT de sesión de Clerk. Pega aquí el token (sin 'Bearer')."),
            }
        }
    },
}

# Clerk: pueden quedar vacías; solo fallan las rutas que las necesitan.
CLERK_SECRET_KEY = env("CLERK_SECRET_KEY", "")
CLERK_WEBHOOK_SECRET = env("CLERK_WEBHOOK_SECRET", "")
CLERK_AUTHORIZED_PARTIES = env_list("CLERK_AUTHORIZED_PARTIES")
CLERK_JWT_KEY = env("CLERK_JWT_KEY", "")

# Correo
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "25"))
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "RM Shop <no-reply@rmshop.local>")
RESEND_API_KEY = env("RESEND_API_KEY", "")
