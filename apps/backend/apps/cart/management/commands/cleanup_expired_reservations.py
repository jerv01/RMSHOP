from django.core.management.base import BaseCommand

from apps.cart.services import release_expired_reservations


class Command(BaseCommand):
    help = "Libera y limpia reservas de inventario expiradas (HU-18)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--remove-items",
            action="store_true",
            help="Elimina también los CartItems asociados a reservas expiradas",
        )

    def handle(self, *args, **options):
        delete_cart_items = options.get("remove_items", False)
        count = release_expired_reservations(delete_cart_items=delete_cart_items)
        self.stdout.write(self.style.SUCCESS(f"Se liberaron {count} reservas expiradas."))
