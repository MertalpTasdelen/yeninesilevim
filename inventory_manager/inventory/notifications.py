import logging
import json
import requests
from datetime import timedelta
from typing import Iterable, List, Optional

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pywebpush import webpush, WebPushException

from .models import Product, PushSubscription, PurchaseItem


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
        """Send push notification to all subscribers in the group using pywebpush."""
        subscriptions = PushSubscription.objects.filter(group=self.group_name)
        
        if not subscriptions.exists():
            logger.warning(f"No subscriptions found for group: {self.group_name}")
            return
        
        # Build VAPID claims
        vapid_claims = {
            "sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"
        }
        
        vapid_private_key = settings.VAPID_PRIVATE_KEY
        
        success_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            try:
                # Build subscription info dict for pywebpush
                subscription_info = {
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth
                    }
                }
                
                # Send the notification
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(payload.as_dict()),
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims,
                    ttl=1000
                )
                success_count += 1
                
            except WebPushException as e:
                failed_count += 1
                logger.error(
                    f"Failed to send push to subscription {subscription.id}: {e}",
                    extra={
                        "subscription_id": subscription.id,
                        "status_code": e.response.status_code if e.response else None
                    }
                )
                
                # If subscription is invalid (410 Gone), delete it
                if e.response and e.response.status_code == 410:
                    logger.info(f"Deleting expired subscription {subscription.id}")
                    subscription.delete()
                    
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Unexpected error sending push to subscription {subscription.id}: {e}",
                    extra={"subscription_id": subscription.id}
                )
        
        logger.info(
            f"Push notification sent: {success_count} succeeded, {failed_count} failed",
            extra={"group": self.group_name}
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
    Send low quantity alert for purchase items to Telegram (excluding archived).
    Messages are split if they exceed Telegram's character limit.
    
    Args:
        items: List of low quantity purchase items (should already be filtered for is_archived=False)
        
    Returns:
        True if at least one message sent successfully, False otherwise
    """
    if not items:
        return False
    
    # Group items by urgency
    critical = [i for i in items if i.quantity == 0]
    urgent = [i for i in items if 0 < i.quantity <= 1]
    warning = [i for i in items if 1 < i.quantity <= 3]
    
    messages = []
    current_message = f"🛒 <b>Ürün Miktar Uyarısı</b> 🛒\n\n📦 <b>{len(items)} ürün</b> düşük miktarda\n\n"
    
    def add_items_section(title, emoji, item_list):
        nonlocal current_message, messages
        
        if not item_list:
            return
        
        section = f"{emoji} <b>{title}</b> ({len(item_list)} ürün):\n"
        
        for item in item_list:
            # Escape HTML special characters
            name = str(item.name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            barcode = item.purchase_barcode or 'N/A'
            
            line = f"└ {name}\n   Barkod: <code>{barcode}</code> | Miktar: <b>{item.quantity}</b>\n"
            
            if item.quantity > 0 and hasattr(item, 'purchase_price') and item.purchase_price:
                line += f"   Alış: {item.purchase_price} ₺\n"
            
            line += "\n"
            
            # Check if adding this line would exceed limit (leave 200 char buffer)
            if len(current_message) + len(section) + len(line) > 3900:
                messages.append(current_message)
                current_message = f"🛒 <b>Ürün Miktar Uyarısı (devam)</b> 🛒\n\n{section}"
            
            if section not in current_message:
                current_message += section
                section = ""
            
            current_message += line
    
    # Add items by priority
    add_items_section("TÜKENDİ", "🔴", critical)
    add_items_section("ACİL", "⚠️", urgent)
    add_items_section("DÜŞÜK", "📦", warning)
    
    # Add timestamp
    timestamp = timezone.now().strftime('%d.%m.%Y %H:%M')
    current_message += f"\n⏰ {timestamp}"
    messages.append(current_message)
    
    # Send all messages
    success = False
    for i, msg in enumerate(messages, 1):
        logger.info(f"Sending Telegram purchase items message {i}/{len(messages)} (length: {len(msg)})")
        if send_telegram_notification(msg):
            success = True
        else:
            logger.error(f"Failed to send purchase items message {i}/{len(messages)}")
    
    return success

