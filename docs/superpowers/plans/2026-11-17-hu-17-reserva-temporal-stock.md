# Plan de Implementación: HU-17 Reserva Temporal de Stock en el Carrito (Solo Backend)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la reserva temporal de stock por 15 minutos al agregar productos al carrito, reflejando el tiempo restante (cuenta regresiva), reduciendo el stock disponible en el catálogo público para otros clientes (0 sobreventas) y permitiendo la conversión atómica de reserva a venta en checkout.

**Architecture:** 
- Exposición en `CartItemOutputSerializer` del campo `time_remaining_seconds` calculado dinámicamente respecto a `StockReservation.expires_at`.
- Reflejo de stock disponible en catálogo público (`PublicProductVariantSerializer` y `PublicProductSerializer.in_stock`) descontando reservas activas (`expires_at > now()`) con prefetch optimizado para evitar consultas N+1.
- Bloqueo estricto `select_for_update(of=("self",))` en orden canónico para reservas concurrentes con 0 sobreventas.
- Servicio de dominio `convert_reservation_to_sale` / `convert_cart_to_sale` en `apps.cart.services` que transforma reservas vigentes en ventas descontando `stock_quantity`, registrando auditoría en `StockMovement` (HU-37) y consumiendo la reserva sin liberarla (AC-HU-17-3).

**Tech Stack:** Django 5.2 LTS, Django REST Framework 3.16, PostgreSQL 17, uv, pytest-django, drf-spectacular.

**Spec:** HU-17 en `RMSHOP/docs/backlog.md`, `RMSHOP/docs/arquitectura.md`.

## Global Constraints

- Precios y subtotales en COP como enteros sin decimales (`DecimalField(max_digits=12, decimal_places=0)`).
- Duración de la reserva: 15 minutos con tolerancia de $\pm 5$ segundos (`RESERVATION_DURATION_MINUTES = 15`).
- Cálculo de stock disponible: $\text{stock\_quantity} - \sum \text{reservas vigentes con } \text{expires\_at} > \text{now()}$.
- Bloqueo transaccional canónico `select_for_update(of=("self",))` en `ProductVariant` para prevenir deadlocks y 0 sobreventas.
- Formato de error API estandarizado: `{"code": "...", "message": "...", "fields": {...}}`.
- Documentación OpenAPI completa mediante `@extend_schema` (`drf-spectacular`).

## Review Focus

1. **AC-HU-17-1 (Camino feliz):** Variante con stock 1 agregada por Cliente A queda reservada; Cliente B en catálogo la ve con `stock_quantity: 0`, `is_available: false` y producto `in_stock: false` ("Agotado"). Al expirar o eliminarse la reserva de A, vuelve a estar disponible para B.
2. **AC-HU-17-2 (Alternativo/Error):** Con reserva vigente de A, intento de B por agregar la misma unidad es rechazado con HTTP 400 y `code="out_of_stock"`.
3. **AC-HU-17-3 (Caso límite):** Checkout pagado antes de 15 minutos convierte la reserva en venta permanente: descuenta stock físico, genera `StockMovement` y consume la reserva sin duplicados ni liberación de stock.
4. **Tiempo restante en carrito:** El carrito retorna `time_remaining_seconds` preciso ($\le 900$ y $\ge 0$), `reservation_expires_at` e `is_reservation_active`.
5. **Concurrencia extrema:** Solicitudes simultáneas de dos o más clientes para la última unidad disponible resultan en exactamente 1 éxito y las demás rechazadas con `out_of_stock` (0 sobreventas).

---

### Tarea 1: Tiempo Restante en Carrito (`time_remaining_seconds`)

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/serializers.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_views.py`

**Interfaces:**
- En `CartItemOutputSerializer`:
  - Campo `time_remaining_seconds`: entero con segundos restantes ($\le 900$, 0 si ya expiró, `null` si no hay reserva).
  - Anotación `@extend_schema_field(serializers.IntegerField(allow_null=True))`.

- [ ] **Paso 1.1: Escribir pruebas para `time_remaining_seconds` en `test_views.py`**
- [ ] **Paso 1.2: Implementar cálculo de `time_remaining_seconds` en `CartItemOutputSerializer`**
- [ ] **Paso 1.3: Ejecutar pruebas de carrito y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_views.py`

---

