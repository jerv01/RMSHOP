# Plan de Implementación: HU-19, HU-20 y HU-21 Pagos con MercadoPago (Solo Backend)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend el pago de un pedido con tarjeta débito (HU-19) o PSE (HU-20) a través de la Orders API de MercadoPago, y mantener el pedido en estado "Pendiente de Pago" con el stock retenido mientras se espera la respuesta de la pasarela (HU-21), sin cobros duplicados y con un estado consistente si la pasarela falla.

**Architecture:**
- App `shipping` mínima y provisional con `ShippingZone` y la regla de cobertura por municipio.
- App `orders` con `Order`, `OrderItem` y `OrderStatusHistory`. Todo cambio de estado pasa por `change_order_status` (mapa de transiciones y escritura de historial). El pedido se crea desde el carrito con `create_order_from_cart`, que convierte las reservas en venta (`convert_cart_to_sale`) para retener el stock.
- App `payments` con el modelo `Payment` (clave de idempotencia y restricción única parcial de un pago activo por pedido), el adaptador `MercadoPagoGateway` sobre `httpx` y los servicios `start_payment`, `sync_payment` y `apply_mp_order`. El webhook queda para HU-22.
- Endpoints DRF protegidos con `IsCustomer`, con `ScopedRateThrottle` en checkout y pagos.

**Tech Stack:** Django 5.2 LTS, Django REST Framework 3.16, PostgreSQL 17, uv, httpx, pytest-django, respx, drf-spectacular.

**Spec:** HU-19, HU-20 y HU-21 en `RMSHOP/docs/backlog.md`, `RMSHOP/docs/arquitectura.md` (secciones de pagos, pedidos y endpoints) y el plan aprobado de la rama `feat/payments`.

## Decisiones

- **MercadoPago Orders API reemplaza a Wompi (P-9):** la pasarela queda definida como MercadoPago (Checkout API, Colombia) detrás de un adaptador propio en `apps/payments/gateways/mercadopago.py`.
- **HU-20 cambia de Nequi a PSE:** la Orders API de MercadoPago para Colombia no ofrece Nequi; solo `visa`, `master`, `debvisa`, `debmaster`, `pse` y `efecty`.
- **Retención de stock:** al crear el pedido, las reservas del carrito se convierten en venta (`convert_cart_to_sale`, que descuenta stock y registra `StockMovement`). Si el pago se rechaza o el pedido se cancela, el stock se devuelve exactamente una vez con `adjust_variant_stock`; la garantía viene de la transición de estado con el pedido bloqueado (`select_for_update`).
- **Checkout provisional:** no existe una HU de checkout y HU-25/HU-26 no están hechas; por eso se implementa un checkout mínimo (municipio, dirección, destinatario y teléfono) con tarifas fijas de la arquitectura: Cali 5.000; Palmira, Jamundí y Yumbo 10.000 COP.
- **Solo tarjeta débito:** el backend acepta únicamente `payment_method_id` en `{debvisa, debmaster}` con tipo `debit_card`; cualquier otro caso se rechaza antes de llamar a MercadoPago.
- **Frontend con Card Payment Brick:** el Brick (`@mercadopago/sdk-react`) tokeniza la tarjeta en el navegador, así que el backend solo recibe el token y nunca datos de tarjeta.

## Global Constraints

