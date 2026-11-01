# RM Shop - Arquitectura base del proyecto

Nov 1, 2026 · @VALENTINA

RM Shop es una tienda en línea de alcance local: SPA en React, API en Django, base de datos en Supabase y autenticación en Clerk, en un monorepo con Docker. Cubre las 67 historias del backlog (12 épicas).

## 1. Resumen y alcance

RM Shop centraliza el catálogo de la marca RM y vende en Cali, Palmira, Jamundí y Yumbo con pago en tarjeta débito o Nequi, un chatbot de IA y un panel para máximo 3 administradores.

| Restricción | Origen | Resolución |
| --- | --- | --- |
| Catálogo de menos de 30 productos; listado en 3 s o menos | HU-1 | Listado en una sola llamada, con caché y CDN |
| Disponibilidad mensual de 99 % | HU-1 | No la garantiza el plan gratuito de Render; ver secciones 2.1 y 13.2 |
| El visitante navega todo el portal; al agregar al carrito o abrir el carrito se le pide registro o inicio de sesión | HU-3, HU-13 | Catálogo y ficha públicos; Clerk al agregar o abrir el carrito |
| Reserva de stock de 15 minutos | HU-17, HU-18 | Tabla de reservas; stock disponible = stock menos reservas vigentes, calculado al leer |
| Cancelar el pedido a los 30 min (±60 s) sin respuesta de la pasarela | HU-24 | `pg_cron` de Supabase llama cada minuto a un endpoint interno de la API |
| Correos en 2 minutos o menos | Épica 9 | Envío tras confirmar la transacción, con reintento en la llamada de cada minuto |
| Pago con tarjeta débito y Nequi | HU-19, HU-20 | Wompi detrás de una interfaz propia |
| Máximo 3 administradores, con cuenta separada | HU-11, HU-12 | Rol `admin` en Clerk; límite validado en el backend |
| Envío a 4 municipios con tarifa fija | Épica 5 | `shipping_zones`: Cali 5.000 COP; Palmira, Jamundí y Yumbo 10.000 COP |
| Chatbot de texto con sesión, límite de uso y sin datos personales | HU-50 a HU-54 | Servicio en el backend con Gemini y herramientas acotadas |
| Español y COP | HU-60 | Clerk en español; formato `es-CO` |
| Texto alternativo, contraste 4.5:1 y teclado | HU-61, HU-62, HU-62b | Radix UI y ESLint `jsx-a11y` |

## 2. Stack tecnológico

| Capa | Tecnología | Versión |
| --- | --- | --- |
| Frontend | React + Vite + TypeScript | React 19, Vite 6, TypeScript 5.x |
| Paquetes frontend | pnpm | 10.x |
| Entorno frontend | Node.js | 26.12.1 o superior |
| Backend | Django + Django REST Framework | Django 5.2.18 o superior (LTS) |
| Servidor WSGI | Gunicorn | Última estable |
| Paquetes backend | uv | Última estable |
| Entorno backend | Python | 3.14 (última 3.14.x) |
| Base de datos | PostgreSQL en Supabase | Transaction Pooler, puerto 6543 |
| Autenticación | Clerk | n/a |
| Pagos | Wompi | n/a |
| Correo transaccional | Resend con `django-anymail` | n/a |
| Chatbot | API de Gemini con el SDK `google-genai` | Modelo Flash, configurable |
| Imágenes | Supabase Storage | n/a |
| Tareas programadas | `pg_cron` y `pg_net` de Supabase hacia un endpoint interno de la API | n/a |
| Contenedores | Docker y Docker Compose | Compose v2 |
| Despliegue | Vercel (frontend) y Render (backend), planes gratuitos | n/a |
| CI/CD | GitHub Actions | n/a |

Fuera de esta versión: Celery, Redis, Sentry y generación de tipos desde OpenAPI.

### 2.1 Planes gratuitos

| Servicio | Plan | Límites relevantes | Efecto en el proyecto |
| --- | --- | --- | --- |
| Render | Gratuito | 750 horas al mes; se suspende tras 15 minutos sin tráfico y tarda hasta 1 minuto en arrancar; sin disco persistente | La llamada de `pg_cron` cada minuto lo mantiene activo; aun así no garantiza el 99 % de HU-1 |
| Supabase | Gratuito | 500 MB de base de datos, 1 GB de archivos, 5 GB de egreso; pausa tras 7 días de inactividad; sin copias automáticas | Alcanza para menos de 30 productos; copias de seguridad manuales con `pg_dump` |
| Clerk | Hobby | 50.000 usuarios retenidos al mes | Cubre el volumen local |
| Wompi | Sin costo fijo | Comisión por transacción | Costo variable por venta |
| Resend | Gratuito | 3.000 correos al mes, 100 al día, 1 dominio | Con 4 correos por pedido, unos 25 pedidos al día |
| Gemini API | Capa gratuita | Límites por minuto y por día; el contenido enviado puede usarse para mejorar productos de Google | El límite de uso por cliente (HU-51) se ajusta a la cuota |
| Vercel | Hobby | Solo uso personal y no comercial | No cubre la tienda de un cliente; ver 13.1 |

