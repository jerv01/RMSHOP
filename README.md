# RM Shop

Tienda en línea de la marca de ropa RM: una SPA en React, una API en Django y autenticación con Clerk, en un monorepo que se desarrolla solo con Docker. Este repositorio contiene los cimientos del proyecto; las historias de usuario se construyen encima.

- Arquitectura (fuente de verdad técnica): [docs/arquitectura.md](docs/arquitectura.md)
- Backlog con las 67 historias: [docs/backlog.md](docs/backlog.md)
- Configuración de Clerk: [docs/clerk-setup.md](docs/clerk-setup.md)

## Estructura

```text
rmshop/
├── apps/
│   ├── backend/             # Django + DRF (apps/core, users, catalog, inventory, notifications)
│   │   ├── config/          # settings/ (base, local, production), urls, wsgi
│   │   ├── pyproject.toml   # dependencias (uv) y configuración de ruff y pytest
│   │   └── uv.lock
│   └── frontend/            # React + Vite + TypeScript + Tailwind 4
│       ├── src/             # app/, features/, shared/
│       ├── package.json
│       └── pnpm-lock.yaml
├── docs/
├── docker-compose.yml       # db, backend, frontend y mailpit
└── .env.example             # variables opcionales de Compose
```

Cada app tiene su propio lockfile; no hay `package.json` ni workspace en la raíz.

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (o Docker Engine) con **Docker Compose v2**: `docker compose version` debe funcionar.
- Git.

**No necesitas** instalar Node, pnpm, Python ni uv: todo corre dentro de los contenedores.

## Inicio rápido

1. Clona el repositorio y entra a la carpeta:

   ```bash
   git clone <url-del-repositorio> rmshop
   cd rmshop
   ```

2. Copia los archivos de ejemplo de variables de entorno.

   ```bash
   # Linux, macOS o Git Bash
   cp apps/backend/.env.example apps/backend/.env
   cp apps/frontend/.env.example apps/frontend/.env
   cp .env.example .env            # opcional: solo para cambiar puertos o credenciales de la base
   ```

   ```powershell
   # PowerShell
   Copy-Item apps/backend/.env.example apps/backend/.env
   Copy-Item apps/frontend/.env.example apps/frontend/.env
   Copy-Item .env.example .env
   ```

3. Completa las claves de Clerk (`CLERK_SECRET_KEY` en `apps/backend/.env` y `VITE_CLERK_PUBLISHABLE_KEY` en `apps/frontend/.env`). Pídelas a quien configuró Clerk o sigue [docs/clerk-setup.md](docs/clerk-setup.md). Puedes saltarte este paso para ver el proyecto arrancar: sin las claves el frontend muestra una pantalla de configuración y `GET /api/v1/me` responde `503`.

4. Levanta todo:

   ```bash
   docker compose up --build
   ```

   La primera vez tarda unos minutos (descarga imágenes e instala dependencias). Espera a que `docker compose ps` muestre los cuatro servicios como `healthy`.

5. Crea las tablas (las migraciones **no** se aplican solas). En otra terminal:

   ```bash
   docker compose exec backend python manage.py migrate
   ```

6. Comprueba que funciona: abre <http://localhost:5173> y revisa el bloque "Estado de la API", o ejecuta `curl http://localhost:8000/api/v1/health`, que debe responder `{"status":"ok","database":"ok"}`.

Si cambias un `.env`, ejecuta `docker compose up -d` para recrear los servicios afectados. `docker compose restart` **no** vuelve a leer los `.env`.

## Direcciones

| Qué | URL |
| --- | --- |
| Frontend | <http://localhost:5173> |
| API | <http://localhost:8000/api/v1/> |
| Salud de la API | <http://localhost:8000/api/v1/health> |
| Mailpit (correos de prueba) | <http://localhost:8025> |
| PostgreSQL desde tu máquina | `localhost:5432` (o el valor de `DB_HOST_PORT`), usuario, contraseña y base `rmshop` |

## Comandos frecuentes

Todos se ejecutan desde la raíz del repositorio.