- Precios, subtotales, tarifas y montos en COP como enteros sin decimales (`DecimalField(max_digits=12, decimal_places=0)`); a MercadoPago se envían como string sin decimales.
- Servicios de dominio con `@transaction.atomic` y argumentos keyword-only; errores con `ApiError` y formato unificado `{"code": "...", "message": "...", "fields": {...}}`.
- Un solo punto de cambio de estado del pedido: `change_order_status`, con mapa de transiciones permitidas e historial en `OrderStatusHistory`.
- Idempotencia: cada `Payment` guarda un `idempotency_key` (UUID4) enviado como `X-Idempotency-Key`; una `UniqueConstraint` condicional permite un solo pago activo (`initiated`, `processing`, `action_required`, `approved`) por pedido.
- El token de tarjeta nunca se persiste ni se loguea; `raw_response` se guarda sin `token` ni `client_token`. El access token de MercadoPago vive solo en el backend; si falta, las rutas de pago responden 503.
- Timeout hacia MercadoPago de 4 s (`MERCADOPAGO_TIMEOUT_SECONDS`) para cumplir el RNF de 5 s. Timeout, 429 o 5xx se traducen a 503 `payment_gateway_unavailable`.
- Los pedidos solo son visibles para su dueño; el pedido de otro usuario responde 404.
- Throttling por alcance: `checkout` y `payments` a 10/min (`DEFAULT_THROTTLE_RATES`).
- Documentación OpenAPI completa mediante `@extend_schema` (`drf-spectacular`).
- Tareas ejecutadas en orden, nunca en paralelo, porque comparten `config/settings/base.py` y `config/urls.py`.

## Review Focus

1. **AC-HU-19-1 (Camino feliz):** pago con débito aprobado por MercadoPago (`processed`) deja el pedido en "Pago aprobado", con la transición registrada en el historial.
2. **AC-HU-19-2 (Alternativo/Error):** tarjeta de crédito, `visa`/`master` o tipo distinto de `debit_card` se rechaza con 400 `only_debit_allowed` y mensaje "Solo se aceptan tarjetas débito", sin llamar a MercadoPago (verificado con respx).
3. **AC-HU-19-3 (Caso límite):** si el cliente abandona sin completar el pago, el pedido permanece "Pendiente de Pago" (la cancelación a los 30 minutos es HU-24).
4. **AC-HU-20-1 (Camino feliz):** PSE devuelve `redirect_url` del banco con el pedido todavía pendiente; al volver, `POST /orders/{n}/payments/sync` con `processed` deja "Pago aprobado".
5. **AC-HU-20-2 (Alternativo/Error):** pago PSE (o tarjeta, incluida la respuesta HTTP 402) rechazado deja el pedido "Pago rechazado" y luego "Cancelado", con el stock devuelto exactamente una vez aunque `sync` se llame dos veces.
6. **AC-HU-20-3 (Caso límite):** el pago PSE se crea con `expiration_time` igual a los minutos restantes de `payment_expires_at` (30 al crear), coherente con HU-24; un pedido vencido responde 409 `payment_window_expired`.
7. **AC-HU-21-1 (Camino feliz):** `GET /orders/{n}` muestra `status="pending_payment"` y `status_label="Pendiente de Pago"` como texto, tanto antes de pagar como con PSE en `action_required`.
8. **AC-HU-21-2 (Alternativo/Error):** MercadoPago con timeout o 500 devuelve 503 `payment_gateway_unavailable`, el `Payment` queda en `error`, el pedido sigue "Pendiente de Pago" y un reintento posterior funciona.
9. **AC-HU-21-3 (Caso límite):** un segundo `POST payments` con un pago activo devuelve 409 `payment_already_in_progress` y MercadoPago se llama una sola vez (restricción única parcial más bloqueo del pedido).
10. **Transversales:** checkout con carrito vacío, municipio no cubierto o reserva expirada (con rollback total); totales = subtotal + envío; pedido de otro usuario responde 404; el token nunca aparece en `raw_response`.

---

### Tarea 1: App `shipping` (ShippingZone, seed y `get_zone_for_municipality`)

**Archivos:**
- Crear: `RMSHOP/apps/backend/apps/shipping/apps.py`
- Crear: `RMSHOP/apps/backend/apps/shipping/models.py`
- Crear: `RMSHOP/apps/backend/apps/shipping/services.py`
- Crear: `RMSHOP/apps/backend/apps/shipping/migrations/0001_initial.py`
- Crear: `RMSHOP/apps/backend/apps/shipping/migrations/0002_seed_zones.py`
- Modificar: `RMSHOP/apps/backend/config/settings/base.py` (agregar `"apps.shipping"` a `INSTALLED_APPS`)
- Test: `RMSHOP/apps/backend/apps/shipping/tests/test_services.py`