Fuentes: [Render](https://temps.sh/blog/render-pricing-2026), [Supabase](https://supabase.com/pricing), [Clerk](https://clerk.com/articles/clerk-pricing-explained), [Resend](https://resend.com/pricing), [Gemini API](https://yingtu.ai/en/blog/google-gemini-api-free-tier-limits-2026) y [Vercel](https://vercel.com/docs/limits/fair-use-guidelines). Estado al 1 de noviembre de 2026.

## 3. Arquitectura de infraestructura y monorepo

Dos despliegues propios, Vercel y Render, y cinco servicios administrados: Supabase, Clerk, la pasarela de pagos, el correo y la IA.

&#91;embedded content: arquitectura de red · 2 despliegues propios y 5 servicios administrados\]

El navegador inicia sesión con Clerk, descarga la SPA desde Vercel y llama a la API de Render con el token de sesión. Solo la API se conecta a Wompi, Resend y Gemini; `pg_cron` de Supabase llama cada minuto al endpoint interno de tareas.

### 3.1 Estructura del monorepo

```text
rmshop/
├── .github/workflows/          # ci-backend.yml, ci-frontend.yml
├── apps/
│   ├── frontend/               # React + Vite
│   │   ├── src/                # app/, features/, shared/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── pnpm-lock.yaml
│   │   ├── Dockerfile
│   │   ├── vercel.json
│   │   └── .env.example
│   └── backend/                # Django + DRF
│       ├── apps/               # users, catalog, inventory, cart, orders,
│       │                       # payments, shipping, notifications, chatbot, core
│       ├── config/             # settings/ (base, local, production), urls, wsgi
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── Dockerfile
│       └── .env.example
├── render.yaml
├── docker-compose.yml
├── .gitignore
└── README.md
```

### 3.2 Convenciones

- `render.yaml` va en la raíz y define el servicio web (imagen Docker de `apps/backend`) en el plan gratuito.
- El Root Directory de Vercel es `apps/frontend` y se configura en el proyecto de Vercel; `vercel.json` guarda las reescrituras de la SPA y las cabeceras de seguridad.
- Cada app tiene su propio lockfile; no se usa `pnpm-workspace.yaml`.

## 4. Modelo de datos

Se conserva el esquema propuesto, sin `reviews` (ninguna historia la usa), con ajustes de campos y seis tablas nuevas.

&#91;embedded content: modelo de datos · 12 tablas del esquema propuesto y 6 nuevas\]

### 4.1 Ajustes al esquema

| Tabla | Cambio | Historias |
| --- | --- | --- |
| `users` | Solo `clerk_user_id` único, `email`, `first_name`, `last_name`, `created_at`; sin contraseña ni rol | HU-7 a HU-12 |
| `user_addresses` | Una por cliente (`user_id` único); `zone_id` (FK a `shipping_zones`), `address_line1`, `recipient_name`, `phone`; campos finales según P-6 | HU-25, HU-28 |
| `shipping_zones` (nueva) | `municipality` único, `fee`, `is_active`; datos iniciales: Cali 5.000, Palmira 10.000, Jamundí 10.000 y Yumbo 10.000 (COP) | HU-25 a HU-28 |
| `products` | `description` y `category_id` obligatorios; `material`; `status` con borrador, publicado y archivado | HU-3, HU-33 |
| `product_variants` | `color` y `size` en lugar de `attributes jsonb`; único (`product_id`, `color`, `size`); `CHECK (stock_quantity >= 0)` | HU-4, HU-36, HU-37 |
| `product_images` | `alt_text` y `position` (1 a 3); único (`product_id`, `position`) | HU-35, HU-61 |
| `carts` | Sin `session_id`; un carrito por `user_id` | HU-13 |
| `stock_reservations` (nueva) | `cart_item_id`, `variant_id`, `quantity`, `expires_at` | HU-17, HU-18 |
| `stock_movements` (nueva) | `variant_id`, `admin_id`, `delta`, `reason`, `created_at` | HU-37 |
| `orders` | `shipping_cost`, `created_at`, `updated_at`; `status` con los 7 estados; `order_number` único; `shipping_address` como copia fija | HU-26, HU-30 |
| `order_items` | `product_name`, `color` y `size` como copia fija | HU-40 |
| `order_status_history` (nueva) | `order_id`, `from_status`, `to_status`, `changed_by` (administrador o sistema), `created_at` | HU-31, HU-42 |
| `payments` | `amount`, `provider`, `created_at`; `transaction_id` único; `payment_method` solo `debit_card` o `nequi` | HU-19 a HU-24 |
| `notification_log` (nueva) | `order_id`, `user_id`, `event`, `status`, `sent_at`; único (`order_id`, `event`) | HU-46 a HU-49 |
| `chat_usage` (nueva) | `user_id`, `period`, `message_count`; sin contenido de mensajes | HU-51 |

Un diseño es una fila de `products`; cada combinación de color y talla es una fila de `product_variants`.

### 4.2 Reglas de datos

- **Moneda**: precios en `DecimalField(max_digits=12, decimal_places=0)`.
- **Estados del pedido**: `pending_payment`, `payment_approved`, `payment_rejected`, `in_preparation`, `shipped`, `delivered`, `cancelled`.
- **Índices**: `orders (status, created_at)`, `stock_reservations (expires_at)`, `orders (user_id, created_at DESC)`, `slug` único en `products` y `categories`.
- **Integridad**: `payments.transaction_id` único; `order_items` con precio y SKU congelados; una prenda publicada tiene entre 1 y 3 imágenes, validado en el servicio de productos.
- **Supabase**: Row Level Security activado, sin políticas, en todas las tablas de `public`; Django accede con su propio rol.
- **Usuarios**: contraseñas, sesiones y roles viven en Clerk. `users` se conserva mínima porque `carts`, `orders`, `user_addresses`, `chat_usage` y `stock_movements` necesitan una clave foránea local, y el panel muestra nombre y correo sin consultar a Clerk por cada pedido.
- **Administradores**: el rol `admin` vive en Clerk (`public_metadata.role`) y se asigna solo con un comando de gestión que valida el máximo de 3.

## 5. Arquitectura del backend

Monolito modular en Django: una app por dominio, vistas delgadas y reglas de negocio en `services.py`.

### 5.1 Apps de Django

| App | Épicas | Responsabilidad |
| --- | --- | --- |
| `users` | 2 | Perfil mínimo vinculado a Clerk, dirección única y webhooks de Clerk |
| `catalog` | 1, 7 | Categorías, productos, variantes e imágenes |
| `inventory` | 3.2, 7.2 | Stock, movimientos y reservas de 15 minutos |
| `cart` | 3 | Carrito e ítems |
| `orders` | 4, 6, 8 | Pedidos, ítems con precio congelado, historial de estados y cancelaciones |
| `payments` | 4 | Adaptador de Wompi, pagos y webhooks |
| `shipping` | 5 | Zonas de cobertura, tarifa y envíos |
| `notifications` | 9 | Plantillas, envío y registro de correos |
| `chatbot` | 10 | Orquestación con Gemini, herramientas y límite de uso |
| `core` | 11, 12 | Errores comunes, configuración pública y endpoint de tareas programadas |

Las épicas 11 y 12 viven en el frontend.

### 5.2 Capas por app

- `models.py`: entidades y restricciones.
- `selectors.py`: consultas de lectura.
- `services.py`: casos de uso con `transaction.atomic()`; único lugar donde cambian el stock, el estado de pedidos y los pagos.
- `serializers.py` y `views.py`: validación de entrada y respuesta HTTP.
- `management/commands/`: `run_scheduled_tasks` y asignación del rol de administrador.
- `tests/`: pruebas por servicio y por endpoint.

### 5.3 API REST

Base `/api/v1/`. Los errores responden `{code, message, fields}` sin detalles técnicos.

| Recurso | Endpoints | Acceso |
| --- | --- | --- |
| Sesión y dirección | `GET /me`, `GET/PUT /me/address` | Autenticado |
| Catálogo | `GET /categories`, `GET /products`, `GET /products/{slug}` | Público |
| Carrito | `GET/POST /cart/items`, `PATCH/DELETE /cart/items/{id}` | Cliente |
| Checkout | `GET /shipping/quote`, `POST /checkout` | Cliente |
| Pagos | `POST /payments`, `POST /webhooks/payments/wompi` | Cliente y Wompi |
| Pedidos | `GET /orders`, `GET /orders/{n}`, `POST /orders/{n}/cancel` | Cliente |
| Chatbot | `POST /chat/messages` | Cliente |
| Administración | `/admin/products`, `/admin/variants`, `/admin/stock`, `/admin/orders`, `/admin/orders/{n}/status` | Administrador |
| Webhooks de Clerk | `POST /webhooks/clerk` | Clerk (firma Svix) |
| Tareas programadas | `POST /internal/run-scheduled-tasks` | `pg_cron` (encabezado `X-Cron-Secret`) |

### 5.4 Autenticación y roles

- Clerk gestiona registro, verificación de correo, inicio de sesión, recuperación de contraseña y roles.
- El catálogo y la ficha de producto son públicos; el carrito y el resto de endpoints exigen el token de sesión de Clerk en `Authorization: Bearer`, validado por una clase de autenticación de DRF con `clerk-backend-api`.
- El token incluye `email` y `role` (`public_metadata.role`), definidos en la plantilla de sesión de Clerk.
- El primer request autenticado crea el registro local en `users` con `clerk_user_id`; los webhooks `user.updated` y `user.deleted` lo mantienen sincronizado y `user.created` dispara el correo de bienvenida (HU-43).
- Permisos: `IsCustomer` para clientes verificados e `IsRMAdmin` (`role=admin`) para `/admin/*`.
- El rol `admin` se asigna con un comando de gestión que valida el máximo de 3 y actualiza `public_metadata.role` en Clerk.
- Los administradores inician sesión en `/admin/ingresar` con la misma instancia de Clerk; son usuarios distintos de los clientes.

### 5.5 Reglas críticas

1. Stock disponible = `stock_quantity` menos reservas con `expires_at > now()`, calculado al leer.
2. Reservar y descontar stock usa `select_for_update()` sobre la variante dentro de una transacción.
3. `pg_cron` y `pg_net` de Supabase llaman cada minuto a `POST /api/v1/internal/run-scheduled-tasks` con el encabezado `X-Cron-Secret`. El endpoint ejecuta `run_scheduled_tasks`: borra reservas vencidas, cancela pedidos en «Pendiente de Pago» con más de 30 minutos, consulta a Wompi el estado de pedidos pendientes y reintenta correos fallidos. La frecuencia de un minuto cumple la tolerancia de ±60 segundos de HU-24 y evita que el servicio gratuito de Render se suspenda.
4. Los webhooks de pago son idempotentes: `transaction_id` único y transición solo si el pedido sigue pendiente.
5. Todo cambio de estado pasa por un único servicio que escribe `order_status_history` y registra a lo sumo un correo (HU-49).

## 6. Arquitectura del frontend

SPA organizada por funcionalidad, con estado del servidor en TanStack Query y autenticación de Clerk.

### 6.1 Estructura de `apps/frontend/src`

```text
src/
├── app/            # Router, proveedores (Clerk, Query), layouts de tienda y panel
├── features/
│   ├── catalog/    # Listado, filtro por categoría, ficha, selector de color y talla
│   ├── auth/       # Rutas de Clerk y protección por rol
│   ├── cart/       # Carrito, reserva y cronómetro de 15 minutos
│   ├── checkout/   # Dirección, tarifa de envío, pago, resultado
│   ├── orders/     # Lista, detalle e historial de estados
│   ├── chatbot/    # Panel de chat
│   ├── legal/      # Datos personales, términos, garantías
│   └── admin/      # products/, inventory/, orders/ (carga diferida)
├── shared/
│   ├── ui/         # Botón, campo, diálogo, selector (accesibles)
│   ├── api/        # Cliente HTTP con el token de Clerk
│   └── lib/        # Formato COP, validaciones, utilidades
└── main.tsx
```

### 6.2 Rutas

| Zona | Rutas | Protección |
| --- | --- | --- |
| Pública | `/`, `/categoria/:slug`, `/producto/:slug`, `/terminos`, `/datos-personales`, `/garantias`, `/ingresar`, `/registro` | Ninguna |
| Cliente | `/carrito`, `/checkout`, `/pedidos`, `/pedidos/:numero` | Sesión de Clerk con correo verificado |
| Administrador | `/admin/ingresar`, `/admin/productos`, `/admin/inventario`, `/admin/pedidos` | Rol `admin`; carga diferida |

### 6.3 Tecnologías por responsabilidad

- **Autenticación**: `@clerk/react` con `<ClerkProvider>`, `<SignIn />` y `<SignUp />`; textos en español con `@clerk/localizations`; `useAuth().getToken()` entrega el token que se envía a la API. Sin sesión, agregar una prenda o abrir el carrito abre el inicio de sesión de Clerk y, al terminar, se completa la acción pendiente.
- **Estado del servidor**: TanStack Query.
- **Formularios**: React Hook Form con Zod para dirección, checkout y panel; errores asociados al campo con `aria-describedby` y `aria-live`.
- **Componentes**: Radix UI y Tailwind CSS 4, con tokens de color de contraste 4.5:1.
- **Cliente HTTP**: `fetch` con un wrapper que agrega el token y normaliza errores.
- **Rendimiento**: listado en una sola llamada; imágenes WebP con `width`, `height` y `loading="lazy"`; panel de administración con carga diferida.
- **Texto alternativo**: el componente de imagen exige `alt`; por defecto usa el nombre del producto.
- **Vercel**: `vercel.json` reescribe todas las rutas a `index.html`; variables `VITE_API_URL` y `VITE_CLERK_PUBLISHABLE_KEY`.

## 7. Integraciones externas

| Integración | Servicio | Historias |
| --- | --- | --- |
| Autenticación | Clerk | HU-7 a HU-12, HU-44, HU-45 |
| Pagos | Wompi | HU-19 a HU-24 |
| Correo transaccional | Resend con `django-anymail` | HU-43, HU-46 a HU-49 |
| Chatbot | API de Gemini con llamadas a funciones | HU-50 a HU-54 |
| Imágenes | Supabase Storage | HU-35, HU-61 |

### 7.1 Clerk

- Clerk envía los correos de verificación y de recuperación de contraseña (HU-44, HU-45).
- La verificación de correo es obligatoria al registrarse.
- Webhooks `user.created`, `user.updated` y `user.deleted`, firmados con Svix, hacia `POST /api/v1/webhooks/clerk`.
- Reglas de contraseña, bloqueo por intentos y vigencia de enlaces (P-2, P-3) se definen en la configuración de Clerk.

### 7.2 Pagos

- Interfaz propia `PaymentGateway` con cuatro operaciones: crear transacción, consultar estado, verificar firma del webhook y traducir el estado de Wompi al del pedido.
- El pago se hace en el widget de Wompi; RM Shop no recibe datos de tarjeta.
- El resultado llega por webhook con verificación de firma e idempotencia; si no llega, la tarea programada consulta el estado de los pedidos pendientes.
- Un rechazo cancela el pedido; reintentar crea un pedido nuevo (HU-23).
- Por verificar con Wompi: restringir el pago a tarjeta débito (HU-19). Su [documentación](https://docs.wompi.co/en/docs/colombia/metodos-de-pago/) lista Nequi como método propio, pero no muestra una opción para aceptar solo débito.

### 7.3 Correo

- El envío ocurre al confirmarse la transacción (`transaction.on_commit`); si falla, queda en `notification_log` con estado `failed` y la tarea programada lo reintenta.
- `notification_log` único por (`order_id`, `event`) evita correos duplicados (HU-49).
- El dominio del remitente lleva SPF, DKIM y DMARC.

### 7.4 Chatbot

API de Gemini con el SDK `google-genai`, modelo Flash configurable con `GEMINI_MODEL` y llamadas a funciones. Herramientas expuestas al modelo:

- `search_products` y `get_availability`: tallas, colores y stock reales (HU-52, HU-52b).
- `add_to_cart`, `update_cart_item` y `remove_cart_item`: mismas reglas de reserva de 15 minutos (HU-53, HU-53b).
- `prepare_checkout`: deja el carrito listo sin cobrar (HU-54).

Reglas:

- Las recomendaciones se basan en la descripción y la categoría de cada prenda (P-14).
- Las herramientas se ejecutan con la identidad del cliente autenticado; el modelo no recibe correo ni dirección.
- La conversación vive en el navegador y no se guarda (HU-50).
- El servidor solo guarda el contador de uso en `chat_usage` (HU-51); una respuesta fallida no descuenta del límite.
- Una respuesta que mencione un producto inexistente se descarta y se reemplaza por el mensaje de «no puedo responder» (HU-52b).
- Tiempo máximo de respuesta: 10 segundos.
- En la capa gratuita de Gemini el contenido enviado puede usarse para mejorar productos de Google; el modelo recibe solo datos del catálogo y el texto del mensaje.

### 7.5 Imágenes de producto

- Supabase Storage con `django-storages` (API compatible con S3); el plan gratuito incluye 1 GB.
- Cada prenda tiene entre 1 y 3 imágenes.
- El backend acepta JPG, PNG o WebP, valida tipo y peso, convierte a WebP con Pillow a calidad 85 y lado mayor de 1600 px, y guarda `alt_text`.

## 8. Docker, entornos y despliegue

### 8.1 Entorno local con Docker Compose

- **Servicios**: `db` (PostgreSQL con la misma versión mayor que Supabase), `backend` (servidor de desarrollo de Django), `frontend` (Vite en el puerto 5173) y `mailpit` (captura de correos de prueba).
- **Claves de desarrollo**: instancia de desarrollo de Clerk y claves de pruebas de Wompi y Gemini.
- **Tareas programadas**: se ejecutan a mano con `docker compose exec backend python manage.py run_scheduled_tasks`.
- **Comandos**: `docker compose up --build`, `docker compose exec backend python manage.py migrate` y `docker compose run --rm backend pytest`.

### 8.2 Imágenes

- **Backend**: `Dockerfile` multi-stage (`builder`, `dev`, `runtime`) sobre `python:3.14-slim` con parche fijado; dependencias con `uv sync --frozen`; Gunicorn como usuario sin privilegios.
- **Frontend**: `Dockerfile` multi-stage (`dev`, `build`) sobre `node:26-alpine` con parche fijado; dependencias con `pnpm install --frozen-lockfile`. Vercel construye el frontend desde el código fuente y no ejecuta esta imagen.

### 8.3 Despliegue

| Destino | Configuración |
| --- | --- |
| Backend en Render | Servicio web gratuito con `runtime: docker` y ruta de salud `/api/v1/health` |
| Tareas programadas | `cron.schedule` en Supabase con `net.http_post` a `/api/v1/internal/run-scheduled-tasks` cada minuto |
| Migraciones | Workflow de GitHub Actions al fusionar en `main`, con `python manage.py migrate` y `MIGRATIONS_DATABASE_URL` |
| Frontend en Vercel | Integración con GitHub, build con `pnpm build` y Root Directory `apps/frontend`; el plan Hobby no permite uso comercial (ver 13.1) |
| Base de datos | Supabase; copias de seguridad manuales con `pg_dump` |

Conexión a Supabase: `DATABASE_URL` apunta al Transaction Pooler (puerto 6543) con `sslmode=require`, `DISABLE_SERVER_SIDE_CURSORS = True` y `CONN_MAX_AGE = 0`. `MIGRATIONS_DATABASE_URL` usa el Session Pooler (puerto 5432), que acepta conexiones IPv4 desde GitHub Actions.

### 8.4 Variables de entorno

| Variable | Componente | Nota |
| --- | --- | --- |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` | Backend | `DEBUG=False` en producción |
| `DATABASE_URL` | Backend | Transaction Pooler, puerto 6543 |
| `MIGRATIONS_DATABASE_URL` | GitHub Actions | Session Pooler, puerto 5432 |
| `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | Backend | Dominio del frontend |
| `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET` | Backend | Verificación de tokens y de webhooks |
| `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_EVENTS_SECRET`, `WOMPI_INTEGRITY_SECRET` | Backend | Pagos |
| `RESEND_API_KEY`, `DEFAULT_FROM_EMAIL` | Backend | Correo transaccional |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Backend | Solo en el servidor |
| `SUPABASE_S3_*` | Backend | Credenciales de Storage |
| `CRON_SECRET` | Backend y `pg_cron` | Secreto del endpoint de tareas |
| `VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY` | Frontend | Públicas; sin secretos |

Los secretos viven en Render, Vercel y GitHub Actions; el repositorio solo incluye `.env.example`.

## 9. CI/CD con GitHub Actions

| Workflow | Se dispara con cambios en | Pasos |
| --- | --- | --- |
| `ci-backend.yml` | `apps/backend/**` | `uv sync --frozen`, `ruff check`, `ruff format --check`, `makemigrations --check`, `pytest` con PostgreSQL, `pip-audit`, construcción de la imagen |
| `ci-frontend.yml` | `apps/frontend/**` | `pnpm install --frozen-lockfile`, ESLint con `jsx-a11y`, `tsc --noEmit`, Vitest, `pnpm build`, `pnpm audit` |
| `migrate.yml` | Push a `main` con cambios en `apps/backend/**` | `uv sync --frozen` y `python manage.py migrate` con `MIGRATIONS_DATABASE_URL` |

- Render y Vercel despliegan al fusionar en `main`; Render solo después de que pase el CI.
- Vercel crea una vista previa por pull request.
- `main` protegida; una rama por historia (`feature/HU-17-reserva-stock`) con revisión antes de fusionar.
- Dependabot para los ecosistemas `npm` y `uv`.

## 10. Dependencias del frontend

Las versiones exactas las fija `pnpm-lock.yaml`; la tabla indica la versión mayor.

### 10.1 Producción

| Paquete | Versión | Uso |
| --- | --- | --- |
| `react`, `react-dom` | 19 | Interfaz |
| `@clerk/react` | Última | Autenticación |
| `@clerk/localizations` | Última | Textos de Clerk en español |
| `react-router` | 7 | Rutas con carga diferida del panel |
| `@tanstack/react-query` | 5 | Estado del servidor |
| `react-hook-form` | 7 | Formularios |
| `zod`, `@hookform/resolvers` | 3 o 4 | Validación de formularios |
| `tailwindcss`, `@tailwindcss/vite` | 4 | Estilos |
| `radix-ui` | 1.x | Diálogos, selectores y menús accesibles |
| `clsx`, `tailwind-merge`, `class-variance-authority` | Última | Composición de clases |
| `lucide-react` | Última | Iconos |

### 10.2 Desarrollo

| Paquete | Versión | Uso |
| --- | --- | --- |
| `vite`, `@vitejs/plugin-react` | 6 | Servidor de desarrollo y build |
| `typescript`, `@types/react`, `@types/react-dom`, `@types/node` | 5.x | Tipado estricto |
| `eslint`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y` | 9 | Código y accesibilidad |
| `prettier` | 3 | Formato |
| `vitest`, `jsdom` | Última | Pruebas unitarias y de componentes |
| `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom` | Última | Pruebas de componentes |

```bash
cd apps/frontend
pnpm add @clerk/react @clerk/localizations react-router @tanstack/react-query react-hook-form \
  zod @hookform/resolvers tailwindcss @tailwindcss/vite radix-ui clsx tailwind-merge \
  class-variance-authority lucide-react
pnpm add -D vite@6 @vitejs/plugin-react typescript @types/react @types/react-dom @types/node \
  eslint typescript-eslint eslint-plugin-react-hooks eslint-plugin-jsx-a11y prettier \
  vitest jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom
```

## 11. Dependencias del backend

Se declaran en `pyproject.toml` y se bloquean en `uv.lock`; las imágenes instalan con `uv sync --frozen`.

### 11.1 Producción

| Paquete | Versión | Uso |
| --- | --- | --- |
| `django` | `>=5.2.18,<5.3` | Framework |
| `djangorestframework` | 3.16 o superior | API REST |
| `clerk-backend-api` | Última | Validación de tokens de sesión y gestión de roles en Clerk |
| `svix` | Última | Verificación de webhooks de Clerk |
| `django-cors-headers` | 4.x | CORS entre Vercel y Render |
| `psycopg[binary]` | 3.2 o superior | Driver de PostgreSQL |
| `dj-database-url` | 3.x | Lee `DATABASE_URL` |
| `gunicorn` | Última | Servidor WSGI |
| `whitenoise` | 6.x | Archivos estáticos |
| `django-anymail[resend]` | Última | Envío de correo con Resend |
| `django-storages[s3]`, `boto3` | Última | Supabase Storage |
| `Pillow` | Última | Validación y conversión de imágenes |
| `httpx` | 0.28 o superior | Llamadas a Wompi |
| `google-genai` | Última | SDK de Gemini para el chatbot |

### 11.2 Desarrollo y pruebas

| Paquete | Uso |
| --- | --- |
| `pytest`, `pytest-django`, `pytest-cov` | Pruebas y cobertura |
| `factory-boy` | Datos de prueba |
| `freezegun` | Simula el paso de 15 y 30 minutos |
| `respx` | Simula la pasarela y el modelo de IA |
| `ruff` | Lint y formato |
| `pip-audit` | Auditoría de vulnerabilidades |

```bash
cd apps/backend
uv init --bare
uv add "django>=5.2.18,<5.3" djangorestframework clerk-backend-api svix django-cors-headers \
  "psycopg[binary]" dj-database-url gunicorn whitenoise "django-anymail[resend]" \
  "django-storages[s3]" boto3 Pillow httpx google-genai
uv add --dev pytest pytest-django pytest-cov factory-boy freezegun respx ruff pip-audit
```

`requires-python` queda en `>=3.14` y `uv.lock` se versiona. Antes de fijar versiones se confirma que `psycopg` y `Pillow` publican ruedas para Python 3.14.

## 12. Seguridad, rendimiento y requisitos no funcionales

### 12.1 Seguridad

- HTTPS en Vercel y Render; Django con `SECURE_SSL_REDIRECT`, HSTS, cookies seguras y `SECURE_PROXY_SSL_HEADER`; conexión a Supabase con `sslmode=require`.
- Contraseñas, sesiones, verificación y recuperación las gestiona Clerk.
- El backend valida firma y expiración del token de Clerk en cada petición y filtra pedidos, carrito y direcciones por el usuario autenticado.
- Los webhooks de Clerk y de Wompi se aceptan solo con firma válida; el endpoint de tareas, solo con `X-Cron-Secret`.
- Throttling de DRF en el chatbot y el checkout.
- CORS con lista explícita de orígenes y Content-Security-Policy en `vercel.json`.
- Secretos solo en variables de entorno; las claves de Gemini y las claves privadas de Wompi nunca llegan al frontend.

### 12.2 Versiones mínimas de seguridad

Estado al 1 de noviembre de 2026.

| Componente | Versión mínima | Motivo |
| --- | --- | --- |
| Node.js | 26.12.1 (24.22.1 o 22.23.4 según la línea) | Corrige CVE-2026-111497 (Brotli) y otras 9 vulnerabilidades |
| Django | 5.2.18 | Corrige los avisos de seguridad del 6 de octubre de 2026 |
| Brotli y brotlicffi (PyPI) | 1.2.1 y 1.2.1.0 | CVE-2026-111497; aplica solo si entran como dependencia transitiva |
| Python | Última 3.14.x | Número exacto por confirmar en python.org |

- Brotli se verifica con `uv tree --invert --package brotli` y `uv tree --invert --package brotlicffi`; `pip-audit` puede no marcar estos paquetes.
- Las imágenes de Docker fijan el parche de Node y Python, no solo la línea.
- Fuentes: [aviso de Node.js](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases), [aviso de Django](https://www.djangoproject.com/weblog/2026/oct/06/security-releases/) y [Debian Security Tracker](https://security-tracker.debian.org/CVE-2026-111497).

### 12.3 Rendimiento y disponibilidad

| Requisito | Resolución |
| --- | --- |
| Catálogo y ficha en 3 s o menos (HU-1, HU-3) | Una llamada para el listado, `Cache-Control` y `ETag`, imágenes WebP, SPA en el CDN de Vercel |
| Filtro por categoría en 2 s o menos (HU-2) | Filtrado en el cliente sobre el listado cargado |
| Disponibilidad de variante en 1 s o menos (HU-4) | El detalle del producto trae todas las variantes con su stock |
| Disponibilidad mensual de 99 % (HU-1) | No garantizada con Render gratuito; la llamada cada minuto de `pg_cron` reduce las suspensiones (ver 13.2) |
| Correos en 2 minutos o menos (Épica 9) | Envío tras confirmar la transacción y reintento cada minuto; el plan gratuito de Resend permite 100 al día |
| Respuesta del chatbot en 10 s o menos (HU-50) | Tiempo máximo en la llamada a Gemini y mensaje de contingencia |
| Carga de imagen en 10 s o menos (HU-35) | Subida a Storage con validación previa |

### 12.4 Observabilidad

- Registros en JSON con un identificador de petición, consultables en Render.
- Métricas mínimas en los registros: pagos aprobados y rechazados, reservas expiradas, pedidos cancelados por tiempo, correos fallidos y consumo del chatbot.

## 13. Decisiones abiertas y riesgos

### 13.1 Decisiones abiertas

| Decisión | Ref. backlog | Impacto |
| --- | --- | --- |
| Restringir el pago a tarjeta débito en Wompi | HU-19 | Configuración del checkout o validación al recibir el webhook |
| Campos finales de la dirección | P-6 | `user_addresses` y `shipping_address` del pedido |
| El cronómetro de 15 minutos se reinicia al modificar el carrito | P-5 | `expires_at` de las reservas |
| Uno o varios correos por cambio de estado | P-16 | Claves únicas de `notification_log` |
| Hosting del frontend: Vercel Hobby no permite uso comercial | n/a | Pasar a Vercel Pro o a un hosting gratuito que permita uso comercial, como Cloudflare Pages |
| Plan de producción de Render y Supabase | n/a | Los planes gratuitos suspenden el servicio (Render) o el proyecto (Supabase) por inactividad |

### 13.2 Riesgos

- **Disponibilidad**: Render gratuito se suspende tras 15 minutos sin tráfico; la llamada de cada minuto lo evita mientras Supabase responda, pero un despliegue o reinicio puede causar un arranque de hasta 1 minuto.
- **Pausa de Supabase**: el proyecto gratuito se pausa tras 7 días de inactividad y, al pausarse, se detienen también `pg_cron` y la tienda.
- **Sin copias automáticas**: el plan gratuito de Supabase no las incluye; se hacen copias manuales con `pg_dump`.
- **Resend**: al superar los 100 correos diarios el envío se pausa.
- **Gemini gratuito**: al agotar la cuota por minuto o por día, el chatbot responde con el mensaje de contingencia.
- **Dependencia de Clerk**: el inicio de sesión depende de un tercero; el catálogo es público y no depende de Clerk.
- **Pooler de Supabase**: se prueba la configuración de la sección 8.3 contra el pooler en un entorno de staging.
- **Python 3.14**: se confirman las ruedas de `psycopg` y `Pillow` al construir la primera imagen.
- **Pasarela única**: la interfaz `PaymentGateway` permite sumar otra; el pedido nunca queda en estado inconsistente (HU-21).
- **Tareas sin cola**: si el volumen crece, `run_scheduled_tasks` se migra a Celery y Redis sin cambiar los servicios, porque la lógica vive en `services.py`.
- **Reseñas**: no se crean; ninguna historia las usa.
