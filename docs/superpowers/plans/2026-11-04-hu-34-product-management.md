# HU-34 Implementation Plan: Edición y Eliminación de Productos en Catálogo

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la actualización de atributos y eliminación lógica (archivado) de productos por parte de administradores (HU-34), con validaciones COP, preservación de integridad de pedidos y documentación Swagger.

**Architecture:** Extensión modular en Django DRF (`apps.catalog`). Se agregan los servicios `update_product` y `delete_product` en `services.py`, serializer de actualización parcial/total, la vista `AdminProductDetailView` (`GET`, `PATCH`, `PUT`, `DELETE`) protegida con `IsRMAdmin` y mapeada en `/api/v1/admin/products/{id}`.

**Tech Stack:** Django 5.2, Django REST Framework 3.16, `drf-spectacular`, PostgreSQL, Docker Compose, `pytest`, `ruff`.

**Spec:** [docs/superpowers/specs/2026-11-04-hu-34-product-management-design.md](file:///c:/Users/elkin/Documentos/Universidad/2026-II/Gestion/RMSHOP/docs/superpowers/specs/2026-11-04-hu-34-product-management-design.md)

## Global Constraints

- Precios en pesos colombianos representados en `DecimalField(max_digits=12, decimal_places=0)` sin centavos.
- Respuestas de error con formato unificado DRF: `{"code": "...", "message": "...", "fields": {...}}`.
- La eliminación es obligatoriamente un borrado lógico asignando `status="archived"`.
- Respuestas en $\le 5$ segundos.
- Nombres de código en inglés; comentarios y textos en español. Verificación con `pytest` y `ruff` en Docker.

## Review Focus

1. Al actualizar solo el precio vía `PATCH`, los demás campos (nombre, descripción, categoría) deben conservarse intactos.
2. Si el precio suministrado en la actualización es negativo o contiene decimales, debe rechazarse con 400.
3. Al eliminar un producto (`DELETE`), la respuesta debe ser 204 No Content y la fila debe continuar existiendo en base de datos con `status="archived"`.
4. Si un usuario no administrador intenta editar o eliminar, debe recibir 401 o 403.
5. Si se intenta actualizar o eliminar un producto inexistente (`id=99999`), debe responder 404 `{code: "not_found", ...}`.

---

### Task 1: Servicios `update_product` y `delete_product`

**Files:**
- Modify: `apps/backend/apps/catalog/services.py`
- Modify: `apps/backend/apps/catalog/tests/test_services.py`

**Steps:**
- [ ] 1.1 Escribir pruebas unitarias en `test_services.py` para:
  - `update_product` actualiza precio, nombre, categoría y estado exitosamente.
  - `update_product` regenera el slug si el nombre cambia.
  - `update_product` rechaza precio $\le 0$ o no entero COP.
  - `delete_product` asigna `status = ProductStatus.ARCHIVED` sin borrar la fila de base de datos.
  - `delete_product` y `update_product` lanzan excepción o error si el producto no existe.
- [ ] 1.2 Implementar `update_product` y `delete_product` en `apps/catalog/services.py`.
- [ ] 1.3 Ejecutar `docker compose run --rm backend pytest apps/catalog/tests/test_services.py` y verificar que pasen todas.

---

### Task 2: Serializers, Vistas DRF y Endpoints `/api/v1/admin/products/{id}`

**Files:**
- Modify: `apps/backend/apps/catalog/serializers.py`
- Modify: `apps/backend/apps/catalog/views.py`
- Modify: `apps/backend/apps/catalog/urls.py`
- Modify: `apps/backend/apps/catalog/tests/test_admin_products.py`

**Steps:**
- [ ] 2.1 Escribir pruebas de integración en `test_admin_products.py`:
  - AC-HU-34-1: Admin edita el precio con `PATCH` -> 200 OK y nuevo precio en el payload y BD.
  - AC-HU-34-2: Admin envía precio negativo o inválido -> 400 Bad Request `{code, message, fields}`.
  - AC-HU-34-3: Admin elimina producto con `DELETE` -> 204 No Content y producto persiste con `status="archived"`.
  - Admin consulta detalle con `GET` -> 200 OK.
  - Visitante o cliente sin rol admin -> 401/403.
  - Producto inexistente -> 404 Not Found.
- [ ] 2.2 Crear `ProductUpdateSerializer` en `apps/catalog/serializers.py`.
- [ ] 2.3 Crear `AdminProductDetailView` en `apps/catalog/views.py` soportando `GET`, `PATCH`, `PUT` y `DELETE`, anotada con `drf-spectacular`.
- [ ] 2.4 Registrar la ruta en `apps/catalog/urls.py`.
- [ ] 2.5 Ejecutar `docker compose run --rm backend pytest apps/catalog/tests/test_admin_products.py` y comprobar que pasen todas.

---

### Task 3: Verificación Integral, Linter y Actualización de Documentación

**Files:**
- Modify: `docs/backlog.md`
- Modify: `.agents/skills/index-proyecto/SKILL.md`

**Steps:**
- [ ] 3.1 Ejecutar suite completa del backend: `docker compose run --rm backend pytest`.
- [ ] 3.2 Ejecutar `docker compose run --rm backend ruff check .` y `docker compose run --rm backend ruff format --check .`.
- [ ] 3.3 Actualizar estado de HU-34 en `docs/backlog.md` y en `SKILL.md` de `index-proyecto`.
