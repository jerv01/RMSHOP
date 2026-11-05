# Plan de Implementación: HU-35 Carga y Gestión de Imágenes de Productos

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend la carga, optimización (WebP/Pillow), reordenamiento y eliminación de imágenes de productos (1 a 3 fotos por prenda) con texto alternativo para accesibilidad (HU-61), almacenamiento local desacoplado y endpoints protegidos para administradores.

**Architecture:** Capas desacopladas en Django/DRF: modelo `ProductImage` con restricciones de base de datos; servicio de procesamiento en memoria con Pillow para redimensionar (máx 1600 px) y convertir a WebP con calidad 85; servicios de negocio para subida con límite de 3 imágenes, eliminación con purga física de archivo y recompactación de posiciones; endpoints REST anidados bajo `/api/v1/admin/products/{id}/images` con permisos `IsRMAdmin` y Swagger UI.

**Tech Stack:** Python 3.14, Django 5.2, Django REST Framework 3.16, Pillow, drf-spectacular, PostgreSQL.

**Spec:** [`RMSHOP/docs/superpowers/specs/2026-11-04-hu-35-product-images-design.md`](file:///c:/Users/elkin/Documentos/Universidad/2026-II/Gestion/RMSHOP/docs/superpowers/specs/2026-11-04-hu-35-product-images-design.md)

## Global Constraints

- Monorepo `RMSHOP/`: Backend en `apps/backend/`.
- No modificar frontend en esta historia (especificación de contrato documentada para futura fase UI).
- Almacenamiento local mediante `FileSystemStorage` sobre `MEDIA_ROOT`, dejando `STORAGES["default"]` extensible a Supabase Storage S3.
- Formato de error DRF unificado: `{"code": "...", "message": "...", "fields": {...}}`.
- Límite estricto de 3 fotos por producto; posiciones 1 a 3 únicas (`unique_product_image_position`).
- Todo cambio de código debe pasar `ruff check .`, `ruff format --check .` y la suite de `pytest`.

## Review Focus

1. **Archivo no imagen o corrupto:** El servicio rechaza con `400 Bad Request` y `{fields: {"image": "..."}}` sin romper el servidor ni dejar archivos huérfanos.
2. **Archivo superior a 5 MB:** Rechazado antes de procesar completamente con mensaje explicativo.
3. **Límite de 3 imágenes (AC-HU-35-3):** Si un producto ya tiene 3 imágenes y se intenta subir otra, responde `400 Bad Request` informando que se alcanzó el límite.
4. **Purga física al eliminar:** Al borrar una imagen (`DELETE`), se elimina el archivo en disco además de la fila en BD, y las posiciones restantes se recompactan (ej. si quedan 1 y 3, pasan a 1 y 2).
5. **Permisos y seguridad:** Solo usuarios autenticados con rol `admin` (`IsRMAdmin`) pueden operar los endpoints; un usuario cliente o visitante anónimo recibe 403 o 401.

---

### Task 1: Configuración de Medios y Almacenamiento Local (Settings & URLs)

**Files:**
- Modify: `apps/backend/config/settings/base.py`
- Modify: `apps/backend/config/urls.py`
- Test: `apps/backend/apps/core/tests/test_media_settings.py`

**Interfaces:**
- Produces: `settings.MEDIA_URL = "/media/"`, `settings.MEDIA_ROOT = BASE_DIR / "media"`, `STORAGES["default"]` configurado.

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/apps/core/tests/test_media_settings.py
from django.conf import settings


def test_media_settings_configured():
    assert settings.MEDIA_URL == "/media/"
    assert settings.MEDIA_ROOT.name == "media"
    assert "default" in settings.STORAGES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/core/tests/test_media_settings.py`  
Expected: FAIL (AttributeError: 'Settings' object has no attribute 'MEDIA_URL')

- [ ] **Step 3: Implement settings and URL serving in `base.py` and `urls.py`**

In `apps/backend/config/settings/base.py`:
```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": env("DEFAULT_FILE_STORAGE_BACKEND", "django.core.files.storage.FileSystemStorage"),
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

In `apps/backend/config/urls.py`:
```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/core/tests/test_media_settings.py`  
Expected: PASS

- [ ] **Step 5: Format and lint**

Run: `cd RMSHOP; docker compose run --rm backend ruff check apps/core/tests/test_media_settings.py config/`

---

### Task 2: Modelo `ProductImage` y Migración de Base de Datos

**Files:**
- Modify: `apps/backend/apps/catalog/models.py`
- Create: `apps/backend/apps/catalog/migrations/0003_product_images.py`
- Modify: `apps/backend/apps/catalog/tests/test_models.py`

**Interfaces:**
- Produces: `ProductImage` con campos `product`, `image`, `alt_text`, `position`, `created_at` y restricciones `unique(product, position)` y `1 <= position <= 3`.

- [ ] **Step 1: Write the failing test for `ProductImage`**

In `apps/backend/apps/catalog/tests/test_models.py`:
```python
import pytest
from django.db import IntegrityError
from apps.catalog.models import Category, Product, ProductImage

@pytest.mark.django_db
def test_product_image_creation_and_constraints():
    cat = Category.objects.create(name="Blusas", slug="blusas")
    product = Product.objects.create(
        name="Blusa Lino",
        slug="blusa-lino",
        description="Desc",
        price=75000,
        category=cat,
    )
    img1 = ProductImage.objects.create(
        product=product,
        image="products/test.webp",
        alt_text="Blusa de lino blanca",
        position=1,
    )
    assert img1.id is not None
    assert img1.position == 1
    assert str(img1) == f"Imagen {img1.position} de {product.name}"

    # Unique constraint (product, position)
    with pytest.raises(IntegrityError):
        ProductImage.objects.create(
            product=product,
            image="products/test2.webp",
            alt_text="Otra foto",
            position=1,
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_models.py::test_product_image_creation_and_constraints`  
Expected: FAIL (cannot import name 'ProductImage')

- [ ] **Step 3: Define `ProductImage` in `apps/catalog/models.py` and run migrations**

In `apps/backend/apps/catalog/models.py`:
```python
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(max_length=255)
    position = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_images"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "position"],
                name="unique_product_image_position",
            ),
            models.CheckConstraint(
                check=models.Q(position__gte=1) & models.Q(position__lte=3),
                name="check_product_image_position_range",
            ),
        ]

    def __str__(self) -> str:
        return f"Imagen {self.position} de {self.product.name}"
```

Run migration:
`cd RMSHOP; docker compose run --rm backend python manage.py makemigrations catalog`

- [ ] **Step 4: Run test to verify it passes**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_models.py`  
Expected: PASS

- [ ] **Step 5: Format and lint**

Run: `cd RMSHOP; docker compose run --rm backend ruff check apps/catalog/models.py`

---

### Task 3: Servicio de Optimización de Imágenes con Pillow (`process_image`)

**Files:**
- Create: `apps/backend/apps/catalog/tests/test_image_processing.py`
- Modify: `apps/backend/apps/catalog/services.py`

**Interfaces:**
- Produces: `process_image(file: IO[bytes] | UploadedFile) -> ContentFile`

- [ ] **Step 1: Write the failing tests for image processing**

In `apps/backend/apps/catalog/tests/test_image_processing.py`:
```python
import io
import pytest
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.catalog.services import process_image

def _create_image_file(name: str, format: str = "JPEG", size=(2000, 1000), color="blue"):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{format.lower()}")

def test_process_image_resizes_and_converts_to_webp():
    uploaded = _create_image_file("foto.jpg", format="JPEG", size=(2000, 1000))
    result = process_image(uploaded)

    assert result.name.endswith(".webp")
    # Verify image dimensions and format with Pillow
    img = Image.open(result)
    assert img.format == "WEBP"
    assert max(img.width, img.height) == 1600
    assert img.width == 1600
    assert img.height == 800

def test_process_image_rejects_corrupted_or_non_image():
    uploaded = SimpleUploadedFile("fake.txt", b"not an image", content_type="text/plain")
    with pytest.raises(ValidationError) as exc:
        process_image(uploaded)
    assert "image" in exc.value.message_dict

def test_process_image_rejects_oversized_file():
    # 6 MB fake file
    big_data = b"0" * (6 * 1024 * 1024)
    uploaded = SimpleUploadedFile("big.jpg", big_data, content_type="image/jpeg")
    with pytest.raises(ValidationError) as exc:
        process_image(uploaded)
    assert "image" in exc.value.message_dict
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_image_processing.py`  
Expected: FAIL (cannot import name 'process_image')

- [ ] **Step 3: Implement `process_image` in `apps/catalog/services.py`**

In `apps/backend/apps/catalog/services.py`:
```python
import io
import uuid
from PIL import Image, ImageOps
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_DIMENSION = 1600
WEBP_QUALITY = 85
ALLOWED_IMAGE_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}

