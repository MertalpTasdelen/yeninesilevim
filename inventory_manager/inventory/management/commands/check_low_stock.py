from django.core.management.base import BaseCommand

from inventory.notifications import LowStockNotificationService, send_low_quantity_purchase_items_telegram_alert
from inventory.models import PurchaseItem


class Command(BaseCommand):
    help = "Send web push and Telegram notifications for products at or below the low-stock threshold."

    def add_arguments(self, parser):
        parser.add_argument(
            "--target-url",
            dest="target_url",
            help="Optional absolute URL to include in the push notification payload.",
        )
        parser.add_argument(
            "--telegram-only",
            action="store_true",
            help="Send only Telegram notifications, skip web push",
        )
        parser.add_argument(
            "--web-push-only",
            action="store_true",
            help="Send only web push notifications, skip Telegram",
        )

    def handle(self, *args, **options):
        service = LowStockNotificationService()
        telegram_only = options.get("telegram_only", False)
        web_push_only = options.get("web_push_only", False)
        
        # Web Push Notifications
        notified_products = []
        if not telegram_only:
            notified_products = service.run_scheduled_check(target_url=options.get("target_url"))
            if notified_products:
                ids = ", ".join(str(product.id) for product in notified_products)
                self.stdout.write(self.style.SUCCESS(f"Web push notifications sent for product IDs: {ids}"))
            else:
                self.stdout.write("No web push notifications were sent.")
        
        # Telegram Notifications
        if not web_push_only:
            # Fetch low quantity purchase items (excluding archived)
            low_quantity_items = list(
                PurchaseItem.objects.filter(
                    quantity__lte=3,
                    is_archived=False
                ).order_by('quantity', 'name')
            )
            
            if low_quantity_items:
                telegram_success = send_low_quantity_purchase_items_telegram_alert(low_quantity_items)
                if telegram_success:
                    item_names = ", ".join(i.name[:30] for i in low_quantity_items[:5])
                    if len(low_quantity_items) > 5:
                        item_names += f" (+{len(low_quantity_items) - 5} more)"
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Telegram notification sent for {len(low_quantity_items)} purchase items: {item_names}")
                    )
                else:
                    self.stdout.write(self.style.WARNING("⚠️ Failed to send purchase items Telegram notification"))
            else:
                self.stdout.write("No low quantity purchase items found for Telegram notification.")