**Interfaces:**
- Consume: `apps.core.exceptions.ApiError`
- Produce:
  - Modelo `ShippingZone(municipality unique, fee Decimal(12,0), is_active, created_at, updated_at)` en la tabla `shipping_zones`.
  - `normalize_municipality(name: str) -> str` (sin espacios extra, minúsculas y sin tildes).
  - `get_zone_for_municipality(*, municipality: str) -> ShippingZone`; lanza `ApiError(code="municipality_not_covered")` con el mensaje "Solo enviamos a Cali, Palmira, Jamundí y Yumbo." si no hay zona activa que coincida.

- [x] **Paso 1.1: Escribir pruebas unitarias en `test_services.py`**
  - La data migration siembra los 4 municipios con sus tarifas (Cali 5.000; Palmira, Jamundí y Yumbo 10.000).
  - `normalize_municipality` ignora mayúsculas, tildes y espacios sobrantes.
  - `get_zone_for_municipality` encuentra la zona sin importar mayúsculas, tildes o espacios y devuelve la tarifa.
  - Un municipio fuera de cobertura, vacío o con la zona inactiva lanza `municipality_not_covered`.
- [x] **Paso 1.2: Ejecutar pruebas para verificar que fallen**
  - Comando: `docker compose exec backend pytest apps/shipping`
  - Esperado: FAIL (módulo `apps.shipping` no existe).
- [x] **Paso 1.3: Implementar `apps.py`, `models.py`, `services.py` y registrar en `INSTALLED_APPS`**
- [x] **Paso 1.4: Generar la migración inicial y la data migration de zonas**
  - Comando: `docker compose exec backend python manage.py makemigrations shipping`
  - Comando: `docker compose exec backend python manage.py makemigrations shipping --empty --name seed_zones` (con `RunPython` de siembra y reversa)
  - Comando: `docker compose exec backend python manage.py migrate`
