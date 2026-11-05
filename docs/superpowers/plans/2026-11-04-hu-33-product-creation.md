# HU-33 Implementation Plan: Creación de Productos en Catálogo y Documentación Swagger

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la creación de productos por parte de administradores (HU-33) con validaciones COP, advertencia al superar 30 productos, estado inicial en borrador e integración de Swagger UI con `drf-spectacular` en `/api/v1/docs/`.

**Architecture:** Monolito modular Django con DRF. La app `apps.catalog` albergará los modelos `Category` y `Product`, la lógica transaccional en `services.py`, serializers DRF y la vista protegida con `IsRMAdmin`. La documentación OpenAPI 3 se configurará globalmente en `config/settings/base.py` y `config/urls.py`.

**Tech Stack:** Django 5.2, Django REST Framework 3.16, `drf-spectacular`, PostgreSQL, Docker Compose, `pytest`, `ruff`.

**Spec:** [docs/superpowers/specs/2026-11-04-hu-33-product-creation-design.md](file:///c:/Users/elkin/Documentos/Universidad/2026-II/Gestion/RMSHOP/docs/superpowers/specs/2026-11-04-hu-33-product-creation-design.md)

## Global Constraints

- Precios en pesos colombianos representados en `DecimalField(max_digits=12, decimal_places=0)` sin centavos.
- Respuestas de error con formato unificado DRF: `{"code": "...", "message": "...", "fields": {...}}`.
- El producto se crea obligatoriamente con `status="draft"`.
- Umbral de catálogo: $\ge 30$ productos no bloquea, sino que retorna una advertencia (`warning`).
- Nombres de modelos, variables y endpoints en inglés; textos, docstrings y mensajes en español.
- Formato y linting verificado con `ruff`. Pruebas ejecutadas con `pytest` dentro del contenedor Docker.

## Review Focus

1. Un precio con decimales o negativo debe ser rechazado inmediatamente con error 400.
2. El slug del producto debe ser autogenerado y único para evitar colisiones ante nombres similares.
3. Usuarios sin rol `admin` (`public_metadata.role != "admin"`) o anónimos deben recibir 401/403.
4. Con 30 o más productos en el catálogo, la creación debe continuar siendo exitosa (201) pero incluir `warning`.
5. El endpoint Swagger `/api/v1/docs/` debe cargar sin errores de JS ni fallas de renderizado del esquema.

---

### Task 1: Configurar Swagger UI y OpenAPI 3 con `drf-spectacular`

**Files:**
- Modify: `apps/backend/pyproject.toml`
- Modify: `apps/backend/config/settings/base.py`
- Modify: `apps/backend/config/urls.py`
- Create: `apps/backend/apps/core/tests/test_swagger.py`

**Steps:**
- [ ] 1.1 Agregar `drf-spectacular` a las dependencias en `pyproject.toml` e instalarlo en el contenedor Docker.
- [ ] 1.2 Registrar `drf_spectacular` en `INSTALLED_APPS` y configurar `REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"` junto con la configuración de `SPECTACULAR_SETTINGS`.
- [ ] 1.3 Exponer las rutas `/api/v1/schema/` y `/api/v1/docs/` en `config/urls.py`.
- [ ] 1.4 Escribir prueba en `apps/core/tests/test_swagger.py` verificando status 200 en `/api/v1/schema/` y `/api/v1/docs/`.
- [ ] 1.5 Ejecutar `docker compose run --rm backend pytest apps/core/tests/test_swagger.py` y verificar que pase.

---

### Task 2: Modelos `Category` y `Product` con Migración de Datos

**Files:**
- Modify: `apps/backend/apps/catalog/models.py`
- Create: `apps/backend/apps/catalog/migrations/0001_initial.py`
- Create: `apps/backend/apps/catalog/migrations/0002_seed_categories.py`
- Create: `apps/backend/apps/catalog/tests/test_models.py`

**Steps:**
- [ ] 2.1 Escribir pruebas en `apps/catalog/tests/test_models.py` para validar creación de `Category`, unicidad de slug, y creación de `Product` con `status="draft"`.
- [ ] 2.2 Definir los modelos `Category` y `Product` en `apps/catalog/models.py` según la especificación.
- [ ] 2.3 Generar migración inicial `0001_initial.py` y crear la migración de datos `0002_seed_categories.py` para insertar las 4 categorías iniciales.
- [ ] 2.4 Aplicar migraciones con `docker compose exec backend python manage.py migrate` y correr `test_models.py`.

---

### Task 3: Capa de Servicio `create_product` (Reglas de Negocio HU-33)

**Files:**
- Create: `apps/backend/apps/catalog/services.py`
- Create: `apps/backend/apps/catalog/tests/test_services.py`

**Steps:**
- [ ] 3.1 Escribir pruebas unitarias en `test_services.py` cubriendo:
  - Creación exitosa con datos válidos y estado inicial `draft`.
  - Rechazo con `ValidationError` si precio es $\le 0$ o no es entero COP.
  - Rechazo con `ValidationError` si `previous_price` es $\le 0$.
  - Generación de slug único.
  - Retorno de advertencia (`warning`) cuando el total de productos no archivados es $\ge 30$.
- [ ] 3.2 Implementar la función `create_product(...)` en `apps/catalog/services.py`.
- [ ] 3.3 Ejecutar las pruebas de servicio y comprobar que pasen todas.

---

### Task 4: Serializers, Vistas DRF y Endpoint `POST /api/v1/admin/products`

**Files:**
- Create: `apps/backend/apps/catalog/serializers.py`
- Create: `apps/backend/apps/catalog/views.py`
- Create: `apps/backend/apps/catalog/urls.py`
- Modify: `apps/backend/config/urls.py`
- Create: `apps/backend/apps/catalog/tests/test_admin_products.py`

**Steps:**
- [ ] 4.1 Escribir pruebas de integración en `test_admin_products.py`:
  - AC-HU-33-1: Admin crea producto con datos válidos -> 201 Created.
  - AC-HU-33-2: Admin envía precio vacío o inválido -> 400 Bad Request `{code, message, fields}`.
  - AC-HU-33-3: Catálogo con $\ge 30$ productos -> 201 Created con advertencia en la respuesta.
  - Seguridad: Cliente autenticado sin rol admin -> 403 Forbidden. Visitante sin autenticación -> 401 Unauthorized.
- [ ] 4.2 Crear `ProductCreateSerializer` y `ProductDetailSerializer` en `apps/catalog/serializers.py`.
- [ ] 4.3 Crear `AdminProductCreateView` en `apps/catalog/views.py` usando `IsRMAdmin` e invocando el servicio.
- [ ] 4.4 Configurar la ruta en `apps/catalog/urls.py` y enlazarla en `config/urls.py`.
- [ ] 4.5 Ejecutar las pruebas de integración y verificar que todas pasen.

---

### Task 5: Verificación Integral, Linting y Actualización del Índice

**Files:**
- Modify: `docs/backlog.md`
- Modify: `.agents/skills/index-proyecto/SKILL.md`

**Steps:**
- [ ] 5.1 Ejecutar suite completa del backend: `docker compose run --rm backend pytest`.
- [ ] 5.2 Ejecutar linter y formato: `docker compose run --rm backend ruff check .` y `docker compose run --rm backend ruff format .`.
- [ ] 5.3 Actualizar el estado de HU-33 en `docs/backlog.md` y el mapa de componentes en `SKILL.md` de `index-proyecto`.
