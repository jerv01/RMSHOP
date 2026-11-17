# Plan de Implementación: HU-13 Agregar Variante al Carrito (Solo Backend)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la funcionalidad de agregar una variante de producto al carrito para un cliente registrado, reservando stock por 15 minutos atómicamente y garantizando privacidad y consistencia ante condiciones de carrera.

**Architecture:** App Django REST Framework `apps.cart` con modelos `Cart`, `CartItem` y `StockReservation` (HU-17). Servicio de dominio `add_to_cart` con `select_for_update()` dentro de `transaction.atomic()` para validación de disponibilidad y bloqueo por fila. Endpoints DRF protegidos con `IsCustomer`.

**Tech Stack:** Django 5.2 LTS, Django REST Framework 3.16, PostgreSQL 17, uv, pytest-django, drf-spectacular.

**Spec:** HU-13 en `RMSHOP/docs/backlog.md`, `RMSHOP/docs/arquitectura.md` sección 3.1, y `.agents/skills/index-proyecto/SKILL.md`.

## Global Constraints

- Precios y subtotales en COP como enteros sin decimales (`DecimalField(max_digits=12, decimal_places=0)`).
- Stock disponible calculado al vuelo: $\text{stock\_quantity} - \sum \text{reservas vigentes}(\text{expires\_at} > \text{now()})$. Nunca persistir stock disponible estático.
- Concurrencia segura: `select_for_update()` en `product_variants` dentro de `transaction.atomic()`.
- Autenticación: token Bearer de Clerk validado con `IsCustomer`. Un carrito por `user_id`, sin `session_id`.
- Duración de reserva: 15 minutos exactos desde la creación o actualización del ítem (`now() + timedelta(minutes=15)`).
- Formato de error API unificado: `{"code": "...", "message": "...", "fields": {...}}`.

## Review Focus

1. Concurrencia: Dos clientes intentan agregar la última unidad de una variante al mismo tiempo; solo uno debe tener éxito y el segundo debe recibir error `out_of_stock`.
2. Reservas expiradas: Reservas con `expires_at <= now()` no deben restar del stock disponible.
3. Auto-reserva: Si un cliente ya tiene una variante en su carrito y aumenta la cantidad, su propia reserva anterior no debe contarse en contra al validar disponibilidad.
4. Aislamiento y privacidad: Un cliente no puede ver, modificar ni recibir ítems de un carrito perteneciente a otro usuario.
5. Inexistencia o borrador: Si la variante no existe o el producto padre no está en estado `published`, debe rechazarse con error claro.

---

### Tarea 1: Modelos `Cart`, `CartItem`, `StockReservation` y Migraciones

**Archivos:**
- Crear: `RMSHOP/apps/backend/apps/cart/apps.py`
- Crear: `RMSHOP/apps/backend/apps/cart/models.py`
- Modificar: `RMSHOP/apps/backend/config/settings/base.py` (agregar `"apps.cart"` a `INSTALLED_APPS`)
- Test: `RMSHOP/apps/backend/apps/cart/tests/test_models.py`

**Interfaces:**
- Consume: `apps.users.models.User`, `apps.catalog.models.ProductVariant`
- Produce: Modelos `Cart`, `CartItem`, `StockReservation`

- [ ] **Paso 1.1: Escribir pruebas unitarias de modelos en `test_models.py`**
  - Creación de `Cart` asociado a `User` (unívoco por usuario).
  - Creación de `CartItem` con restricción única `(cart, variant)` y `quantity > 0`.
  - Creación de `StockReservation` asociado a `CartItem` y `ProductVariant` con `expires_at` y método `is_active`.
  - Métodos computados de carrito: `total_items` y `total_price`.
- [ ] **Paso 1.2: Ejecutar pruebas para verificar que fallen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_models.py`
  - Esperado: FAIL (módulo `apps.cart` no existe).
- [ ] **Paso 1.3: Implementar `apps/cart/apps.py`, registrar en `INSTALLED_APPS` e implementar `models.py`**
- [ ] **Paso 1.4: Generar y aplicar migraciones de base de datos**
  - Comando: `docker compose exec backend python manage.py makemigrations cart`
  - Comando: `docker compose exec backend python manage.py migrate`
- [ ] **Paso 1.5: Ejecutar pruebas de modelo para verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_models.py`
  - Esperado: PASS.

---

### Tarea 2: Servicio de Negocio `add_to_cart` y Cálculo de Disponibilidad

**Archivos:**
- Crear: `RMSHOP/apps/backend/apps/cart/services.py`
- Test: `RMSHOP/apps/backend/apps/cart/tests/test_services.py`

**Interfaces:**
- Consume: `Cart`, `CartItem`, `StockReservation`, `ProductVariant`, `User`
- Produce:
  - `get_available_variant_stock(variant: ProductVariant, exclude_reservation_id: int | None = None) -> int`
  - `add_to_cart(*, user: User, variant_id: int, quantity: int = 1) -> tuple[CartItem, StockReservation]`

