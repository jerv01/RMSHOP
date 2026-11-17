# Plan de Implementación: HU-18 Liberación Automática de Stock de Reservas Vencidas (Solo Backend)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la liberación automática de stock de reservas vencidas tras 15 minutos sin checkout, reflejando el estado "Tu reserva expiró" en el carrito, verificando disponibilidad al intentar pagar ítems expirados, permitiendo re-confirmación/re-reserva y garantizando resolución determinista sin sobreventas ante concurrencia límite.

**Architecture:** 
- Liberación atómica e inmediata a través del cálculo dinámico de stock disponible ($\text{stock\_quantity} - \sum \text{reservas con } \text{expires\_at} > \text{now()}$) con latencia 0.
- Exposición en `CartItemOutputSerializer` de `reservation_status` (`"active"`, `"expired"`, `"none"`) y `reservation_message` (`"Tu reserva expiró"` cuando `expires_at <= now()`).
- Servicio de dominio `release_expired_reservations` para limpieza de registros caducados y comando de administración `cleanup_expired_reservations`.
- Servicio de dominio `re_reserve_cart_item` y endpoint `POST /api/v1/cart/items/<int:item_id>/re-reserve/` para re-confirmar stock liberado si aún hay disponibilidad.
- Verificación estricta en checkout (`convert_cart_to_sale` / `convert_reservation_to_sale`): si un ítem expiró, se aborta la venta con `code="reservation_expired"`, informando el stock actual disponible (AC-HU-18-2).
- Resolución atómica con orden canónico de bloqueo `ProductVariant` -> `StockReservation` ante coincidencia en el límite de expiración (AC-HU-18-3).

**Tech Stack:** Django 5.2 LTS, Django REST Framework 3.16, PostgreSQL 17, uv, pytest-django, drf-spectacular.

**Spec:** HU-18 en `RMSHOP/docs/backlog.md`, `RMSHOP/docs/arquitectura.md`.

## Global Constraints

- Duración de la reserva: 15 minutos (`RESERVATION_DURATION_MINUTES = 15`).
- Tolerancia de liberación: el stock queda disponible para otros inmediatamente al vencer (dentro de los 60 segundos requeridos por NFR).
- Cero duplicados: un stock liberado no puede liberarse dos veces.
- Aislamiento transaccional: Bloqueo de fila `select_for_update(of=("self",))` en `ProductVariant` en todas las operaciones que evalúen o modifiquen stock.
- Formato de error API estandarizado: `{"code": "...", "message": "...", "fields": {...}}`.
- Documentación OpenAPI completa mediante `@extend_schema` (`drf-spectacular`).

## Review Focus

1. **AC-HU-18-1 (Camino feliz):** Reserva de 15 minutos sin checkout vence (`expires_at <= now()`) -> el stock queda automáticamente disponible para otros clientes (0 latencia, 0 duplicados).
2. **AC-HU-18-2 (Alternativo/Error):** Cliente intenta pagar un ítem cuya reserva ya expiró -> checkout aborta con HTTP 400 `code="reservation_expired"`, informando el stock disponible actual para verificación.
3. **AC-HU-18-3 (Caso límite de colisión checkout vs expiración):** Concurrencia exacta en el límite de expiración: checkout y liberación/reserva por otro cliente se resuelven de forma excluyente por el bloqueo de fila. Exactamente una operación prevalece y no se produce sobreventa alguna.
4. **Mensaje y estado en carrito:** Ítems vencidos retornan `reservation_status: "expired"`, `reservation_message: "Tu reserva expiró"`, `is_reservation_active: false` y `time_remaining_seconds: 0`.
5. **Re-reserva de ítem expirado:** Cliente puede re-confirmar el ítem expirado en su carrito mediante endpoint seguro si aún hay stock disponible.

---

### Tarea 1: Estado y Mensaje de Expiración en Carrito (`reservation_status`, `reservation_message`)

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/serializers.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_views.py`

**Interfaces:**
- En `CartItemOutputSerializer`:
  - `reservation_status`: `"active"` si `is_active()`, `"expired"` si existe pero venció, `"none"` si no tiene reserva.
  - `reservation_message`: `"Tu reserva expiró"` si está expirada, `None` en otro caso.
  - Documentar con `@extend_schema_field`.

- [ ] **Paso 1.1: Escribir pruebas unitarias en `test_views.py` para `reservation_status` y `reservation_message`**
- [ ] **Paso 1.2: Implementar campos en `CartItemOutputSerializer`**
- [ ] **Paso 1.3: Ejecutar pruebas y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_views.py`

