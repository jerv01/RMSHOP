# Diseño Técnico: HU-34 Edición y Eliminación de Productos en Catálogo

**Fecha:** 2026-11-04  
**Historia de Usuario:** HU-34 (Épica 7: Administración)  
**Alcance:** Exclusivo Backend  

---

## 1. Intención y Propósito

Permitir que los administradores de RM Shop actualicen los datos de cualquier producto existente (nombre, descripción, precios COP, material, categoría y estado) y eliminen productos del catálogo de forma segura (mediante archivado lógico) para mantener el catálogo actualizado sin comprometer la integridad referencial de pedidos ni carritos (AC-HU-34-3).

---

## 2. Objetivos, No-Objetivos y Restricciones

### Objetivos
- Servicios en `apps.catalog.services`:
  - `update_product(*, product_id: int, **fields) -> Product`:
    - Valida que `price > 0` e integer COP si se actualiza.
    - Valida que `previous_price > 0` si se suministra o actualiza.
    - Valida que `category` exista si se modifica.
    - Si cambia el `name`, recalcula un `slug` único sólo si es necesario.
    - Permite cambiar el `status` (por ejemplo, de `draft` a `published` o `archived`).
  - `delete_product(*, product_id: int) -> Product`:
    - Aplica borrado lógico marcando `product.status = ProductStatus.ARCHIVED`.
    - Garantiza que carritos, pedidos existentes e historial no queden inconsistentes (AC-HU-34-3 / P-15).
- Endpoints DRF en `apps.catalog.views`:
  - `GET /api/v1/admin/products/{id}`: Detalle del producto para administración.
  - `PATCH /api/v1/admin/products/{id}` (y `PUT`): Actualización de atributos.
  - `DELETE /api/v1/admin/products/{id}`: Eliminación (archivado) con respuesta `204 No Content`.
- Permisos: Protegidos con `IsRMAdmin` (401 no autenticado, 403 usuario regular).
- Documentación OpenAPI 3 / Swagger:
  - Anotación con `@extend_schema` y visibilidad interactiva en `/api/v1/docs/`.
- Pruebas automatizadas: Cobertura completa de casos felices (AC-HU-34-1), errores de validación (AC-HU-34-2), eliminación y preservación de pedidos/reservas (AC-HU-34-3) y permisos.

### No-Objetivos
- Interfaz gráfica en React / Frontend (diferida por solicitud expresa).
- Purga física irreversible de la fila en PostgreSQL (se adopta archivado lógico para cumplir AC-HU-34-3).
- Gestión de variantes de inventario (HU-36/37).

### Restricciones
- Tiempos de respuesta $\le 5$ segundos (según RNF de HU-34).
- Validación estricta de precios COP (`decimal_places=0`).
- Formato de error unificado `{code, message, fields}`.

---

## 3. Enfoques Técnicos para Eliminación (AC-HU-34-3)

1. **Enfoque 1: Borrado Lógico vía `status = ProductStatus.ARCHIVED` (Seleccionado)**
   - **Mecanismo**: El producto permanece en base de datos pero pasa a estado `archived`. Queda fuera del catálogo activo para clientes y no puede agregarse a nuevos carritos, mientras que los pedidos históricos y reservas conservan intacta la integridad referencial.
   - **Ventajas**: Cumple AC-HU-34-3 sin riesgo de romper claves foráneas de órdenes futuras (`order_items`). Reversible por el administrador.
2. **Enfoque 2: Borrado Físico Condicional (Descartado)**
   - **Mecanismo**: Si no tiene órdenes, `DELETE FROM products`; si tiene órdenes, rechaza o archiva.
   - **Desventajas**: Mayor complejidad, comportamiento no uniforme para el usuario y riesgo de fallos en cascada.

---

## 4. Decisiones Acordadas
- **Alcance**: Exclusivo backend.
- **Eliminación**: Borrado lógico archivando el producto (`status="archived"`).
- **Endpoint**: Rutas REST bajo `/api/v1/admin/products/{id}` con Swagger UI actualizado.
