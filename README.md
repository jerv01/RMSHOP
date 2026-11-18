# RM Shop

Tienda en línea de la marca de ropa RM: una SPA en React, una API en Django y autenticación con Clerk, en un monorepo que se desarrolla solo con Docker. Este repositorio contiene los cimientos del proyecto; las historias de usuario se construyen encima.

- Arquitectura (fuente de verdad técnica): [docs/arquitectura.md](docs/arquitectura.md)
- Backlog con las 67 historias: [docs/backlog.md](docs/backlog.md)
- Configuración de Clerk: [docs/clerk-setup.md](docs/clerk-setup.md)

## Estructura

```text
rmshop/
├── apps/
│   ├── backend/             # Django + DRF (apps/core, users, catalog, inventory, cart, shipping, orders, payments)
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

7. (Opcional) Carga datos de ejemplo para tener catálogo desde el primer momento, ver [Datos de ejemplo](#datos-de-ejemplo).

Si cambias un `.env`, ejecuta `docker compose up -d` para recrear los servicios afectados. `docker compose restart` **no** vuelve a leer los `.env`.

## Direcciones

| Qué | URL |
| --- | --- |
| Frontend | <http://localhost:5173> |
| API | <http://localhost:8000/api/v1/> |
| Salud de la API | <http://localhost:8000/api/v1/health> |
| Mailpit (correos de prueba) | <http://localhost:8025> |
| PostgreSQL desde tu máquina | `localhost:5432` (o el valor de `DB_HOST_PORT`), usuario, contraseña y base `rmshop` |

## Datos de ejemplo

Las 4 categorías (Camisetas / Tops, Buzos / Sacos, Pantalones / Jeans, Conjuntos) y las 4 zonas de envío (Cali, Palmira, Jamundí, Yumbo) se crean solas con `migrate`. Los productos no: se cargan con un comando.

```bash
docker compose exec backend python manage.py seed_products
```

Crea 2 camisetas publicadas ("Camiseta Texturizada Blanca" y "Negra") a 89.900 COP, con foto, tallas M y L y 5 unidades por variante. Es idempotente: si el producto ya existe lo omite, así que puedes correrlo varias veces. Las imágenes viven en `apps/backend/apps/catalog/seed_images/` y las fotos procesadas quedan en `apps/backend/media/` (no se sube a git).

Para empezar de cero: `docker compose down -v`, `docker compose up -d`, `migrate` y `seed_products`.

## Autenticación en desarrollo

Todas las rutas del cliente piden una sesión de Clerk; el panel de administración pide además `role: "admin"` en `public_metadata` (ver [docs/clerk-setup.md](docs/clerk-setup.md)). Para probar la API con Swagger en <http://localhost:8000/api/v1/docs/>:

1. Inicia sesión en <http://localhost:5173> y, en la consola del navegador, ejecuta `await window.Clerk.session.getToken()`.
2. En Swagger usa **Authorize** y pega el token (dura cerca de un minuto: pide uno nuevo si responde `authentication_failed`).

Para entrar como administrador sin buscar el enlace en Clerk: `docker compose exec backend python manage.py get_admin_token`.

## Pagos con MercadoPago

El backend paga con la API de Orders de MercadoPago (tarjeta débito y PSE). Sin configurar, todo lo demás funciona y las rutas de pago responden `503`.

Variables en `apps/backend/.env` (explicadas en `apps/backend/.env.example`):

| Variable | Para qué |
| --- | --- |
| `MERCADOPAGO_ACCESS_TOKEN` | Credencial privada. La API de Orders **no acepta** credenciales `TEST-`: usa las de producción de un **usuario de prueba vendedor** |
| `MERCADOPAGO_CALLBACK_BASE_URL` | URL https pública a la que vuelve el cliente tras PSE. MercadoPago **rechaza `localhost`** (`processing_error`); en local pon `https://www.example.com` y, al terminar en el banco, abre a mano `http://localhost:5173/pedidos/<número>` |
| `MERCADOPAGO_WEBHOOK_SECRET` | Opcional en local. Valida la firma de las notificaciones (ver más abajo) |
| `CRON_SECRET` | Opcional en local. Protege el endpoint de tareas programadas |