---

### Tarea 2: Servicios de Dominio `release_expired_reservations` y `re_reserve_cart_item`

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/services.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_services.py`
- Crear: `RMSHOP/apps/backend/apps/cart/management/commands/cleanup_expired_reservations.py`

**Interfaces:**
- `release_expired_reservations(*, delete_cart_items: bool = False) -> int`:
  - Busca reservas con `expires_at <= timezone.now()`.
  - Bloquea y elimina registros de forma idempotente (0 duplicados).
  - Retorna cantidad de reservas liberadas/eliminadas.
- `re_reserve_cart_item(*, user: User, item_id: int) -> tuple[CartItem, StockReservation]`:
  - Bloquea `ProductVariant`.
  - Valida stock disponible. Si no hay suficiente, lanza `ApiError(code="out_of_stock")`.
  - Renueva la reserva por 15 minutos y retorna `(cart_item, reservation)`.
- Comando `cleanup_expired_reservations`:
  - Ejecuta `release_expired_reservations`.

- [ ] **Paso 2.1: Escribir pruebas unitarias en `test_services.py`**
- [ ] **Paso 2.2: Implementar servicios en `services.py` y comando Django**
- [ ] **Paso 2.3: Ejecutar pruebas de servicios y comando**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_services.py`

---

### Tarea 3: Endpoint de Re-reserva y Pruebas de Integración

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/views.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/urls.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_views.py`

**Interfaces:**
- `POST /api/v1/cart/items/<int:item_id>/re-reserve/`:
  - `CartItemReReserveView(APIView)` protegido con `IsCustomer`.
  - Llama a `re_reserve_cart_item`.
  - Retorna HTTP 200 con `CartOutputSerializer`.
  - Documentar con `@extend_schema`.

- [ ] **Paso 3.1: Escribir pruebas de vista para `POST /cart/items/<id>/re-reserve/`**
- [ ] **Paso 3.2: Implementar vista y ruta en `urls.py`**
- [ ] **Paso 3.3: Ejecutar pruebas de vistas**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_views.py`

---

### Tarea 4: Suite de Aceptación HU-18 (AC-HU-18-1, AC-HU-18-2, AC-HU-18-3)

**Archivos:**
- Crear: `RMSHOP/apps/backend/apps/cart/tests/test_hu18_acceptance.py`

**Escenarios:**
- AC-HU-18-1: Reserva de 15 minutos vence sin checkout -> stock disponible inmediatamente para otro cliente.
- AC-HU-18-2: Cliente intenta hacer checkout de ítem expirado -> aborta con `code="reservation_expired"`, informando stock actual.
- AC-HU-18-3: Coincidencia en el instante de expiración (Checkout vs Expiración/Reserva por B) -> exclusión mutua estricta, exactamente 1 prevalece y 0 sobreventas.

- [ ] **Paso 4.1: Escribir pruebas de aceptación completas en `test_hu18_acceptance.py`**
- [ ] **Paso 4.2: Ejecutar y verificar suite completa**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_hu18_acceptance.py`

---

### Tarea 5: Auditoría Crítica con Gemini 4 Argon (`--thinking-level high`)

**Archivos:**
- Scratch: `C:\Users\elkin\.gemini\antigravity\brain\c4fa1044-a0d9-4696-988e-8da85155ad22\scratch\argon_prompt_hu18.txt`

- [ ] **Paso 5.1: Compilar prompt de auditoría de HU-18**
- [ ] **Paso 5.2: Invocar Gemini 4 Argon con `--thinking-level high`**
- [ ] **Paso 5.3: Refactorizar e integrar hallazgos de inmediato**

---

### Tarea 6: Verificación Global, Linters, Documentación y Pull Request

**Archivos:**
- Modificar: `RMSHOP/docs/backlog.md`
- Modificar: `.agents/skills/index-proyecto/SKILL.md`

- [ ] **Paso 6.1: Ejecutar suite completa del backend: `docker compose exec backend pytest`**
- [ ] **Paso 6.2: Ejecutar linters y formato: `docker compose exec backend ruff check .` y `docker compose exec backend ruff format .`**
- [ ] **Paso 6.3: Actualizar `docs/backlog.md` marcando HU-18 como `[BACKEND LISTO]`**
- [ ] **Paso 6.4: Actualizar índice en `.agents/skills/index-proyecto/SKILL.md`**
- [ ] **Paso 6.5: Commits atómicos convencionales, push a `origin` en `feat/reserva_stock` y apertura del PR hacia `develop`**
