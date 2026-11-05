from django.core.management.base import BaseCommand

from apps.notifications.services import retry_failed_notifications


class Command(BaseCommand):
    help = "Reintenta los correos transaccionales fallidos (programar cada minuto)."

    def handle(self, *args, **options):
        count = retry_failed_notifications()
        self.stdout.write(f"Correos reintentados: {count}")