def process_image(file) -> ContentFile:
    if getattr(file, "size", len(file)) > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError({"image": "La imagen no debe superar los 5 MB."})

    try:
        file.seek(0)
    except (AttributeError, io.UnsupportedOperation):
        pass

    try:
        img = Image.open(file)
        img.verify()
        # verify() closes/empties the file pointer in some PIL versions; reopen
        file.seek(0)
        img = Image.open(file)
    except Exception:
        raise ValidationError(
            {"image": "El archivo debe ser una imagen válida (JPG, PNG o WebP)."}
        )

    if (img.format or "").upper() not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(
            {"image": "Formato no permitido. Solo se aceptan archivos JPG, PNG o WebP."}
        )

    # Transpose according to EXIF orientation if present
    img = ImageOps.exif_transpose(img)

    # Resize if largest side exceeds 1600 px
    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIMENSION:
        if w >= h:
            new_w = MAX_IMAGE_DIMENSION
            new_h = int(round((h * MAX_IMAGE_DIMENSION) / w))
        else:
            new_h = MAX_IMAGE_DIMENSION
            new_w = int(round((w * MAX_IMAGE_DIMENSION) / h))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Convert modes to RGB / RGBA
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=WEBP_QUALITY, optimize=True)
    filename = f"{uuid.uuid4().hex}.webp"
    return ContentFile(output.getvalue(), name=filename)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_image_processing.py`  
Expected: PASS

- [ ] **Step 5: Format and lint**

Run: `cd RMSHOP; docker compose run --rm backend ruff check apps/catalog/services.py`

---

### Task 4: Servicios de Negocio para Imágenes (`upload_product_image`, `delete_product_image`, `reorder_product_images`)

**Files:**
- Modify: `apps/backend/apps/catalog/services.py`
- Modify: `apps/backend/apps/catalog/tests/test_services.py`

**Interfaces:**
- Produces:
  - `upload_product_image(*, product_id: int, file, alt_text: str = "", position: int | None = None) -> ProductImage`
  - `delete_product_image(*, product_id: int, image_id: int) -> None`
  - `reorder_product_images(*, product_id: int, image_ids: list[int]) -> list[ProductImage]`

- [ ] **Step 1: Write failing tests for image services**

In `apps/backend/apps/catalog/tests/test_services.py`:
```python
def test_upload_product_image_happy_path(seeded_category):
    product = create_product(name="Vestido Seda", description="...", price=120000, category_id=seeded_category.id)
    img_file = _create_image_file("vestido.png", format="PNG")
    img = upload_product_image(product_id=product.id, file=img_file, alt_text="Vestido vista frontal")
    assert img.position == 1
    assert img.alt_text == "Vestido vista frontal"
    assert img.image.name.endswith(".webp")