- [x] **Paso 1.5: Ejecutar pruebas para verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/shipping`
  - Esperado: PASS.
- [x] **Paso 1.6: Revisar el diff, ejecutar linter**
  - Comando: `docker compose exec backend ruff check apps/shipping`

---

### Tarea 2: App `orders` (modelos, estados, creación desde el carrito, cancelación y endpoints)

**Archivos:**
- Crear: `RMSHOP/apps/backend/apps/orders/apps.py`
- Crear: `RMSHOP/apps/backend/apps/orders/models.py`
- Crear: `RMSHOP/apps/backend/apps/orders/services.py`
- Crear: `RMSHOP/apps/backend/apps/orders/serializers.py`
- Crear: `RMSHOP/apps/backend/apps/orders/views.py`
- Crear: `RMSHOP/apps/backend/apps/orders/urls.py`
- Crear: `RMSHOP/apps/backend/apps/orders/migrations/0001_initial.py`
- Modificar: `RMSHOP/apps/backend/config/settings/base.py` (agregar `"apps.orders"` a `INSTALLED_APPS` y `DEFAULT_THROTTLE_RATES` con `checkout`)
- Modificar: `RMSHOP/apps/backend/config/urls.py` (incluir `apps.orders.urls`)
- Test: `RMSHOP/apps/backend/apps/orders/tests/conftest.py`
- Test: `RMSHOP/apps/backend/apps/orders/tests/test_services.py`
- Test: `RMSHOP/apps/backend/apps/orders/tests/test_views.py`

**Interfaces:**
- Consume: `apps.cart.models.Cart`, `apps.cart.models.CartItem`, `apps.cart.services.convert_cart_to_sale`, `apps.inventory.services.adjust_variant_stock`, `apps.shipping.services.get_zone_for_municipality`, `apps.users.models.User`, `apps.users.permissions.IsCustomer`
- Produce:
  - Modelos `Order` (`order_number` único con formato `RM-000123`, `status`, `subtotal`, `shipping_cost`, `total`, copia fija de la dirección, `payment_expires_at`; índices `(status, created_at)` y `(user, -created_at)`), `OrderItem` (copias fijas de nombre, color, talla y precio; `variant` con `SET_NULL`; `quantity > 0`) y `OrderStatusHistory` (`from_status` vacío en la creación, `changed_by` nulo = sistema).
  - `OrderStatus` (`pending_payment`, `payment_approved`, `payment_rejected`, `in_preparation`, `shipped`, `delivered`, `cancelled`) con la etiqueta en texto de cada estado (por ejemplo "Pendiente de Pago").
  - `change_order_status(*, order: Order, to_status: str, changed_by: User | None = None, note: str = "") -> Order`; lanza `ApiError(code="invalid_status_transition")` si la transición no está en `ALLOWED_TRANSITIONS`.
  - `create_order_from_cart(*, user: User, municipality: str, address_line: str, recipient_name: str, phone: str) -> Order`; lanza `empty_cart`, `municipality_not_covered` o `reservation_expired` (con rollback completo).
  - `cancel_order(*, order: Order, changed_by: User | None = None, note: str = "") -> Order`; idempotente, lanza `order_not_cancellable` desde estados distintos de pendiente o rechazado.
  - `approve_order_payment(*, order: Order, note: str = "") -> Order` (idempotente).
  - `reject_order_payment(*, order: Order, note: str = "") -> Order` (deja «Pago rechazado» y luego «Cancelado», devolviendo el stock una vez; idempotente).
  - `POST /api/v1/checkout` -> 201 con el pedido. Entrada: `{"municipality", "address_line", "recipient_name", "phone"}`. Throttling con alcance `checkout`.
  - `GET /api/v1/orders` -> lista de pedidos del cliente (`order_number`, `status`, `status_label`, `total`, `created_at`).
  - `GET /api/v1/orders/{order_number}` -> detalle con `status`, `status_label`, ítems e historial de estados; 404 si el pedido es de otro usuario.

- [x] **Paso 2.1: Escribir pruebas en `test_services.py` y `test_views.py`**
  - Crear el pedido copia ítems con el precio actual, calcula `total = subtotal + envío` y retiene el stock (descuento con `StockMovement`).
  - La tarifa de envío depende del municipio; carrito vacío y municipio no cubierto se rechazan.
  - Reserva expirada revierte todo el pedido.
  - Transición inválida se rechaza; `approve_order_payment` es idempotente.
  - `cancel_order` y `reject_order_payment` devuelven el stock exactamente una vez y registran ambos estados en el historial; cancelar un pedido aprobado no se permite.
  - Endpoints: checkout crea el pedido "Pendiente de Pago", requiere autenticación, valida campos y mensaje de cobertura; AC-HU-21-1 (el cliente ve `status_label="Pendiente de Pago"`); otro cliente no puede ver el pedido (404).
- [x] **Paso 2.2: Ejecutar pruebas para verificar que fallen**
  - Comando: `docker compose exec backend pytest apps/orders`
  - Esperado: FAIL (módulo `apps.orders` no existe).
- [x] **Paso 2.3: Implementar `apps.py`, `models.py`, registrar en `INSTALLED_APPS` y generar migraciones**
  - Comando: `docker compose exec backend python manage.py makemigrations orders`
  - Comando: `docker compose exec backend python manage.py migrate`
- [x] **Paso 2.4: Implementar `services.py` (`change_order_status`, `create_order_from_cart`, `cancel_order`, `approve_order_payment`, `reject_order_payment`)**
  - Pedido bloqueado con `select_for_update(of=("self",))` en cada cambio de estado; variantes ordenadas por `variant_id` al devolver stock.
- [x] **Paso 2.5: Implementar `serializers.py`, `views.py`, `urls.py`, actualizar `config/urls.py` y `DEFAULT_THROTTLE_RATES`**
- [x] **Paso 2.6: Ejecutar pruebas para verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/orders`
  - Esperado: PASS.
