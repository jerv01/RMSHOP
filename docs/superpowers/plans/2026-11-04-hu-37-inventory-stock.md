# Plan de Implementación: HU-37 Registro y Aumento Manual de Stock por Variante

## Tareas

- [x] **Tarea 1: Modelo `StockMovement` y Migración de BD**
  - Implementar el modelo `StockMovement` en `apps/backend/apps/inventory/models.py`.
  - Crear pruebas unitarias del modelo en `apps/backend/apps/inventory/tests/test_models.py`.
  - Generar y aplicar migraciones (`makemigrations inventory`, `migrate inventory`).
  - Ejecutar verificación de pruebas de modelo.

- [x] **Tarea 2: Servicio de Negocio `adjust_variant_stock`**
  - Implementar `adjust_variant_stock` en `apps/backend/apps/inventory/services.py` con `transaction.atomic` y `select_for_update()`.
  - Validar delta positivo, delta negativo permitido siempre que el resultante sea >= 0, y rechazo de stock negativo o delta cero.
  - Crear pruebas unitarias del servicio en `apps/backend/apps/inventory/tests/test_services.py`.
  - Ejecutar pruebas con pytest.

- [x] **Tarea 3: Serializadores, Vistas REST y Rutas**
  - Crear `StockAdjustmentInputSerializer`, `StockMovementSerializer`, `StockAdjustmentResponseSerializer` en `apps/backend/apps/inventory/serializers.py`.
  - Crear `AdminVariantStockAdjustmentView` y `AdminVariantStockMovementsListView` en `apps/backend/apps/inventory/views.py`.
  - Configurar rutas en `apps/backend/apps/inventory/urls.py` e incluir en `apps/backend/config/urls.py`.
  - Crear pruebas de integración en `apps/backend/apps/inventory/tests/test_admin_stock.py` cubriendo:
    - AC-HU-37-1: Stock 3 + 2 = 5 con registro de movimiento y admin.
    - AC-HU-37-2: Rechazo con validación unificada para valores no numéricos o stock negativo.
    - AC-HU-37-3: Stock 0 aumentado pasa a disponible con stock actualizado.
    - Control de permisos: solo administradores (`IsRMAdmin`).
    - Consulta de historial de movimientos.

- [x] **Tarea 4: Verificación Integral y Documentación**
  - Ejecutar suite completa de backend (`pytest`).
  - Ejecutar linter y formatter (`ruff check .`, `ruff format --check .`).
  - Actualizar `RMSHOP/docs/backlog.md` (marcar HU-37 como `[BACKEND LISTO]`).
  - Actualizar `.agents/skills/index-proyecto/SKILL.md` con los detalles de `apps.inventory`.
  - Notificar al usuario con reporte estilo Ponytail.
