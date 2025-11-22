import logging
from datetime import timedelta
from typing import Iterable, List, Optional

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from webpush import send_group_notification

from .models import Product


logger = logging.getLogger(__name__)


class NotificationPayload:
    """Value object representing a push payload."""

    def __init__(self, head: str, body: str, icon: str, url: str):
        self.head = head
        self.body = body
        self.icon = icon
        self.url = url

    def as_dict(self) -> dict:
        return {
            "head": self.head,
            "body": self.body,
            "icon": self.icon,
            "url": self.url,
        }


class LowStockNotificationService:
    """Handles preparing and delivering low-stock push notifications."""

    def __init__(
        self,
        group_name: str = "low_stock",
        threshold: int = 3,
        cooldown_hours: int = 6,
        default_target_url: Optional[str] = None,
        icon_path: str = "/static/img/icons/icon-192x192.png",
    ) -> None:
        self.group_name = group_name
        self.threshold = threshold
        self.cooldown_hours = cooldown_hours
        self.icon_path = icon_path
        self.default_target_url = default_target_url or getattr(
            settings, "LOW_STOCK_NOTIFICATION_URL", reverse("product_list")
        )

    def fetch_low_stock_products(self) -> Iterable[Product]:
        return Product.objects.filter(stock__lte=self.threshold)

    def _is_allowed_to_notify(self, product: Product, now) -> bool:
        if product.low_stock_notified_at is None:
            return True
        return now - product.low_stock_notified_at >= timedelta(hours=self.cooldown_hours)

    def build_payload(self, product: Product, target_url: Optional[str] = None) -> NotificationPayload:
        resolved_url = target_url or self.default_target_url
        body = f"{product.name} ürününün stoğu {product.stock} adetin altına düştü."
        return NotificationPayload(
            head="Stok Uyarısı",
            body=body,
            icon=self.icon_path,
            url=resolved_url,
        )

    def mark_notified(self, product: Product, timestamp) -> None:
        product.low_stock_notified_at = timestamp
        product.save(update_fields=["low_stock_notified_at"])

    def send_payload(self, payload: NotificationPayload) -> None:
        send_group_notification(
            group_name=self.group_name,
            payload=payload.as_dict(),
            ttl=1000,
        )

    def notify_if_needed(
        self, product: Product, now=None, target_url: Optional[str] = None
    ) -> bool:
        now = now or timezone.now()
        if product.stock > self.threshold:
            return False
        if not self._is_allowed_to_notify(product, now):
            return False

        payload = self.build_payload(product, target_url=target_url)
        try:
            self.send_payload(payload)
            self.mark_notified(product, now)
            logger.info("Low stock notification sent", extra={"product_id": product.id})
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to send low stock notification",
                extra={"product_id": product.id, "error": str(exc)},
            )
        return False

    def notify_products(self, products: Iterable[Product], target_url: Optional[str] = None) -> List[Product]:
        now = timezone.now()
        notified: List[Product] = []
        for product in products:
            if self.notify_if_needed(product, now=now, target_url=target_url):
                notified.append(product)
        return notified

    def run_scheduled_check(self, target_url: Optional[str] = None) -> List[Product]:
        low_stock_products = self.fetch_low_stock_products()
        return self.notify_products(low_stock_products, target_url=target_url)