- [x] **Paso 2.7: Ejecutar la suite completa y el linter**
  - Comando: `docker compose exec backend pytest`
  - Comando: `docker compose exec backend ruff check .`

---

### Tarea 3: App `payments` (modelo, adaptador MercadoPago, servicios y endpoints)

**Archivos:**
- Crear: `RMSHOP/apps/backend/apps/payments/apps.py`
- Crear: `RMSHOP/apps/backend/apps/payments/models.py`
- Crear: `RMSHOP/apps/backend/apps/payments/exceptions.py`
- Crear: `RMSHOP/apps/backend/apps/payments/gateways/__init__.py`
- Crear: `RMSHOP/apps/backend/apps/payments/gateways/mercadopago.py`
- Crear: `RMSHOP/apps/backend/apps/payments/services.py`
- Crear: `RMSHOP/apps/backend/apps/payments/serializers.py`
- Crear: `RMSHOP/apps/backend/apps/payments/views.py`
- Crear: `RMSHOP/apps/backend/apps/payments/urls.py`
- Crear: `RMSHOP/apps/backend/apps/payments/migrations/0001_initial.py`
- Modificar: `RMSHOP/apps/backend/config/settings/base.py` (agregar `"apps.payments"` a `INSTALLED_APPS` y el alcance `payments` en `DEFAULT_THROTTLE_RATES`)
- Modificar: `RMSHOP/apps/backend/config/urls.py` (incluir `apps.payments.urls`)
- Test: `RMSHOP/apps/backend/apps/payments/tests/conftest.py`
- Test: `RMSHOP/apps/backend/apps/payments/tests/test_payments.py`

**Interfaces:**
- Consume: `apps.orders.models.Order`, `apps.orders.services.approve_order_payment`, `apps.orders.services.reject_order_payment`, `apps.orders.views.get_customer_order`, `apps.users.permissions.IsCustomer`, `httpx`
- Produce:
  - Modelo `Payment` (`order` FK, `provider="mercadopago"`, `method` en `debit_card`|`pse`, `amount`, `status` en `initiated`/`processing`/`action_required`/`approved`/`rejected`/`error`, `status_detail`, `mp_order_id` y `mp_payment_id` únicos y nulos, `idempotency_key` UUID único, `redirect_url`, `raw_response` JSON saneado) con `UniqueConstraint(fields=["order"], condition=Q(status__in=ACTIVE_PAYMENT_STATUSES), name="uniq_active_payment_per_order")`.
  - Excepciones: `PaymentGatewayNotConfigured` (503 `payment_gateway_not_configured`), `PaymentGatewayUnavailable` (503 `payment_gateway_unavailable`), `PaymentRequestRejected` (400 `payment_request_invalid`), `PaymentAlreadyInProgress` (409 `payment_already_in_progress`) y `OrderNotPayable` (409 `order_not_payable`, también `payment_window_expired`).
  - `MercadoPagoGateway(*, access_token=None, base_url=None, timeout=None)` con:
    - `create_order(*, payload: dict, idempotency_key: str) -> dict` (`POST /v1/orders`; la respuesta 402 se normaliza como orden `failed`).
    - `get_order(*, mp_order_id: str) -> dict` (`GET /v1/orders/{id}`).
    - `list_pse_banks() -> list[dict]` (`GET /v1/payment_methods`, filtra `pse.financial_institutions`).
  - `map_mp_status(mp_order: dict) -> MpStatus` (`processed` -> aprobado; `failed`/`canceled`/`cancelled`/`expired` -> rechazado; `action_required` -> acción del cliente; el resto -> en proceso).
  - `apply_mp_order(*, payment: Payment, mp_order: dict) -> Payment` (idempotente; guarda `raw_response` sin tokens).
  - `start_payment(*, user: User, order_number: str, method: str, data: dict, payer_email: str, ip_address: str | None = None) -> Payment`.
  - `sync_payment(*, user: User, order_number: str) -> Order`.
  - `list_pse_banks() -> list[dict]` (caché de una hora).
  - `POST /api/v1/orders/{n}/payments` -> 201 con `{"order": ..., "payment": {...}}`. Entrada: `method` (`debit_card` o `pse`) más `token`, `payment_method_id` y `payment_type` para tarjeta, o banco y datos del pagador para PSE.
  - `POST /api/v1/orders/{n}/payments/sync` -> 200 con el pedido y el pago actualizados.
  - `GET /api/v1/payments/pse-banks` -> lista de `{id, description}`.

