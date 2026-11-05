# Plan de Implementación: HU-36 Definición de Variantes de Producto (Colores y Tallas)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la creación individual y masiva (colores x tallas), listado y eliminación segura de variantes de producto (`ProductVariant`) con control de unicidad y bloqueo de eliminación si existe stock o reservas.

**Architecture:** Capas en Django/DRF: modelo `ProductVariant` en `apps.catalog.models` con `unique(product, color, size)` y `CHECK (stock_quantity >= 0)`; servicios de creación, generación masiva y eliminación condicional en `apps.catalog.services`; endpoints REST bajo `/api/v1/admin/products/{id}/variants` con permisos `IsRMAdmin` y Swagger OpenAPI.

**Tech Stack:** Python 3.14, Django 5.2, Django REST Framework 3.16, PostgreSQL.

**Spec:** [`RMSHOP/docs/superpowers/specs/2026-11-04-hu-36-product-variants-design.md`](file:///c:/Users/elkin/Documentos/Universidad/2026-II/Gestion/RMSHOP/docs/superpowers/specs/2026-11-04-hu-36-product-variants-design.md)

## Global Constraints

- Monorepo `RMSHOP/`: Backend en `apps/backend/`.
- No modificar el frontend en esta historia (especificación documentada en la spec técnica).
- Formato de error DRF unificado `{code, message, fields}`.
- Validación de unicidad de combinaciones (AC-HU-36-2).
- Bloqueo de eliminación cuando `stock_quantity > 0` (AC-HU-36-3).
- Todos los cambios deben pasar `ruff check .`, `ruff format --check .` y la suite de `pytest`.

## Review Focus

1. **Combinación duplicada:** Intentar crear la misma combinación de color y talla (incluso variando mayúsculas/minúsculas) es rechazada con `400 Bad Request` y mensaje claro en `fields`.
2. **Eliminación con stock positivo:** Si la variante tiene `stock_quantity > 0`, se bloquea con `400 Bad Request` indicando que no se puede eliminar con existencias.
3. **Generación masiva (Bulk):** Al suministrar listas de colores y tallas, crea todas las combinaciones inexistentes y retorna el conjunto resultante.
4. **Permisos y seguridad:** Solo administradores (`IsRMAdmin`) pueden operar los endpoints de variantes.
5. **Cascada al archivar/borrar producto:** Si un producto se elimina físicamente, sus variantes se eliminan en cascada; si se archiva lógicamente, sus variantes permanecen asociadas.

---

### Task 1: Modelo `ProductVariant` y Migración de Base de Datos

**Files:**
- Modify: `apps/backend/apps/catalog/models.py`
- Create: `apps/backend/apps/catalog/migrations/0006_productvariant.py`
- Modify: `apps/backend/apps/catalog/tests/test_models.py`

**Interfaces:**
- Produces: `ProductVariant` con campos `product`, `color`, `size`, `stock_quantity`, `created_at`, `updated_at` y restricciones `unique(product, color, size)` y `stock_quantity >= 0`.

- [ ] **Step 1: Write failing test for `ProductVariant`**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Define `ProductVariant` in `models.py` and run makemigrations/migrate**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Format and lint**

---

### Task 2: Servicios de Negocio para Variantes (`create_product_variant`, `bulk_create_variants`, `delete_product_variant`)

**Files:**
- Modify: `apps/backend/apps/catalog/services.py`
- Modify: `apps/backend/apps/catalog/tests/test_services.py`

**Interfaces:**
- Produces:
  - `create_product_variant(*, product_id: int, color: str, size: str, stock_quantity: int = 0) -> ProductVariant`
  - `bulk_create_variants(*, product_id: int, colors: list[str], sizes: list[str]) -> list[ProductVariant]`
  - `delete_product_variant(*, product_id: int, variant_id: int) -> None`

- [ ] **Step 1: Write failing tests for variant services**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement variant services in `services.py`**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Format and lint**

---

### Task 3: Serializadores y Vistas REST para Variantes

**Files:**
- Modify: `apps/backend/apps/catalog/serializers.py`
- Modify: `apps/backend/apps/catalog/views.py`
- Modify: `apps/backend/apps/catalog/urls.py`
- Create: `apps/backend/apps/catalog/tests/test_admin_product_variants.py`

**Interfaces:**
- Endpoints:
  - `GET /api/v1/admin/products/{product_id}/variants`
  - `POST /api/v1/admin/products/{product_id}/variants`
  - `POST /api/v1/admin/products/{product_id}/variants/bulk`
  - `DELETE /api/v1/admin/products/{product_id}/variants/{variant_id}`

- [ ] **Step 1: Write integration tests for admin variant endpoints**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement serializers, views and routes**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Format and lint**

---

### Task 4: Verificación Integral, Formato y Actualización de Documentación

**Files:**
- Modify: `RMSHOP/docs/backlog.md`
- Modify: `.agents/skills/index-proyecto/SKILL.md`

- [ ] **Step 1: Run full backend pytest suite**
- [ ] **Step 2: Run Ruff check and format check**
- [ ] **Step 3: Update documentation in backlog.md and index-proyecto**
