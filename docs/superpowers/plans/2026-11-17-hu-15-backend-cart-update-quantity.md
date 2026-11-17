# Plan de Implementación: HU-15 Modificar Cantidades en el Carrito (Solo Backend)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la funcionalidad de modificar la cantidad de un ítem en el carrito para un cliente registrado, validando el stock disponible, actualizando la reserva de 15 minutos, recalculando totales y garantizando aislamiento.

**Architecture:** Servicio `update_cart_item_quantity` en `apps.cart.services` ejecutado bajo `@transaction.atomic` con `select_for_update(of=("self",))` en `ProductVariant` para verificar stock disponible (excluyendo la reserva previa del ítem). Endpoint `PATCH /api/v1/cart/items/<int:item_id>/` en `CartItemDetailView` protegido con `IsCustomer`, retornando el carrito actualizado (`CartOutputSerializer`).

**Tech Stack:** Django 5.2 LTS, Django REST Framework 3.16, PostgreSQL 17, uv, pytest-django, drf-spectacular.

**Spec:** HU-15 en `RMSHOP/docs/backlog.md`, `RMSHOP/docs/arquitectura.md`.

## Global Constraints

- Precios y subtotales en COP como enteros sin decimales (`DecimalField(max_digits=12, decimal_places=0)`).
- Stock disponible calculado al vuelo: $\text{stock\_quantity} - \sum \text{reservas vigentes}(\text{expires\_at} > \text{now()})$. Al modificar la cantidad, la reserva anterior del propio ítem no cuenta en su contra.
- Bloqueo transaccional de fila con `select_for_update(of=("self",))` en `ProductVariant` para prevenir sobreventa ante solicitudes concurrentes.
- Formato de error API unificado: `{"code": "...", "message": "...", "fields": {...}}`.
- Cantidad mínima: 1. Cantidades <= 0 se rechazan con 400 Bad Request (`code="validation_error"`).
- Cantidad que supere el stock disponible se rechaza con 400 Bad Request (`code="out_of_stock"`), informando el máximo disponible.
- Aislamiento: Un cliente no puede modificar ítems del carrito de otro cliente (responde 404 `not_found`).

## Review Focus

1. AC-HU-15-1 (Camino feliz): Ítem con cantidad 1 y stock de 3, se actualiza a 2 -> carrito muestra cantidad 2, reserva actualizada a 2 por 15 min, total recalculado.
2. AC-HU-15-2 (Exceso de stock): Cantidad solicitada mayor al stock disponible -> rechazo con `code="out_of_stock"`, indicando el máximo disponible. La cantidad en base de datos no cambia.
3. AC-HU-15-3 (Cantidad <= 0): Cantidad 0 o negativa -> rechazo con `code="validation_error"` y se mantiene la cantidad anterior intacta.
4. Concurrencia: Dos peticiones concurrentes para aumentar cantidad sobre el límite de stock disponible no pueden sobrevender.
5. Seguridad / BOLA: Cliente A intentando modificar ítem de Cliente B recibe 404 `not_found` y el ítem de B no se altera.

---

### Tarea 1: Servicio de Dominio `update_cart_item_quantity` y Pruebas Unitarias

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/services.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_services.py`

**Interfaces:**
- Produce: `update_cart_item_quantity(*, user: User, item_id: int, quantity: int) -> tuple[CartItem, StockReservation]`
  - Valida `quantity >= 1`; si no, lanza `ValidationError({"quantity": ["La cantidad debe ser mayor a cero."]})`.
  - Busca `CartItem` por `id=item_id` y `cart__user=user`. Si no existe, lanza `CartItem.DoesNotExist`.
  - Bloquea atómicamente la variante asociada con `select_for_update(of=("self",))`.
  - Calcula stock disponible excluyendo la reserva actual de este ítem (`exclude_reservation_id`).
  - Si `quantity > available_stock`, lanza `ApiError(detail=f"No hay disponibilidad suficiente. El stock máximo disponible es {available_stock}.", code="out_of_stock", fields={"max_available": available_stock})`.
  - Actualiza `item.quantity = quantity`.
  - Actualiza o crea `StockReservation` con `quantity=quantity` y `expires_at = now() + 15 min`.
  - Retorna `(item, reservation)`.

- [ ] **Paso 1.1: Escribir pruebas unitarias en `test_services.py`**
  - AC-HU-15-1: Aumentar y disminuir cantidad dentro del stock disponible actualiza ítem y reserva.
  - AC-HU-15-2: Intentar superar el stock disponible lanza `ApiError(code="out_of_stock")` con `fields["max_available"]`.
  - AC-HU-15-3: Cantidad 0 o negativa lanza `ValidationError` y no muta el ítem.
  - Ítem inexistente o de otro usuario lanza `CartItem.DoesNotExist`.
- [ ] **Paso 1.2: Implementar `update_cart_item_quantity` en `services.py`**
- [ ] **Paso 1.3: Ejecutar pruebas de servicio y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_services.py`