- [x] **Paso 3.1: Escribir pruebas en `test_payments.py` (respx para MercadoPago, `force_authenticate`)**
  - AC-HU-19-1: débito aprobado (`processed/accredited`) deja el pedido "Pago aprobado" con historial.
  - AC-HU-19-2: `master`, `visa` o `credit_card` devuelve 400 `only_debit_allowed` sin llamar a MercadoPago.
  - AC-HU-19-3: pago sin terminar deja el pedido "Pendiente de Pago"; el token es obligatorio.
  - AC-HU-20-1: PSE devuelve `redirect_url` y luego `sync` con `processed` aprueba; PSE exige banco y datos del pagador.
  - AC-HU-20-2: rechazo (`failed` o HTTP 402) deja "Pago rechazado" y luego "Cancelado"; el stock vuelve una sola vez aunque `sync` se llame dos veces.
  - AC-HU-21-2: timeout o 500 devuelve 503, el `Payment` queda en `error`, el pedido sigue pendiente y un reintento funciona.
  - AC-HU-21-3: un segundo `POST payments` con pago activo devuelve 409 y MercadoPago se llama una sola vez.
  - Otros: pedido aprobado no se puede pagar de nuevo; ventana de pago vencida (`payment_window_expired`); solicitud inválida a la pasarela (`payment_request_invalid`); sin `MERCADOPAGO_ACCESS_TOKEN` responde 503; otro cliente no puede pagar ni sincronizar (404); una aprobación tardía no reactiva un pedido cancelado; bancos PSE listados y cacheados; `map_mp_status` parametrizado y `sanitize_mp_response` quita tokens a cualquier profundidad.
- [x] **Paso 3.2: Ejecutar pruebas para verificar que fallen**
  - Comando: `docker compose exec backend pytest apps/payments`
  - Esperado: FAIL (módulo `apps.payments` no existe).
- [x] **Paso 3.3: Implementar `models.py`, registrar en `INSTALLED_APPS` y generar migraciones**
  - Comando: `docker compose exec backend python manage.py makemigrations payments`
  - Comando: `docker compose exec backend python manage.py migrate`
- [x] **Paso 3.4: Implementar `exceptions.py` y el adaptador `gateways/mercadopago.py` con httpx**
  - Errores de red, 429 y 5xx se convierten en `PaymentGatewayUnavailable`; los 4xx de MercadoPago en `PaymentRequestRejected` sin exponer el cuerpo sensible; la respuesta 402 de `create_order` se procesa como rechazo.
- [x] **Paso 3.5: Implementar `services.py` (`map_mp_status`, `apply_mp_order`, `start_payment`, `sync_payment`, `list_pse_banks`)**
  - `start_payment` registra el intento con el pedido bloqueado, llama a MercadoPago fuera del bloqueo y marca el pago como `error` si la pasarela falla.
  - Payload común: `type=online`, `processing_mode=automatic`, `total_amount` como string sin decimales, `external_reference=order_number` y `payer.email` desde los claims de Clerk.
  - PSE: `expiration_time="PT{minutos}M"` y `callback_url = FRONTEND_BASE_URL/pedidos/{n}`.
