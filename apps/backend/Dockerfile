# Imagen del backend de RM Shop. Etapas: builder -> dev | runtime.

FROM ghcr.io/astral-sh/uv:0.13.6 AS uv

# Instala solo las dependencias de producción en un entorno virtual fuera del código,
# para que el montaje de apps/backend en desarrollo no lo oculte.
FROM python:3.14.10-slim AS builder
COPY --from=uv /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Desarrollo: agrega las dependencias de desarrollo y el servidor con recarga automática.
FROM builder AS dev
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN uv sync --frozen --no-install-project
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Producción: sin dependencias de desarrollo ni uv, con un usuario sin privilegios.
FROM python:3.14.10-slim AS runtime
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production
RUN groupadd --system app && useradd --system --gid app --no-create-home app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .
# Los valores son solo para que Django cargue la configuración; collectstatic no usa la base.
RUN DJANGO_SECRET_KEY=solo-para-construir DATABASE_URL=postgres://build:build@localhost/build \
    python manage.py collectstatic --noinput
USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]