- [ ] **Paso 2.1: Escribir pruebas unitarias de servicio en `test_services.py`**
  - Caso feliz: agregar variante con stock suficiente crea `CartItem` y `StockReservation` por 15 min.
  - Caso incremento: agregar a un ítem existente suma cantidades y extiende reserva 15 min más.
  - Caso sin stock: variante con stock 0 o reservas vigentes de otros usuarios lanza `ApiError` (`out_of_stock`).
  - Caso auto-reserva: la propia reserva del usuario no se autocensura al aumentar cantidad.
  - Caso concurrencia: `select_for_update()` protege la variante durante la reserva atómica.
- [ ] **Paso 2.2: Ejecutar pruebas de servicio para verificar que fallen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_services.py`
  - Esperado: FAIL (servicio no implementado).
- [ ] **Paso 2.3: Implementar `services.py`**
  - Funciones `get_available_variant_stock` y `add_to_cart` con `select_for_update()` y `transaction.atomic()`.
- [ ] **Paso 2.4: Ejecutar pruebas de servicio para verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_services.py`
  - Esperado: PASS.

---

### Tarea 3: Serializadores, Endpoints REST (`CartView`, `CartItemAddView`) y URLs

**Archivos:**
- Crear: `RMSHOP/apps/backend/apps/cart/serializers.py`
- Crear: `RMSHOP/apps/backend/apps/cart/views.py`
- Crear: `RMSHOP/apps/backend/apps/cart/urls.py`
- Modificar: `RMSHOP/apps/backend/config/urls.py`
- Test: `RMSHOP/apps/backend/apps/cart/tests/test_views.py`

**Interfaces:**
- Produce:
  - `GET /api/v1/cart/` -> Detalle del carrito del usuario autenticado.
  - `POST /api/v1/cart/items/` -> Agrega variante al carrito. Entrada: `{"variant_id": int, "quantity": int}`.

- [ ] **Paso 3.1: Escribir pruebas de integración en `test_views.py` cubriendo los ACs**
  - `AC-HU-13-1` (Camino feliz): Cliente con sesión agrega variante con stock -> 200/201 con carrito actualizado y reserva de 15 min.
  - `AC-HU-13-2` (Sin sesión): Petición anónima -> 401 Unauthorized (`not_authenticated`), base de datos intacta.
  - `AC-HU-13-3` (Caso límite / Sin stock): Si otra persona reservó el stock justo antes -> 400 Bad Request con código `out_of_stock`.
  - Validación de campos: `variant_id` requerido y existente, `quantity` entero $\ge 1$.
  - Privacidad: Carrito visible y mutable solo por el cliente autenticado dueño del carrito.
- [ ] **Paso 3.2: Ejecutar pruebas de vistas para verificar que fallen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_views.py`
  - Esperado: FAIL (rutas/vistas no definidas).
- [ ] **Paso 3.3: Implementar `serializers.py`, `views.py`, `urls.py` y actualizar `config/urls.py`**
- [ ] **Paso 3.4: Ejecutar pruebas de vistas para verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_views.py`
  - Esperado: PASS.

---

### Tarea 4: Validación y Auditoría Crítica de Pruebas con Argon (`--thinking-level high`)

**Archivos:**
- Scratch: `C:\Users\elkin\.gemini\antigravity\brain\be8951e5-54a8-49fe-b63e-a71f84b585f5\scratch\argon_prompt.txt`
- Ejecución: `call_argon.py --thinking-level high`

- [ ] **Paso 4.1: Compilar contexto y suite de pruebas para Argon**
  - Extraer código de modelos, servicio, vistas y pruebas creadas.
  - Redactar prompt técnico solicitando a Argon una revisión profunda con pensamiento alto enfocada en:
    1. Robustez ante carreras de concurrencia y bloqueos muertos (`deadlocks`).
    2. Cobertura estricta de los criterios AC-HU-13-1, AC-HU-13-2, AC-HU-13-3.
    3. Fugas de disponibilidad por reservas expiradas o canceladas.
    4. Cumplimiento de contratos de error estándar de RM Shop (`build_error`).
- [ ] **Paso 4.2: Invocar `call_argon.py` con `--thinking-level high`**
  - Comando: `python C:\Users\elkin\.gemini\config\skills\argon-subagent\scripts\call_argon.py --thinking-level high --prompt-file "<scratch_path>"`
- [ ] **Paso 4.3: Incorporar retroalimentación o pruebas adicionales recomendadas por Argon**
  - Aplicar mejoras o casos de prueba frontera identificados por Argon y ejecutar pytest.

---

### Tarea 5: Verificación Integral, Limpieza y Actualización Documental

**Archivos:**
- Modificar: `RMSHOP/docs/backlog.md`
- Modificar: `.agents/skills/index-proyecto/SKILL.md`

- [ ] **Paso 5.1: Ejecutar suite completa de backend**
  - Comando: `docker compose exec backend pytest` (debe pasar el 100% de los tests).
- [ ] **Paso 5.2: Ejecutar linter y formatter**
  - Comando: `docker compose exec backend ruff check .`
  - Comando: `docker compose exec backend ruff format --check .`
- [ ] **Paso 5.3: Actualizar `docs/backlog.md` y `.agents/skills/index-proyecto/SKILL.md`**
  - Registrar HU-13 como `[BACKEND LISTO]`, detallando nuevos modelos y endpoints.