- [x] **Paso 3.6: Implementar `serializers.py`, `views.py`, `urls.py` y actualizar `config/urls.py`**
- [x] **Paso 3.7: Ejecutar pruebas para verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/payments`
  - Esperado: PASS.

---

### Tarea 4: Settings, variables de entorno y dependencia (httpx)

**Archivos:**
- Modificar: `RMSHOP/apps/backend/config/settings/base.py`
- Modificar: `RMSHOP/apps/backend/.env.example`
- Modificar: `RMSHOP/apps/backend/pyproject.toml`
- Modificar: `RMSHOP/apps/backend/uv.lock`

**Interfaces:**
- Produce:
  - Settings `MERCADOPAGO_ACCESS_TOKEN` (por defecto vacío), `MERCADOPAGO_API_BASE_URL` (por defecto `https://api.mercadopago.com`) y `MERCADOPAGO_TIMEOUT_SECONDS` (por defecto `4`).
  - `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"checkout": "10/min", "payments": "10/min"}`.
  - Dependencia directa `httpx>=0.28.1`.

- [x] **Paso 4.1: Agregar `httpx` como dependencia directa**
  - Comando: `cd apps/backend && uv add httpx`
- [x] **Paso 4.2: Agregar los settings de MercadoPago y los límites de throttling en `base.py`**
- [x] **Paso 4.3: Documentar las variables en `.env.example`**
  - Nota: para el sandbox se usan credenciales de producción de un usuario de prueba, porque la Orders API no acepta credenciales `TEST-`.
- [x] **Paso 4.4: Verificar que las migraciones estén al día**
  - Comando: `docker compose exec backend python manage.py makemigrations --check`
  - Esperado: sin cambios pendientes.

---

### Tarea 5: Documentación (`arquitectura.md` y `backlog.md`)

**Archivos:**
- Modificar: `RMSHOP/docs/arquitectura.md`
- Modificar: `RMSHOP/docs/backlog.md`

**Interfaces:**
- Produce: documentación coherente con MercadoPago y PSE en lugar de Wompi y Nequi.

- [x] **Paso 5.1: Actualizar `docs/arquitectura.md`**
  - Cambiar Wompi por MercadoPago (Orders API) en resumen, stack, costos, endpoints, variables de entorno y modelo `payments` (`debit_card` o `pse`).
  - Documentar los endpoints de checkout, pedidos y pagos, la idempotencia, el mapeo de estados, la retención de stock y los pendientes (webhook HU-22, cancelación automática HU-24, 3DS).
  - Agregar la nota de que PSE redirige al banco, algo propio de PSE, y la nota del sandbox con usuarios de prueba.
- [x] **Paso 5.2: Actualizar `docs/backlog.md`**
  - HU-20 pasa de Nequi a PSE (visión del producto, descripción, reglas y criterios AC-HU-20-1..3).
  - Dejar P-9 resuelta como MercadoPago en HU-19 y HU-20, y aclarar que el checkout es provisional.
  - Marcar HU-19, HU-20 y HU-21 como `[BACKEND LISTO]`.

---

### Tarea 6: Verificación Integral y Cierre

**Archivos:**
- Modificar: `RMSHOP/docs/backlog.md` (marca `[BACKEND LISTO]`, ya aplicada en la Tarea 5)

- [x] **Paso 6.1: Ejecutar suite completa de backend**
  - Comando: `docker compose exec backend pytest` (debe pasar el 100% de los tests).
- [x] **Paso 6.2: Ejecutar linter y formatter**
  - Comando: `docker compose exec backend ruff check .`
  - Comando: `docker compose exec backend ruff format --check .`
