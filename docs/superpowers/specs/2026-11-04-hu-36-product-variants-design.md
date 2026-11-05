# Diseño Técnico: HU-36 Definición de Variantes de Producto (Colores y Tallas)

**Fecha:** 2026-11-04  
**Historia de Usuario:** HU-36 (Épica 7: Gestión de productos)  
**Dependencias:** HU-33, HU-11  
**Alcance:** Exclusivo Backend  

---

## 1. Intención y Propósito

Permitir que el Administrador defina y gestione las combinaciones de color y talla (variantes) para cada diseño/prenda del catálogo de RM Shop. Cada variante representará una unidad de mantenimiento de stock (`SKU` / `ProductVariant`) sobre la cual se gestionará el inventario en HU-37 y las reservas de compra en el carrito (HU-17).

---

## 2. Objetivos, No-Objetivos y Restricciones

### Objetivos
- **Modelo `ProductVariant` (`apps.catalog.models`):**
  - Vinculado a `Product` mediante clave foránea en cascada (`related_name="variants"`).
  - Campos: `color` (`CharField(max_length=50)`), `size` (`CharField(max_length=20)`), `stock_quantity` (`PositiveIntegerField(default=0)`), `created_at`, `updated_at`.
  - Normalización en guardado: `color` en Title Case limpio (ej. "Negro") y `size` en mayúsculas limpias (ej. "M", "XL", "ÚNICA").
  - Restricción única en base de datos: `unique(product, color, size)`.
  - Restricción de verificación: `CHECK (stock_quantity >= 0)`.
- **Servicios de negocio (`apps.catalog.services`):**
  - `create_product_variant(*, product_id, color, size, stock_quantity=0)`:
    - Valida existencia del producto.
    - Normaliza `color` y `size`.
    - Verifica que no exista una variante idéntica para el producto (AC-HU-36-2).
    - Valida `stock_quantity >= 0`.
  - `bulk_create_variants(*, product_id, colors: list[str], sizes: list[str]) -> list[ProductVariant]`:
    - Permite la generación automática de la matriz cartesiana `colores × tallas`.
    - Ignora o reporta combinaciones ya existentes sin romper la transacción atómica.
  - `delete_product_variant(*, product_id, variant_id)`:
    - Valida si la variante tiene `stock_quantity > 0` o reservas activas. En dicho caso, **bloquea la eliminación** con `ValidationError` explicativo cumpliendo AC-HU-36-3.
    - Si el stock es 0 y no tiene reservas, elimina el registro.
- **Endpoints REST (`apps.catalog.views`):**
  - `GET /api/v1/admin/products/{product_id}/variants`: Lista todas las variantes del producto ordenadas por talla y color.
  - `POST /api/v1/admin/products/{product_id}/variants`: Crea una variante individual (201 Created).
  - `POST /api/v1/admin/products/{product_id}/variants/bulk`: Genera variantes a partir de listas de colores y tallas (201 Created).
  - `DELETE /api/v1/admin/products/{product_id}/variants/{variant_id}`: Elimina la variante si su stock es 0 (204 No Content).
- **Seguridad y Documentación:**
  - Restringido a administradores autenticados (`IsRMAdmin`).
  - Documentado en Swagger UI OpenAPI 3 (`/api/v1/docs/`).
- **Pruebas automatizadas:**
  - Pruebas unitarias de modelo, servicios y endpoints REST con casos felices (AC-HU-36-1), duplicados (AC-HU-36-2), bloqueo de eliminación con stock (AC-HU-36-3) y permisos.

### No-Objetivos
- Implementación de interfaz de usuario en React (diferida para la etapa de frontend).
- Aumento o movimiento de inventario transaccional con auditoría (alcance específico de HU-37).
- Reserva de 15 minutos en el carrito (alcance de HU-17 / app `inventory`).

### Restricciones
- Tiempos de guardado $\le 3$ segundos (según RNF de HU-36).
- Cero combinaciones duplicadas por producto.
- Respuestas de error unificadas `{code, message, fields}`.

---

## 3. Especificación de Contrato para el Frontend

### Endpoints y Payloads HTTP
Todos los endpoints requieren `Authorization: Bearer <clerk_token>` con rol de administrador.

#### 1. Listar variantes de un producto
- `GET /api/v1/admin/products/{product_id}/variants`
- **Respuesta (200 OK):**
  ```json
  [
    {
      "id": 1,
      "product_id": 10,
      "color": "Negro",
      "size": "M",
      "stock_quantity": 0,
      "created_at": "2026-11-04T21:00:00Z",
      "updated_at": "2026-11-04T21:00:00Z"
    }
  ]
  ```

#### 2. Crear variante individual
- `POST /api/v1/admin/products/{product_id}/variants`
- **Cuerpo JSON:**
  ```json
  {
    "color": "Negro",
    "size": "M",
    "stock_quantity": 0
  }
  ```
- **Respuesta (201 Created):** Retorna el objeto de la variante creada.
- **Error duplicado (400 Bad Request):**
  ```json
  {
    "code": "validation_error",
    "message": "Los datos enviados no son válidos.",
    "fields": {
      "non_field_errors": ["Ya existe una variante con el color 'Negro' y la talla 'M' para este producto."]
    }
  }
  ```

#### 3. Generar variantes en lote
- `POST /api/v1/admin/products/{product_id}/variants/bulk`
- **Cuerpo JSON:**
  ```json
  {
    "colors": ["Negro", "Blanco"],
    "sizes": ["S", "M", "L"]
  }
  ```
- **Respuesta (201 Created):** Lista de todas las variantes generadas.

#### 4. Eliminar variante
- `DELETE /api/v1/admin/products/{product_id}/variants/{variant_id}`
- **Respuesta exitosa (204 No Content):** Sin contenido.
- **Error con stock (400 Bad Request - AC-HU-36-3):**
  ```json
  {
    "code": "validation_error",
    "message": "Los datos enviados no son válidos.",
    "fields": {
      "stock_quantity": ["No se puede eliminar una variante que posee stock (3 unidades) o reservas activas."]
    }
  }
  ```