### Tarea 2: Reflejo de Stock Disponible en Catálogo Público (AC-HU-17-1)

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/catalog/serializers.py`
- Modificar: `RMSHOP/apps/backend/apps/catalog/views.py`
- Modificar: `RMSHOP/apps/backend/apps/catalog/tests/test_public_catalog.py`
- Crear: `RMSHOP/apps/backend/apps/cart/tests/test_hu17_acceptance.py`

**Interfaces:**
- En `apps.catalog.serializers`:
  - `PublicProductVariantSerializer`: serializador de variantes para catálogo público con `stock_quantity`, `available_quantity` e `is_available` basados en stock disponible real (descontando reservas activas).
  - `PublicProductSerializer`: utiliza `PublicProductVariantSerializer` y calcula `in_stock` basado en la disponibilidad real de variantes.
- En `apps.catalog.views._published_products_queryset`:
  - Optimizar la consulta prefetching las reservas activas o anotando variantes para evitar consultas N+1.

- [ ] **Paso 2.1: Escribir pruebas de AC-HU-17-1 en `test_public_catalog.py` y `test_hu17_acceptance.py`**
  - Variante con stock 1 reservada por Cliente A -> Cliente B consulta catálogo público y ve variante agotada (`stock_quantity=0`, `is_available=False`, `in_stock=False`).
  - Al expirar la reserva (15 minutos después) o al eliminarse del carrito, Cliente B ve la variante disponible de nuevo (`stock_quantity=1`, `is_available=True`).
- [ ] **Paso 2.2: Implementar `PublicProductVariantSerializer` y optimización en `_published_products_queryset`**
- [ ] **Paso 2.3: Ejecutar pruebas de catálogo público y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/catalog/tests/test_public_catalog.py`

---

### Tarea 3: Verificación de Concurrencia y Rechazo por Stock Agotado (AC-HU-17-2)

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_hu17_acceptance.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_services.py`

**Interfaces:**
- AC-HU-17-2: Cliente B intentando agregar variante reservada por A recibe `ApiError(code="out_of_stock")`.
- Test de concurrencia: Múltiples hilos compitiendo por la última unidad ejecutan `add_to_cart`.

- [ ] **Paso 3.1: Escribir pruebas para AC-HU-17-2 y concurrencia multi-hilo**
- [ ] **Paso 3.2: Ejecutar pruebas y verificar 0 sobreventas y rechazo consistente**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_hu17_acceptance.py`

---

### Tarea 4: Conversión de Reserva en Venta en Checkout (AC-HU-17-3 [SUPUESTO])

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/services.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_services.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_hu17_acceptance.py`

**Interfaces:**
- `convert_reservation_to_sale(*, reservation_id: int | None = None, reservation: StockReservation | None = None, admin_user: User | None = None, order_reference: str = "") -> StockMovement`
- `convert_cart_to_sale(*, cart: Cart, admin_user: User | None = None, order_reference: str = "") -> list[StockMovement]`
  - Bloquea variantes con `select_for_update(of=("self",))`.
  - Verifica vigencia (`reservation.is_active()`). Si expiró, lanza `ApiError(code="reservation_expired")`.
  - Reduce `variant.stock_quantity -= reservation.quantity`.
  - Registra `StockMovement` (HU-37) con delta negativo y motivo de venta.
  - Elimina la reserva y el ítem de carrito (la reserva no se libera al stock disponible, se consolida como venta).

- [ ] **Paso 4.1: Escribir pruebas unitarias y de integración para conversión a venta (AC-HU-17-3)**
- [ ] **Paso 4.2: Implementar `convert_reservation_to_sale` y `convert_cart_to_sale` en `apps.cart.services`**
- [ ] **Paso 4.3: Ejecutar pruebas de servicios de carrito y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_services.py`

---

### Tarea 5: Auditoría Crítica con Gemini 4 Argon (`--thinking-level high`)

**Archivos:**
- Scratch: `C:\Users\elkin\.gemini\antigravity\brain\c4fa1044-a0d9-4696-988e-8da85155ad22\scratch\argon_prompt_hu17.txt`
- Script: `C:\Users\elkin\.gemini\config\skills\argon-subagent\scripts\call_argon.py`

- [ ] **Paso 5.1: Compilar prompt de auditoría con código completo, locking, servicios y pruebas**
- [ ] **Paso 5.2: Invocar Gemini 4 Argon con `--thinking-level high`**
- [ ] **Paso 5.3: Analizar veredicto y aplicar de inmediato refactorizaciones/optimizaciones recomendadas**

---

### Tarea 6: Verificación Global, Linters, Documentación y Pull Request

**Archivos:**
- Modificar: `RMSHOP/docs/backlog.md`
- Modificar: `.agents/skills/index-proyecto/SKILL.md`

- [ ] **Paso 6.1: Ejecutar suite completa del backend: `docker compose exec backend pytest`**
- [ ] **Paso 6.2: Ejecutar linters y formato: `docker compose exec backend ruff check .` y `docker compose exec backend ruff format .`**
- [ ] **Paso 6.3: Actualizar `docs/backlog.md` marcando HU-17 como `[BACKEND LISTO]`**
- [ ] **Paso 6.4: Actualizar índice en `.agents/skills/index-proyecto/SKILL.md`**
- [ ] **Paso 6.5: Commits atómicos convencionales, push a `origin` y creación del PR hacia `develop`**
