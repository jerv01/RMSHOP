# Panel RM Shop — HU-33 a HU-37

Implementación de frontend sobre los endpoints actuales, sin cambios de backend ni dependencias nuevas.

## Uso

1. Ingresar con una cuenta de Clerk con rol `admin` en `/admin/ingresar`.
2. Abrir `/admin/productos` y elegir **Nuevo producto**.
3. Completar datos y categoría. El resultado se guarda como borrador; conservar el ID mostrado.
4. En la edición, subir hasta tres fotos, indicar texto alternativo y ordenar con las flechas.
5. Agregar una variante o generar colores por tallas, separados por comas. Se crean con stock cero.
6. Abrir **Gestionar inventario**, seleccionar la variante y elegir **Agregar stock** (por defecto) o **Retirar stock**. Ingresar siempre una cantidad entera positiva y su motivo. Los retiros requieren confirmación y no pueden superar las existencias; se envían como `delta` negativo al mismo endpoint.
7. Verificar el stock actualizado y el historial con administrador y fecha (hora de Colombia).
8. Volver al producto para editar y publicar. Esta interfaz exige al menos una foto para publicar.
9. Archivar mediante confirmación. El servidor conserva el producto con estado `archived`.

La búsqueda por ID permite recuperar productos después de recargar. La lista **Creados durante esta sesión** vive solo en memoria, se borra al recargar/cambiar de cuenta y no representa todo el catálogo. Las consultas de TanStack Query se separan por usuario.

## Categorías temporales

`src/features/admin/products/config.ts` centraliza los IDs esperados de las cuatro categorías iniciales. La migración `0002_seed_categories` usa `get_or_create` **sin asignar PKs**, de modo que 1–4 solo es la correspondencia esperada en una base nueva. El formulario muestra los nombres y permite indicar el ID real; la API valida su existencia. Un endpoint de categorías permitirá reemplazar esta solución sin cambiar el resto del formulario.

## Solicitudes para backend

### Prioridad alta

- **Proteger historial al eliminar variantes.** Actualmente `StockMovement.variant` usa `CASCADE`: borrar una variante con stock cero borra su auditoría. Bloquear la eliminación cuando tenga movimientos, con una validación transaccional, y conservar los registros. El frontend oculta la acción si detecta historial y vuelve a consultar historial/stock antes de eliminar, pero no puede garantizar la protección frente a operaciones concurrentes.
- **Listado administrativo:** agregar `GET /api/v1/admin/products`, incluyendo borradores y archivados, con campos básicos y categoría. Para el MVP basta una lista pequeña; paginación no es indispensable.
- **Categorías:** agregar un endpoint de consulta que devuelva `id`, `name` y `slug`; no depender de PKs asumidas en el cliente.
- **Publicación:** exigir entre una y tres imágenes al pasar a `published` y evitar retirar la última foto de un producto publicado. Hoy el frontend lo restringe, pero las llamadas directas a la API pueden omitir la regla.
- **Precio anterior:** diferenciar un campo omitido de `previous_price: null` en edición. El primero conserva el valor y el segundo debería borrarlo. Mientras tanto, el frontend permite cambiarlo pero bloquea vaciarlo cuando ya existe.

### Prioridad media / antes del despliegue

- Devolver `404` al eliminar una imagen o variante inexistente o perteneciente a otro producto; los `.get()` de los servicios actualmente pueden producir `500`.
- Validar `image_ids` sin duplicados al reordenar; la igualdad de conjuntos actual no garantiza una permutación válida.
- Conectar almacenamiento persistente de fotografías y su entrega en producción. Actualmente se usa `FileSystemStorage`, y Django solo sirve `/media/` en desarrollo.
- Permitir actualizar `alt_text` de una foto existente. Actualmente solo se define al subirla.
- Asegurar que todo ingreso de stock inicial genere auditoría si se mantiene `stock_quantity` en la creación de variantes. Este frontend evita ese camino creando siempre con cero.
- Aplicar protección por reservas activas cuando se implemente ese dominio; hoy la eliminación solo comprueba stock.
- Validar el máximo de stock admitido por la columna de PostgreSQL en el servicio de ajustes.

### Posterior al MVP