| Tarea | Comando |
| --- | --- |
| Pruebas del backend | `docker compose run --rm backend pytest` |
| Lint del backend | `docker compose run --rm backend ruff check .` |
| Formato del backend | `docker compose run --rm backend ruff format .` (revisar sin cambiar: `ruff format --check .`) |
| Crear migraciones | `docker compose exec backend python manage.py makemigrations` |
| Aplicar migraciones | `docker compose exec backend python manage.py migrate` |
| Shell de Django | `docker compose exec backend python manage.py shell` |
| Pruebas del frontend | `docker compose run --rm frontend pnpm test --run` |
| Lint del frontend | `docker compose run --rm frontend pnpm lint` |
| Tipos del frontend | `docker compose run --rm frontend pnpm typecheck` |
| Formato del frontend | `docker compose run --rm frontend pnpm format` |
| Compilar el frontend | `docker compose run --rm frontend pnpm build` |
| Ver logs | `docker compose logs -f backend` (o `frontend`, `db`, `mailpit`) |
| Detener sin borrar datos | `docker compose down` |
| Reiniciar la base (borra los datos) | `docker compose down -v` y luego `docker compose up -d` y `migrate` |
| Consola de PostgreSQL | `docker compose exec db psql -U rmshop` |

Los cambios en el código se reflejan solos (hot reload) en ambas apps.

## Agregar una dependencia

El `lockfile` se regenera **dentro del contenedor**, así que no necesitas instalar uv ni pnpm. Después, el resto del equipo reconstruye sus imágenes.

**Backend** (actualiza `pyproject.toml` y `uv.lock`):

```bash
docker compose exec backend uv add <paquete>          # producción
docker compose exec backend uv add --dev <paquete>    # desarrollo y pruebas
docker compose up --build -d backend                  # reconstruye la imagen
```

**Frontend** (actualiza `package.json` y `pnpm-lock.yaml`):

```bash
docker compose exec frontend pnpm add <paquete>       # producción
docker compose exec frontend pnpm add -D <paquete>    # desarrollo y pruebas
```

Sube `pyproject.toml` y `uv.lock` (o `package.json` y `pnpm-lock.yaml`) en el mismo commit. Quien reciba el cambio ejecuta `docker compose up --build -V` (ver "node_modules obsoleto" más abajo).

## Solución de problemas

**El puerto 5432 está ocupado** (`address already in use`): tienes un PostgreSQL instalado en tu máquina. Crea el archivo `.env` de la raíz con otro puerto y vuelve a levantar:

```dotenv
DB_HOST_PORT=5433
```

Solo cambia el puerto de tu máquina; el backend sigue conectándose a la base por la red de Docker.

**El hot reload no detecta cambios del frontend** (Docker en Windows o macOS): en `apps/frontend/.env` pon `WATCH_POLLING=true` y ejecuta `docker compose up -d`. El backend recarga solo.

**Errores raros de finales de línea** (`exec ... no such file or directory` o `^M` en scripts), sobre todo en Windows: el repositorio fuerza LF con `.gitattributes`. Si clonaste con CRLF, ejecuta `git config core.autocrlf false`, vuelve a clonar o corre `git add --renormalize .` y revisa que tu editor guarde en LF.

**`node_modules` obsoleto tras cambiar dependencias** (el frontend no encuentra un paquete recién agregado por otra persona): el volumen de `node_modules` conserva el contenido de la imagen anterior. Reconstruye y renueva solo ese volumen, sin tocar la base:

```bash
docker compose up --build -V frontend
```

**Cambié `pyproject.toml` o `uv.lock` y el backend no ve el paquete:** `docker compose up --build -d backend`.

**`env file ... not found`:** falta copiar un `.env.example` (paso 2 del inicio rápido).

**Linux:** los archivos que crea un contenedor (migraciones, lockfiles) pueden quedar con dueño `root`. Corrígelo con `sudo chown -R "$USER": apps`. En sistemas con SELinux (Fedora, RHEL) los montajes ya llevan la etiqueta `:z` en `docker-compose.yml`.

**El frontend dice "Falta configurar Clerk":** falta `VITE_CLERK_PUBLISHABLE_KEY` en `apps/frontend/.env`. Complétala y ejecuta `docker compose up -d`.

## Convenciones

- **Una rama por historia de usuario**, con el número de la HU: `feature/HU-17-reserva-stock`. Las tareas de infraestructura usan `chore/…`.
- `main` está protegida: no se hace push directo; todo entra por pull request con revisión de al menos una persona.
- Commits con [Conventional Commits](https://www.conventionalcommits.org/) y descripción en español: `feat(backend): agrega autenticación con Clerk`.
- Código, nombres de archivos, modelos y variables en inglés; textos de interfaz, mensajes de error, comentarios y documentación en español.
- Antes de pedir revisión: pruebas, lint y formato de la app que tocaste en verde (tabla de comandos).
- Los errores de la API tienen un único formato: `{"code": "...", "message": "...", "fields": {...}}`.
- Los secretos nunca se suben a git: solo viven en archivos `.env`.
