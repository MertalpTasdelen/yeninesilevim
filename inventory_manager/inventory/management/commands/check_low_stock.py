from django.core.management.base import BaseCommand

from inventory.notifications import LowStockNotificationService


class Command(BaseCommand):
    help = "Send web push notifications for products at or below the low-stock threshold."

    def add_arguments(self, parser):
        parser.add_argument(
            "--target-url",
            dest="target_url",
            help="Optional absolute URL to include in the push notification payload.",
        )

    def handle(self, *args, **options):
        service = LowStockNotificationService()
        notified_products = service.run_scheduled_check(target_url=options.get("target_url"))
        if notified_products:
            ids = ", ".join(str(product.id) for product in notified_products)
            self.stdout.write(self.style.SUCCESS(f"Low stock notifications sent for product IDs: {ids}"))
        else:
            self.stdout.write("No low stock notifications were sent.")