---

### Tarea 2: Serializador, Método `PATCH` en `CartItemDetailView` y Pruebas de Integración

**Archivos:**
- Modificar: `RMSHOP/apps/backend/apps/cart/serializers.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/views.py`
- Modificar: `RMSHOP/apps/backend/apps/cart/tests/test_views.py`

**Interfaces:**
- Produce:
  - `CartItemUpdateInputSerializer(serializers.Serializer)`: `quantity = serializers.IntegerField(min_value=1, required=True)`
  - `PATCH /api/v1/cart/items/<int:item_id>/`:
    - Valida payload con `CartItemUpdateInputSerializer`.
    - Llama a `update_cart_item_quantity`.
    - Retorna `CartOutputSerializer(cart).data` con HTTP 200 OK.
    - Si el ítem no existe para el usuario: 404 Not Found (`code="not_found"`).
    - Si la cantidad no está disponible: 400 Bad Request (`code="out_of_stock"`).
    - Si no está autenticado: 401 Unauthorized (`code="not_authenticated"`).

- [ ] **Paso 2.1: Escribir pruebas de integración en `test_views.py`**
  - AC-HU-15-1: PATCH con nueva cantidad válida -> 200 OK con totales y subtotales recalculados.
  - AC-HU-15-2: PATCH con cantidad mayor a stock -> 400 Bad Request con `code="out_of_stock"`.
  - AC-HU-15-3: PATCH con cantidad <= 0 o inválida -> 400 Bad Request (`code="validation_error"`), cantidad previa intacta.
  - No autenticado -> 401 Unauthorized.
  - Ítem inexistente o de otro usuario -> 404 Not Found.
- [ ] **Paso 2.2: Implementar `CartItemUpdateInputSerializer` y `CartItemDetailView.patch`**
- [ ] **Paso 2.3: Ejecutar pruebas de vistas y verificar que pasen**
  - Comando: `docker compose exec backend pytest apps/cart/tests/test_views.py`

---

### Tarea 3: Validación y Auditoría Crítica con Gemini 4 Argon (`--thinking-level high`)

**Archivos:**
- Scratch: `C:\Users\elkin\.gemini\antigravity\brain\be8951e5-54a8-49fe-b63e-a71f84b585f5\scratch\argon_prompt_hu15.txt`
- Ejecución: `call_argon.py --thinking-level high`

- [ ] **Paso 3.1: Compilar contexto de HU-15 y ejecutar script de Argon**
- [ ] **Paso 3.2: Evaluar veredicto de Argon y aplicar optimizaciones**

---

### Tarea 4: Verificación Integral, Limpieza y Actualización Documental

**Archivos:**
- Modificar: `RMSHOP/docs/backlog.md`
- Modificar: `.agents/skills/index-proyecto/SKILL.md`

- [ ] **Paso 4.1: Ejecutar suite completa de backend (`pytest`)**
- [ ] **Paso 4.2: Ejecutar linter y formatter (`ruff check .`, `ruff format --check .`)**
- [ ] **Paso 4.3: Actualizar backlog y skill index-proyecto**
