# Plan de Implementación: HU-14 Eliminar Ítem del Carrito (Solo Backend)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la funcionalidad de eliminar un ítem del carrito para un cliente registrado, liberando su reserva de stock atómicamente, recalculando totales y garantizando aislamiento entre usuarios.

**Architecture:** Servicio `remove_from_cart` en `apps.cart.services` con `transaction.atomic()` que elimina el `CartItem` (disparando cascada sobre `StockReservation` y liberando el stock). Endpoint DRF `DELETE /api/v1/cart/items/<int:item_id>/` en `CartItemDetailView` protegido con `IsCustomer`, retornando el carrito actualizado (`CartOutputSerializer`).

**Tech Stack:** Django 5.2 LTS, Django REST Framework 3.16, PostgreSQL 17, uv, pytest-django, drf-spectacular.

**Spec:** HU-14 en `RMSHOP/docs/backlog.md`, `RMSHOP/docs/arquitectura.md`.

## Global Constraints

- Precios y subtotales en COP como enteros sin decimales (`DecimalField(max_digits=12, decimal_places=0)`).
- Stock disponible calculado al vuelo: al eliminar un `CartItem`, su `StockReservation` se elimina y el stock queda disponible de inmediato para otros clientes.
- Formato de error API unificado: `{"code": "...", "message": "...", "fields": {...}}`.
- Autenticación: token Bearer de Clerk validado con `IsCustomer`. Un carrito por `user_id`.
- Seguridad y Privacidad: Un cliente no puede eliminar ítems del carrito de otro cliente (responde 404 `not_found`).

## Review Focus

1. AC-HU-14-1 (Camino feliz): Carrito con 2 ítems, se elimina uno -> queda 1 ítem, totales recalculados correctamente.
2. AC-HU-14-2 (Reserva expirada): Ítem con reserva expirada (`expires_at < now()`) se elimina sin error y el carrito se actualiza.
3. AC-HU-14-3 (Último ítem): Carrito con 1 ítem, se elimina -> carrito queda vacío (`total_items=0`, `total_price="0"`, `items=[]`).
4. Aislamiento: Cliente A intentando eliminar ítem de Cliente B recibe 404 `not_found` y el ítem de B no se altera.
5. Idempotencia / Ítem inexistente: Intentar eliminar un `item_id` que no existe retorna 404 `not_found`.

---

### Tarea 1: Servicio de Dominio `remove_from_cart` y Pruebas Unitarias

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/services.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_services.py`

**Interfaces:**
- Produce: `remove_from_cart(*, user: User, item_id: int) -> Cart`
  - Busca `CartItem` filtrando por `id=item_id` y `cart__user=user`.
  - Si no existe, lanza `CartItem.DoesNotExist`.
  - Atómicamente elimina el `CartItem` (liberando `StockReservation` por CASCADE).
  - Retorna la instancia de `Cart` con relaciones preparadas para recálculo de totales.

- [ ] **Paso 1.1: Escribir pruebas unitarias en `test_services.py`**
  - Eliminar ítem existente: libera reserva y actualiza totales del carrito.
  - Eliminar ítem cuya reserva ya expiró: se elimina correctamente sin fallar.
  - Eliminar ítem inexistente: lanza `CartItem.DoesNotExist`.
  - Eliminar ítem perteneciente a otro usuario: lanza `CartItem.DoesNotExist`.
- [ ] **Paso 1.2: Implementar `remove_from_cart` en `services.py`**
- [ ] **Paso 1.3: Ejecutar pruebas de servicio y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_services.py`

---

### Tarea 2: Endpoint REST (`CartItemDetailView`), Enrutamiento y Pruebas de Integración

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/views.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/urls.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_views.py`

**Interfaces:**
- Consume: `remove_from_cart(*, user: User, item_id: int) -> Cart`
- Produce:
  - `DELETE /api/v1/cart/items/<int:item_id>/` (y `items/<int:item_id>`) -> Retorna `CartOutputSerializer(cart).data` con HTTP 200 OK.
  - Si el ítem no existe para el usuario autenticado: HTTP 404 Not Found (`code="not_found"`).
  - Si el usuario no está autenticado: HTTP 401 Unauthorized (`code="not_authenticated"`).

- [ ] **Paso 2.1: Escribir pruebas de integración en `test_views.py`**
  - AC-HU-14-1: Cliente autenticado elimina 1 de 2 ítems -> 200 OK, queda 1 ítem, totales recalculados.
  - AC-HU-14-2: Cliente elimina ítem con reserva expirada -> 200 OK, ítem removido, sin error.
  - AC-HU-14-3: Cliente elimina el único ítem -> 200 OK con carrito vacío (`total_items=0`, `total_price="0"`).
  - No autenticado: 401 Unauthorized.
  - Ítem inexistente o de otro cliente: 404 Not Found.
- [ ] **Paso 2.2: Implementar `CartItemDetailView.delete` en `views.py` y registrar en `urls.py`**
- [ ] **Paso 2.3: Ejecutar pruebas de vistas y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_views.py`

---

### Tarea 3: Validación y Auditoría Crítica con Gemini 4 Argon (`--thinking-level high`)

**Archivos:**
- Scratch: `C:\Users\elkin\.gemini\antigravity\brain\be8951e5-54a8-49fe-b63e-a71f84b585f5\scratch\argon_prompt_hu14.txt`
- Ejecución: `call_argon.py --thinking-level high`

- [ ] **Paso 3.1: Compilar contexto de HU-14 y ejecutar script de Argon**
- [ ] **Paso 3.2: Evaluar veredicto de Argon y aplicar optimizaciones identificadas**

---

### Tarea 4: Verificación Integral, Limpieza y Actualización Documental

**Archivos:**
- Modificar: `RMSHOP/docs/backlog.md`
- Modificar: `.agents/skills/index-proyecto/SKILL.md`

- [ ] **Paso 4.1: Ejecutar suite completa de backend (`pytest`)**
- [ ] **Paso 4.2: Ejecutar linter y formatter (`ruff check .`, `ruff format --check .`)**
- [ ] **Paso 4.3: Actualizar backlog y skill index-proyecto**