def test_upload_product_image_fallback_alt_text(seeded_category):
    product = create_product(name="Pantalón Casual", description="...", price=90000, category_id=seeded_category.id)
    img = upload_product_image(product_id=product.id, file=_create_image_file("p.jpg"), alt_text="")
    assert img.alt_text == product.name

def test_upload_product_image_limit_3_exceeded(seeded_category):
    product = create_product(name="Top Crop", description="...", price=45000, category_id=seeded_category.id)
    for _ in range(3):
        upload_product_image(product_id=product.id, file=_create_image_file("f.jpg"))
    
    with pytest.raises(ValidationError) as exc:
        upload_product_image(product_id=product.id, file=_create_image_file("f4.jpg"))
    assert "image" in exc.value.message_dict

def test_delete_product_image_recompacts_positions(seeded_category):
    product = create_product(name="Falda Larga", description="...", price=80000, category_id=seeded_category.id)
    img1 = upload_product_image(product_id=product.id, file=_create_image_file("f1.jpg"))
    img2 = upload_product_image(product_id=product.id, file=_create_image_file("f2.jpg"))
    img3 = upload_product_image(product_id=product.id, file=_create_image_file("f3.jpg"))

    delete_product_image(product_id=product.id, image_id=img2.id)
    remaining = list(product.images.order_by("position"))
    assert len(remaining) == 2
    assert remaining[0].id == img1.id and remaining[0].position == 1
    assert remaining[1].id == img3.id and remaining[1].position == 2