Flujo de prueba sin armar el checkout a mano:

1. Agrega una camiseta al carrito (`/carrito`).
2. Presiona **Pagar con PSE (prueba)**: crea el pedido con una dirección fija de Cali y te lleva al banco de prueba de MercadoPago.
3. Completa el pago y abre `http://localhost:5173/pedidos/RM-000001` (con tu número): consulta a MercadoPago y muestra el estado.

Pagar con tarjeta débito necesita el formulario de MercadoPago (Card Payment Brick), que aún no está en el frontend; hasta entonces solo se prueba con tokens generados a mano.

Si cambias de `.env`, recuerda `docker compose up -d` (no `restart`).

### Tareas programadas

Un pedido sin pago a los 30 minutos se cancela y su stock vuelve; las reservas de carrito vencidas se liberan. Esto lo hace un comando que en producción llama `pg_cron` cada minuto (`POST /api/v1/internal/run-scheduled-tasks` con el header `X-Cron-Secret`). **En local no corre solo**: lánzalo a mano.

```bash
docker compose exec backend python manage.py run_scheduled_tasks
```

### Webhook de MercadoPago (opcional en local)

Sin webhook el estado del pago se actualiza igual (al volver del banco y con las tareas programadas); el webhook solo lo hace inmediato. Para probarlo hace falta una URL pública: levanta un túnel (por ejemplo `cloudflared tunnel --url http://localhost:8000`) y en el panel de MercadoPago (Webhooks, tópico **Order**) registra `https://<tu-túnel>/api/v1/webhooks/payments/mercadopago`. Copia la firma secreta a `MERCADOPAGO_WEBHOOK_SECRET` y agrega el dominio del túnel (por ejemplo `.trycloudflare.com`) a `DJANGO_ALLOWED_HOSTS`.

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
| Cargar productos de ejemplo | `docker compose exec backend python manage.py seed_products` |
| Liberar reservas y cancelar pedidos vencidos | `docker compose exec backend python manage.py run_scheduled_tasks` |
| Liberar solo reservas vencidas | `docker compose exec backend python manage.py cleanup_expired_reservations` |
| Revisar que no falten migraciones | `docker compose exec backend python manage.py makemigrations --check --dry-run` |
| Documentación de la API (Swagger) | <http://localhost:8000/api/v1/docs/> |
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

**Pagar da `503` (`payment_gateway_not_configured`):** falta `MERCADOPAGO_ACCESS_TOKEN` en `apps/backend/.env`; ponlo y ejecuta `docker compose up -d backend`.

**PSE falla con `processing_error`:** `MERCADOPAGO_CALLBACK_BASE_URL` apunta a `localhost` o a una URL sin https. Debe ser pública y https.

**Mi pedido sigue "Pendiente de Pago" y no vuelve el stock:** las tareas programadas no corren solas en local; ejecuta `run_scheduled_tasks`.

**Tras un `git pull` el backend falla por `httpx` o por tablas que no existen:** `docker compose up --build -d backend` y luego `migrate`.

**El frontend dice "Falta configurar Clerk":** falta `VITE_CLERK_PUBLISHABLE_KEY` en `apps/frontend/.env`. Complétala y ejecuta `docker compose up -d`.

## Convenciones

- **Una rama por historia de usuario**, con el número de la HU: `feature/HU-17-reserva-stock`. Las tareas de infraestructura usan `chore/…`.
- `main` está protegida: no se hace push directo; todo entra por pull request con revisión de al menos una persona.
- Commits con [Conventional Commits](https://www.conventionalcommits.org/) y descripción en español: `feat(backend): agrega autenticación con Clerk`.
- Código, nombres de archivos, modelos y variables en inglés; textos de interfaz, mensajes de error, comentarios y documentación en español.
- Antes de pedir revisión: pruebas, lint y formato de la app que tocaste en verde (tabla de comandos).
- Los errores de la API tienen un único formato: `{"code": "...", "message": "...", "fields": {...}}`.
- Los secretos nunca se suben a git: solo viven en archivos `.env`.
