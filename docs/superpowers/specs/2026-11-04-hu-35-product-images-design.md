# Diseño Técnico: HU-35 Carga y Gestión de Imágenes de Productos

**Fecha:** 2026-11-04  
**Historia de Usuario:** HU-35 (Épica 7: Gestión de productos)  
**Dependencias:** HU-33, HU-11, HU-61 (Texto alternativo)  
**Alcance:** Exclusivo Backend  

---

## 1. Intención y Propósito

Permitir que el Administrador cargue, ordene y elimine fotografías para cada prenda del catálogo (1 a 3 fotos por producto), asegurando que cada imagen cuente con texto alternativo (`alt_text`) para accesibilidad web (HU-61). El sistema debe optimizar automáticamente los archivos cargados (conversión a WebP, compresión de calidad 85 y reescalado de lado mayor a 1600 px) para garantizar tiempos de carga ágiles en dispositivos móviles y escritorio.

---

## 2. Objetivos, No-Objetivos y Restricciones

### Objetivos
- **Modelo de datos `ProductImage` (`apps.catalog.models`):**
  - Vinculado a `Product` mediante clave foránea con borrado en cascada.
  - Almacena archivo de imagen (`ImageField`), texto alternativo (`alt_text`) y posición ordinal (`position` de 1 a 3).
  - Restricción de base de datos de unicidad `unique(product, position)` y chequeo `1 <= position <= 3`.
- **Servicios de negocio (`apps.catalog.services`):**
  - `process_image(file)`: valida que el archivo sea una imagen real (JPEG, PNG o WebP) y que su tamaño no supere 5 MB. Re-escala proporcionalmente si el lado mayor supera 1600 px y convierte a formato WebP con calidad 85 usando Pillow.
  - `upload_product_image(*, product_id, file, alt_text, position=None)`:
    - Valida que el producto no exceda el límite máximo de 3 imágenes (AC-HU-35-3).
    - Asigna automáticamente la siguiente posición disponible (1..3) si no se especifica.
    - Asigna fallback a `alt_text` con el nombre del producto si llega vacío (cumpliendo AC-HU-61-2).
  - `delete_product_image(*, product_id, image_id)`: elimina el registro de base de datos, purga el archivo físico del storage y recompacta las posiciones restantes (1..N) para evitar huecos.
  - `reorder_product_images(*, product_id, image_ids)`: actualiza atómicamente el orden (posiciones 1, 2, 3) de las imágenes existentes.
- **Configuración de almacenamiento de medios:**
  - `MEDIA_URL = "/media/"` y `MEDIA_ROOT = BASE_DIR / "media"` en `config.settings.base`.
  - Configuración desacoplada en `STORAGES["default"]` mediante `FileSystemStorage` para entorno local y testing, lista para soportar `storages.backends.s3boto3.S3Boto3Storage` (Supabase S3) al definir variables de entorno en producción.
  - Servir archivos de medios en desarrollo en `urls.py` cuando `DEBUG=True`.
- **Endpoints REST (`apps.catalog.views`):**
  - `GET /api/v1/admin/products/{id}/images`: lista las fotos del producto ordenadas por posición.
  - `POST /api/v1/admin/products/{id}/images`: carga una imagen (`multipart/form-data`) y retorna la imagen procesada (201 Created).
  - `DELETE /api/v1/admin/products/{id}/images/{image_id}`: elimina la foto especificada (204 No Content).
  - `PATCH /api/v1/admin/products/{id}/images/reorder`: reordena las posiciones enviando la lista ordenada de IDs (200 OK).
- **Seguridad y Documentación:**
  - Restringido a administradores autenticados mediante `IsRMAdmin`.
  - Documentado en Swagger UI OpenAPI 3 (`/api/v1/docs/`).
- **Pruebas automatizadas:**
  - Pruebas unitarias de procesamiento de imágenes con Pillow.
  - Pruebas de servicio y de vistas (validación de formatos, tamaño, límite de 3 fotos, eliminación, reordenamiento y permisos).

### No-Objetivos
- Implementación de interfaz de usuario en React (diferida para la etapa de frontend).
- Conexión forzada en local al bucket remoto de Supabase (se utiliza almacenamiento local para agilidad y aislamiento en testing).
- Edición de imágenes o filtros avanzados en el backend más allá de la optimización estándar definida.

### Restricciones
- Formato de salida mandatorio: WebP (calidad 85, máx 1600 px en lado mayor).
- Límite estricto de 1 a 3 imágenes por producto.
- Formatos de entrada permitidos: JPEG, PNG, WebP. Límite de tamaño: 5 MB.
- Respuestas de error estandarizadas en `{code, message, fields}`.

---

## 3. Enfoques Técnicos Evaluados

1. **Enfoque A: Endpoints anidados dedicados por producto con servicio de optimización (Seleccionado)**
   - Endpoints RESTful bajo `/api/v1/admin/products/{id}/images`.
   - Carga atómica vía `multipart/form-data` sin mezclar con los atributos textuales del producto.
   - Permite subir, reordenar y eliminar fotos individualmente con validaciones aisladas.