- Consulta global de inventario, edición de atributos de variantes y catálogo público conectado. Estas capacidades no existen hoy; no se simulan desde este panel.

## Verificación con Docker

Desde la raíz del repositorio, con Docker Desktop iniciado y los `.env` ya configurados:

```powershell
docker compose up --build -d
docker compose exec backend python manage.py migrate
docker compose exec frontend pnpm lint
docker compose exec frontend pnpm typecheck
docker compose exec frontend pnpm test --run
docker compose exec frontend pnpm build
```

`migrate` aplica las migraciones existentes; no requiere modificar código del backend ni reiniciar la base. No ejecutar `down -v`.

Abrir `http://localhost:5173/admin/productos`. Clerk debe incluir el rol administrador en el token; la protección real la realiza la API. Si el volumen de dependencias del frontend está obsoleto, reconstruirlo con `docker compose up --build -V frontend` sin eliminar el volumen de PostgreSQL.

## Prueba manual del MVP

- Crear un producto sin precio anterior y comprobar que queda en borrador con ID visible.
- Probar un precio vacío, negativo y decimal; verificar que no se guarda y que los campos válidos se conservan.
- Consultar ese ID, editar precio/material y volver a consultar para confirmar persistencia.
- Si tiene precio anterior, intentar vaciarlo y comprobar el aviso sin enviar `null`.
- Subir JPG/PNG/WebP, verificar vista previa y foto guardada; rechazar archivos mayores a 5 MB o de otro formato. Alcanzar tres fotos y comprobar el límite.
- Reordenar y recargar; eliminar una foto cancelando primero y confirmando después.
- Publicar sin fotos debe mostrar validación; con una foto debe permitir guardar.
- Crear Negro/M; repetir `negro/m` debe bloquearse. Generar dos colores por dos tallas y comprobar que no duplica las existentes.
- Eliminar una variante sin stock/historial. Una variante con historial debe conservarse.
- Registrar dos unidades, comprobar stock, motivo, administrador y fecha en historial; cero/negativos/decimales deben rechazarse.
- Con diez unidades disponibles, elegir **Retirar stock**, indicar tres y confirmar: el stock debe quedar en siete y el historial debe mostrar `-3`, conservando los ingresos anteriores. Cancelar un retiro no debe enviar el ajuste; intentar retirar once debe bloquearse. Retirar las diez unidades debe dejar la variante agotada.
- Archivar cancelando primero, confirmar después y consultar el ID para verificar `archived`.
- Recargar y comprobar que la lista de sesión desaparece, aunque el producto sigue accesible por ID.
- Probar vista de 360 px y teclado: foco visible, campos con etiqueta, mensajes y botones accesibles.

Las pruebas automatizadas usan dobles de la API para validar los contratos y flujos del frontend. No sustituyen una prueba con Clerk, Django y PostgreSQL activos.

## Estado de verificación en esta entrega

- Se añadieron pruebas de creación, validación, edición, publicación sin fotos, confirmación de archivado, carga multipart, orden de fotos, variantes y protección del historial, e ingreso de stock con actualización de historial.
- Con Docker Desktop disponible, se ejecutaron los comandos del README mediante `docker compose run --rm frontend pnpm ...`: lint, typecheck, las 46 pruebas de ocho archivos y build pasaron.
- Los ajustes de inventario incluyen pruebas de retiro parcial y total, confirmación/cancelación, stock insuficiente, cantidades inválidas para ambas operaciones, errores del servidor y conservación del historial. Se comprobó además la ausencia del aviso retirado del formulario, manteniendo las categorías existentes.
- La primera ejecución detectó un tipo de retorno incompatible en la creación individual/masiva de variantes y una diferencia al conservar la escritura de colores duplicados. Se corrigieron ambos puntos y se repitieron las verificaciones correctamente.
- Build mostró advertencias no bloqueantes de comentarios de Zod y tamaño del bundle principal. No se cambiaron dependencias, manifiestos ni lockfiles.
- La integración real con API/Clerk y la revisión visual en navegador siguen pendientes; las pruebas automatizadas usan dobles de la API.
- El código se formateó con Prettier y se comprobó con `git diff --check`.
