from django.core.management.base import BaseCommand

from apps.core.services import run_scheduled_tasks


class Command(BaseCommand):
    help = "Libera reservas vencidas y cancela pedidos sin pago tras 30 minutos (HU-18, HU-24)."

    def handle(self, *args, **options):
        result = run_scheduled_tasks()
        self.stdout.write(
            f"Reservas liberadas: {result['released_reservations']} · "
            f"Pedidos cancelados: {result['cancelled_orders']}"
        )