2. **Enfoque B: Upload embebido en `/admin/products/{id}` (Descartado)**
   - Complejiza el contrato JSON y dificulta el manejo de errores atómicos en imágenes.
3. **Enfoque C: Endpoint plano `/admin/images` (Descartado)**
   - Pierde el contexto jerárquico de pertenencia al producto y su orden de 1 a 3.

---

## 4. Decisiones de Diseño Acordadas

- **Almacenamiento:** `FileSystemStorage` en local y tests; abstracción `STORAGES["default"]` extensible a Supabase S3 vía variables de entorno.
- **Formato y optimización:** Conversión en memoria a WebP con Pillow previo a persistir el archivo.
- **Accesibilidad:** `alt_text` persistido por imagen con fallback al nombre del producto si viene vacío.
- **Límite:** 3 imágenes máximo por producto; superar este límite responde con código de error explicativo (`400 Bad Request`).


---

## 5. Especificación de Contrato para el Frontend

Cuando se construya la interfaz de usuario en React (`apps/frontend/src/features/admin/products/`), el equipo o agente encargado deberá implementar el gestor de imágenes siguiendo este contrato:

### 5.1 Endpoints y Contratos HTTP

Todos los endpoints requieren cabecera `Authorization: Bearer <clerk_token>` con rol de administrador.

#### 1. Listar imágenes de un producto
- **Método y Ruta:** `GET /api/v1/admin/products/{product_id}/images`
- **Respuesta exitosa (200 OK):**
  ```json
  [
    {
      "id": 12,
      "product_id": 4,
      "image_url": "/media/products/2026/11/a9d8c.webp",
      "alt_text": "Camiseta Básica de Algodón Negra vista frontal",
      "position": 1,
      "created_at": "2026-11-04T20:30:00Z"
    },
    {
      "id": 13,
      "product_id": 4,
      "image_url": "/media/products/2026/11/b3f1e.webp",
      "alt_text": "Camiseta Básica detalle de costura",
      "position": 2,
      "created_at": "2026-11-04T20:32:00Z"
    }
  ]
  ```

#### 2. Subir nueva imagen
- **Método y Ruta:** `POST /api/v1/admin/products/{product_id}/images`
- **Cabeceras:** `Content-Type: multipart/form-data`
- **Cuerpo (`FormData`):**
  - `image`: Archivo binario (JPG, PNG o WebP, $\le$ 5 MB).
  - `alt_text` *(opcional)*: Texto descriptivo de la prenda para accesibilidad (si se omite o va vacío, el backend asigna el nombre del producto).
  - `position` *(opcional)*: Entero entre 1 y 3 (si se omite, se asigna la siguiente posición disponible).
- **Respuesta exitosa (201 Created):** Retorna el objeto de la imagen creada (mismo formato del listado).
- **Errores esperados:**
  - `400 Bad Request` si ya existen 3 imágenes:
    ```json
    {
      "code": "invalid_input",
      "message": "Datos de entrada inválidos.",
      "fields": {
        "image": "El producto ya tiene el máximo permitido de 3 fotografías."
      }
    }
    ```
  - `400 Bad Request` si el archivo no es imagen o excede 5 MB:
    ```json
    {
      "code": "invalid_input",
      "message": "Datos de entrada inválidos.",
      "fields": {
        "image": "El archivo debe ser una imagen válida (JPG, PNG o WebP) de hasta 5 MB."
      }
    }
    ```

#### 3. Eliminar imagen
- **Método y Ruta:** `DELETE /api/v1/admin/products/{product_id}/images/{image_id}`
- **Respuesta exitosa (204 No Content):** Cuerpo vacío. El backend purga el archivo físico y recompacta automáticamente las posiciones restantes (1..N).

#### 4. Reordenar posiciones de imágenes
- **Método y Ruta:** `PATCH /api/v1/admin/products/{product_id}/images/reorder`
- **Cabeceras:** `Content-Type: application/json`
- **Cuerpo:**
  ```json
  {
    "image_ids": [13, 12]
  }
  ```
- **Respuesta exitosa (200 OK):** Lista de imágenes reordenadas.

### 5.2 Directrices y Experiencia de Usuario (UI/UX) para el Frontend
- **Límite visible:** Mostrar indicador de cupos ocupados (ej. `2 / 3 fotos`). Deshabilitar el botón de subida cuando existan 3 fotos.
- **Previsualización y Drag & Drop:** Permitir arrastrar archivos o seleccionar desde explorador, con preview local inmediato antes o durante la carga.
- **Campo `alt_text` explícito:** Proveer un input con placeholder que sugiera describir la prenda (ej. *"Vista frontal sobre modelo"*). Informar al usuario que si lo deja vacío se utilizará el nombre del producto como valor predeterminado para lectores de pantalla.
- **Reordenamiento visual:** Permitir mover las tarjetas de fotos mediante botones de flecha o arrastre, enviando el nuevo orden a `/reorder`.