def test_reorder_product_images(seeded_category):
    product = create_product(name="Buzo Oversize", description="...", price=95000, category_id=seeded_category.id)
    img1 = upload_product_image(product_id=product.id, file=_create_image_file("f1.jpg"))
    img2 = upload_product_image(product_id=product.id, file=_create_image_file("f2.jpg"))

    reordered = reorder_product_images(product_id=product.id, image_ids=[img2.id, img1.id])
    assert reordered[0].id == img2.id and reordered[0].position == 1
    assert reordered[1].id == img1.id and reordered[1].position == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_services.py`  
Expected: FAIL (cannot import name 'upload_product_image')

- [ ] **Step 3: Implement image services in `apps/catalog/services.py`**

Implement `upload_product_image`, `delete_product_image`, and `reorder_product_images` with atomic transactions, storage file deletion, next-position allocation, and position recompacting.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_services.py`  
Expected: PASS

- [ ] **Step 5: Format and lint**

Run: `cd RMSHOP; docker compose run --rm backend ruff check apps/catalog/services.py`

---

### Task 5: Serializadores y Vistas REST para Gestión de Imágenes

**Files:**
- Modify: `apps/backend/apps/catalog/serializers.py`
- Modify: `apps/backend/apps/catalog/views.py`
- Modify: `apps/backend/apps/catalog/urls.py`
- Create: `apps/backend/apps/catalog/tests/test_admin_product_images.py`

**Interfaces:**
- Endpoints:
  - `GET /api/v1/admin/products/{product_id}/images`
  - `POST /api/v1/admin/products/{product_id}/images`
  - `DELETE /api/v1/admin/products/{product_id}/images/{image_id}`
  - `PATCH /api/v1/admin/products/{product_id}/images/reorder`

- [ ] **Step 1: Write integration tests for admin image endpoints**

In `apps/backend/apps/catalog/tests/test_admin_product_images.py`:
- Test GET list of product images returns 200.
- Test POST image upload (`multipart/form-data`) with valid image returns 201.
- Test POST image when already 3 images returns 400.
- Test POST image with invalid file returns 400.
- Test DELETE image returns 204.
- Test PATCH reorder returns 200 with new order.
- Test 401 unauthenticated and 403 non-admin.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_admin_product_images.py`  
Expected: FAIL (404 or missing endpoints)

- [ ] **Step 3: Implement serializers, views and routes**

In `serializers.py`:
- `ProductImageSerializer`
- `ProductImageUploadSerializer`
- `ProductImageReorderSerializer`

In `views.py`:
- `AdminProductImageListCreateView`
- `AdminProductImageDetailView`
- `AdminProductImageReorderView`
- Decorate with `@extend_schema` for OpenAPI documentation in Swagger UI.

In `urls.py`:
- Map paths under `admin/products/<int:product_id>/images/`

- [ ] **Step 4: Run test to verify it passes**

Run: `cd RMSHOP; docker compose run --rm backend pytest apps/catalog/tests/test_admin_product_images.py`  
Expected: PASS

- [ ] **Step 5: Format and lint**

Run: `cd RMSHOP; docker compose run --rm backend ruff check apps/catalog/`

---

### Task 6: Verificación Integral, Formato y Actualización de Documentación

**Files:**
- Modify: `RMSHOP/docs/backlog.md`
- Modify: `.agents/skills/index-proyecto/SKILL.md`

- [ ] **Step 1: Run full backend test suite**

Run: `cd RMSHOP; docker compose run --rm backend pytest`  
Expected: All tests PASS (>75 tests).

- [ ] **Step 2: Run Ruff check and format check**

Run: `cd RMSHOP; docker compose run --rm backend ruff check .`  
Run: `cd RMSHOP; docker compose run --rm backend ruff format --check .`  
Expected: 0 errors.

- [ ] **Step 3: Update documentation in backlog.md and index-proyecto**

Mark HU-35 as `[BACKEND LISTO]` in `RMSHOP/docs/backlog.md`.
Update `Catálogo de Productos` in `.agents/skills/index-proyecto/SKILL.md` noting the completion of HU-35 backend.
