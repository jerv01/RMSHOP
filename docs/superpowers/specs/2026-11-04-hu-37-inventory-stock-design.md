# Especificación de Diseño: HU-37 Registro y Aumento Manual de Stock por Variante

## 1. Contexto y Objetivos
- **Historia de Usuario**: HU-37 (Épica 7: Panel de Administración - Catálogo e Inventario).
- **Actor**: Administrador de la tienda.
- **Objetivo**: Permitir al administrador registrar el stock inicial e incrementarlo (o ajustarlo) manualmente por cada variante de producto (`ProductVariant`) para reflejar ingresos reales de mercancía en tienda física.
- **Auditoría e Historial**: Registrar cada ajuste en la tabla `stock_movements` con fecha/hora, usuario administrador que ejecutó la operación, cantidad ajustada (`delta`), stock resultante (`resulting_stock`) y motivo (`reason`).
- **Criterios de Aceptación**:
  - `AC-HU-37-1`: Variante con stock 3, al sumar 2, el stock final pasa a 5.
  - `AC-HU-37-2`: Cantidad no numérica o que resulte en stock negativo (< 0), se rechaza con error de validación estandarizado (`code: "validation_error"`).
  - `AC-HU-37-3`: Combinación agotada (stock 0), al incrementarse queda disponible con el nuevo stock actualizado.

---

## 2. Modelo de Datos (`apps.inventory.models.StockMovement`)

Tabla en PostgreSQL: `stock_movements`
- `id`: BigAutoField (PK)
- `variant`: ForeignKey a `catalog.ProductVariant` con `on_delete=models.CASCADE`, `related_name="stock_movements"`.
- `admin`: ForeignKey a `users.User` con `on_delete=models.SET_NULL`, `null=True`, `blank=True`, `related_name="stock_movements"`.
- `delta`: `IntegerField(help_text="Variación de stock; positivo para ingresos, negativo para ajustes/mermas.")`
- `resulting_stock`: `PositiveIntegerField(help_text="Cantidad de stock resultante tras aplicar el delta.")`
- `reason`: `CharField(max_length=255, blank=True, default="Ajuste manual")`
- `created_at`: `DateTimeField(auto_now_add=True, db_index=True)`

Meta:
- `db_table = "stock_movements"`
- `ordering = ["-created_at", "-id"]`
- `indexes = [models.Index(fields=["variant", "-created_at"])]`

---

## 3. Lógica de Servicio (`apps.inventory.services`)

### `adjust_variant_stock(*, variant_id: int, delta: int, admin_user: User | None = None, reason: str = "Ajuste manual") -> tuple[ProductVariant, StockMovement]`
- Abre transacción atómica (`transaction.atomic()`).
- Obtiene la variante bloqueando la fila con `ProductVariant.objects.select_for_update().get(id=variant_id)`.
- Si la variante no existe, levanta `ValidationError({"variant_id": ["La variante especificada no existe."]})` o 404 según corresponda.
- Valida que `delta != 0` (no se admiten movimientos vacíos).
- Calcula `new_stock = variant.stock_quantity + delta`.
- Valida que `new_stock >= 0`. Si `new_stock < 0`, levanta `ValidationError({"delta": [f"El stock resultante no puede ser negativo (actual: {variant.stock_quantity}, cambio: {delta})."]})`.
- Actualiza `variant.stock_quantity = new_stock` y guarda con `update_fields=["stock_quantity", "updated_at"]`.
- Crea y persiste el registro en `StockMovement`:
  - `variant=variant`
  - `admin=admin_user`
  - `delta=delta`
  - `resulting_stock=new_stock`
  - `reason=reason.strip() or "Ajuste manual"`
- Retorna la tupla `(variant, movement)`.

---

## 4. API REST y Endpoints (`apps.inventory.views`)

1. **Ajuste de Stock**:
   - `POST /api/v1/admin/variants/{variant_id}/stock`
   - `POST /api/v1/admin/products/{product_id}/variants/{variant_id}/stock` (alias con contexto de producto)
   - Permiso: `IsRMAdmin`
   - Request Body:
     ```json
     {
       "delta": 2,
       "reason": "Ingreso de lote semanal"
     }
     ```
   - Response 200 OK:
     ```json
     {
       "variant": {
         "id": 1,
         "product_id": 10,
         "color": "Negro",
         "size": "M",
         "stock_quantity": 5,
         "created_at": "2026-11-04T12:00:00Z",
         "updated_at": "2026-11-04T12:05:00Z"
       },
       "movement": {
         "id": 1,
         "variant_id": 1,
         "delta": 2,
         "resulting_stock": 5,
         "reason": "Ingreso de lote semanal",
         "admin": {
           "id": 1,
           "email": "admin@rmshop.co"
         },
         "created_at": "2026-11-04T12:05:00Z"
       }
     }
     ```

2. **Historial de Movimientos de Stock**:
   - `GET /api/v1/admin/variants/{variant_id}/stock-movements`
   - `GET /api/v1/admin/products/{product_id}/variants/{variant_id}/stock-movements`
   - Permiso: `IsRMAdmin`
   - Response 200 OK: Lista ordenada descendente de movimientos de inventario de la variante.

---

## 5. Manejo de Errores y Validaciones
- Si `delta` no es numérico -> 400 Bad Request (`code: "validation_error"`).
- Si `delta == 0` -> 400 Bad Request (`code: "validation_error"`).
- Si `stock_quantity + delta < 0` -> 400 Bad Request (`code: "validation_error"`).
- Si `variant_id` no existe (o si `product_id` no coincide con la variante) -> 404 Not Found (`code: "not_found"`).
- Si el usuario no tiene rol `admin` -> 403 Forbidden (`code: "permission_denied"`).
- Si no hay token de autenticación -> 401 Unauthorized (`code: "not_authenticated"`).