- [x] **Paso 6.3: Verificar que no falten migraciones**
  - Comando: `docker compose exec backend python manage.py makemigrations --check`
- [x] **Paso 6.4: Confirmar en `docs/backlog.md` que HU-19, HU-20 y HU-21 están como `[BACKEND LISTO]`**
- [ ] **Paso 6.5: Prueba manual en el sandbox de MercadoPago con Swagger (`/api/v1/docs/`)**
  - Pendiente: requiere credenciales de MercadoPago; los tests automáticos simulan la API con respx.
  - Usar credenciales de producción de usuarios de prueba de MercadoPago. Recorrido: carrito, checkout, pago débito (token del Brick o tarjeta de prueba) y pedido aprobado; PSE, `redirect_url` y `sync`.
- [ ] **Paso 6.6: Commits atómicos convencionales, push a `origin` y creación del PR**
  - Pendiente: todavía no se ha hecho ningún commit; se hará solo cuando se solicite.

---

## Fuera de alcance

- Webhook firmado de MercadoPago (`POST /webhooks/payments/mercadopago`): HU-22. Mientras tanto, el estado de PSE se consulta con `POST /orders/{n}/payments/sync`.
- Cancelación automática a los 30 minutos y endpoint de tareas programadas (`run-scheduled-tasks`): HU-24.
- Correos transaccionales de pedido y pago: HU-49.
- Frontend de checkout y de pago (Card Payment Brick, selector de banco PSE, vista `/pedidos/{n}`).
- 3DS: se difiere; la validación 3DS queda pendiente.

## Notas para frontend

- **Card Payment Brick:** configurarlo solo para débito (sin crédito). La variable pública es `VITE_MERCADOPAGO_PUBLIC_KEY`.
- **Tarjeta débito:** enviar `token`, `payment_method_id` (`debvisa` o `debmaster`) y `payment_type` (`debit_card`) del Brick a `POST /api/v1/orders/{n}/payments` con `method=debit_card`. El número de tarjeta nunca debe pasar por el backend.
- **PSE:**
  1. Listar los bancos con `GET /api/v1/payments/pse-banks` (`id` y `description`).
  2. Enviar `POST /api/v1/orders/{n}/payments` con `method=pse`, `financial_institution` y los datos del pagador (`entity_type`, `identification_type`, `identification_number`, `phone_area_code`, `phone_number`, `zip_code`, `street_number`, `neighborhood`).
  3. Redirigir al cliente a `payment.redirect_url`.
  4. Cuando el cliente vuelva a `/pedidos/{n}`, llamar a `POST /api/v1/orders/{n}/payments/sync` y mostrar el estado resultante.
- **Estado del pedido:** mostrar `status_label` como texto (por ejemplo "Pendiente de Pago"), no solo con color.
- **Códigos de error** (formato `{code, message, fields}`):
  - `only_debit_allowed` (400): tarjeta que no es débito Visa o Mastercard; mostrar el mensaje.
  - `payment_already_in_progress` (409): ya hay un pago activo; si trae `fields.redirect_url`, redirigir al banco para continuar.
  - `order_not_payable` (409): el pedido ya no está pendiente de pago.
  - `payment_window_expired` (409): terminó el tiempo para pagar; hacer el pedido de nuevo.
  - `payment_gateway_unavailable` (503): MercadoPago no respondió; el pedido sigue pendiente y se puede reintentar.
  - `payment_request_invalid` (400): MercadoPago rechazó los datos enviados; pedir revisarlos.
  - `municipality_not_covered` (400): solo se envía a Cali, Palmira, Jamundí y Yumbo.
  - `empty_cart` (400): el carrito está vacío.
  - `reservation_expired` (400): alguna reserva del carrito venció; volver al carrito.
- **Sandbox de MercadoPago:** usar usuarios de prueba con credenciales de producción; la Orders API rechaza las credenciales `TEST-` con `invalid_credentials`.
