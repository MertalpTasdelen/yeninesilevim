import logging
import json
import requests
from datetime import timedelta
from typing import Iterable, List, Optional

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Product, PurchaseItem


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
        cooldown_hours: int = 12,
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
        body = f"{product.name} ürününün stoğu {product.stock} adete düştü."
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
        """
        Web push notifications have been removed from the project.
        This method is kept for compatibility but does nothing.
        Use Telegram notifications instead via send_telegram_notification().
        """
        logger.info(f"Web push notification skipped (feature removed): {payload.head}")
        pass

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


# ===========================
# Telegram Notification Service
# ===========================

def send_telegram_notification(message: str) -> bool:
    """
    Send a notification message to Telegram group/channel.
    
    Args:
        message: The text message to send
        
    Returns:
        True if successful, False otherwise
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    if not bot_token or not chat_id:
        logger.warning("Telegram bot token or chat ID not configured")
        return False
    
    # Convert chat_id to string and ensure it's valid
    try:
        chat_id = str(chat_id).strip()
        if not chat_id or chat_id == 'None':
            logger.error("Invalid chat_id value")
            return False
    except Exception as e:
        logger.error(f"Failed to process chat_id: {e}")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Telegram has 4096 character limit
    if len(message) > 4096:
        message = message[:4090] + "..."
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Telegram notification sent successfully to chat_id: {chat_id}")
        return True
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"Telegram HTTP error: {e}")
        logger.error(f"Response: {e.response.text if e.response else 'No response'}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram: {e}")
        return False


def send_low_quantity_purchase_items_telegram_alert(items: List[PurchaseItem]) -> bool:
    """
    Send a compact summary alert for low quantity purchase items to Telegram.
    Only counts per category are shown; detail commands are included for drill-down.

    Args:
        items: List of low quantity purchase items (should already be filtered for is_archived=False)

    Returns:
        True if message sent successfully, False otherwise
    """
    if not items:
        return False

    # Group items by urgency
    critical = [i for i in items if i.quantity == 0]
    urgent = [i for i in items if 0 < i.quantity <= 1]
    warning = [i for i in items if 1 < i.quantity <= 3]

    timestamp = timezone.now().strftime('%d.%m.%Y %H:%M')

    lines = [
        "🛒 <b>Ürün Miktar Özeti</b>",
        f"⏰ {timestamp}",
        "",
        f"📊 Toplam <b>{len(items)}</b> ürün dikkat gerektiriyor:",
        "",
    ]

    if critical:
        lines.append(f"🔴 <b>Tükendi</b>: {len(critical)} ürün")
    if urgent:
        lines.append(f"⚠️ <b>Acil</b> (1 adet): {len(urgent)} ürün")
    if warning:
        lines.append(f"📦 <b>Düşük</b> (2-3 adet): {len(warning)} ürün")

    lines += [
        "",
        "💬 Detay için komut gönderin:",
    ]
    if critical:
        lines.append("/tukenen_urunler — Tükenenleri listele")
    if urgent:
        lines.append("/acil_urunler — Acil olanları listele")
    if warning:
        lines.append("/dusuk_urunler — Düşük miktarlıları listele")

    message = "\n".join(lines)

    logger.info(f"Sending Telegram purchase items summary (length: {len(message)})")
    success = send_telegram_notification(message)
    if not success:
        logger.error("Failed to send Telegram purchase items summary")
    return success

