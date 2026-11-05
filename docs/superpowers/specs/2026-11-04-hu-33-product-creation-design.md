# Diseño Técnico: HU-33 Creación de Productos en Catálogo y Documentación Swagger

**Fecha:** 2026-11-04  
**Historia de Usuario:** HU-33 (Épica 7: Administración)  
**Alcance:** Exclusivo Backend  

---

## 1. Intención y Propósito

Permitir que los administradores de RM Shop creen productos en el catálogo con sus datos base (nombre, descripción, precio, precio anterior opcional, material y categoría) bajo el rol `IsRMAdmin`, e integrar una interfaz interactiva Swagger UI en `/api/v1/docs/` mediante `drf-spectacular` para inspeccionar y probar la API desde el navegador.

---

## 2. Objetivos, No-Objetivos y Restricciones

### Objetivos
- Modelo `Category` en `apps.catalog.models` con `name` y `slug` único.
- Migración de datos que inserte las 4 categorías iniciales fijas:
  1. *Camisetas / Tops*
  2. *Buzos / Sacos*
  3. *Pantalones / Jeans*
  4. *Conjuntos*
- Modelo `Product` en `apps.catalog.models` con:
  - `name`: `CharField(max_length=255)`
  - `slug`: `SlugField(unique=True)`
  - `description`: `TextField`
  - `price`: `DecimalField(max_digits=12, decimal_places=0)` (COP entero)
  - `previous_price`: `DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)`
  - `material`: `CharField(max_length=120)`
  - `category`: `ForeignKey(Category, on_delete=models.PROTECT, related_name="products")`
  - `status`: `CharField` con choices `draft`, `published`, `archived` (valor inicial: `draft`).
  - `created_at` / `updated_at`.
- Servicio `create_product(...)` en `apps.catalog.services`:
  - Valida que `price > 0`.
  - Valida que `previous_price > 0` si se proporciona.
  - Valida existencia de `category`.
  - Genera `slug` único.
  - Estado inicial `status = "draft"`.
  - Evalúa la regla del catálogo de 30 productos: si el total de productos no archivados es $\ge 30$, permite la creación pero incluye una advertencia explícita en el resultado.
- Endpoint DRF `POST /api/v1/admin/products`:
  - Protegido por autenticación y permiso `IsRMAdmin`.
  - Respuesta HTTP 201 con datos del producto creado y campo opcional `warning` si aplica AC-HU-33-3.
  - Respuestas HTTP 400 uniformes `{code, message, fields}` en caso de error de validación.
  - Respuestas HTTP 401 / 403 para accesos no autenticados o usuarios sin rol administrador.
- Integración de `drf-spectacular`:
  - Dependencia agregada en `pyproject.toml`.
  - Configuración en `config.settings.base` y `REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"]`.
  - Rutas `/api/v1/schema/` (OpenAPI 3 JSON/YAML) y `/api/v1/docs/` (Swagger UI interactivo con soporte de autenticación Bearer).
- Cobertura de pruebas unitarias y de integración para todos los criterios AC-HU-33-1, AC-HU-33-2, AC-HU-33-3 y permisos.

### No-Objetivos
- Implementación de interfaz de usuario en el frontend (diferida por solicitud expresa).
- Creación y gestión de variantes (color/talla) e inventario (corresponden a HU-36 y HU-37).
- Carga y procesamiento de imágenes WebP (corresponde a HU-35).
- Edición y eliminación de productos (corresponde a HU-34).

### Restricciones
- Moneda: COP representada sin decimales (`decimal_places=0`).
- Tiempo de respuesta en creación $\le 3$ segundos.
- Cumplimiento de estándares del repositorio: formateo con `ruff`, pruebas con `pytest` ejecutadas en Docker.

---

## 3. Enfoques Considerados

1. **`drf-spectacular` (Seleccionado)**:
   - Soporte nativo para OpenAPI 3 y Swagger UI en DRF.
   - Introspección automática sin duplicar código de documentación.
2. **`drf-yasg` (Descartado)**:
   - Basado en OpenAPI 2.0 y desactualizado respecto a Django 5.2.
3. **Swagger UI estático / YAML manual (Descartado)**:
   - Propenso a desactualizarse ante cualquier cambio en serializers o modelos.

---

## 4. Decisiones Acordadas con el Usuario

- **Estado inicial**: El producto se crea en modo borrador (`draft`), para su posterior publicación.
- **Límite de catálogo (30 productos)**: No bloquea la creación; genera una advertencia en la respuesta indicando que se ha alcanzado o superado el umbral recomendado.
- **Swagger**: Interfaz disponible en `/api/v1/docs/`.
