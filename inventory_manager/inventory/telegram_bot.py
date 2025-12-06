"""
Telegram Bot Command Handlers
Handles incoming commands from Telegram group
"""
import logging
from typing import List, Dict, Any
from django.conf import settings
from .models import Product
from .notifications import send_telegram_notification
import requests

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot command handler"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        
    def send_message(self, chat_id: str, text: str, reply_to_message_id: int = None) -> bool:
        """Send a message to specific chat"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        # Telegram has 4096 character limit
        if len(text) > 4096:
            text = text[:4090] + "..."
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def format_products_message(self, products: List[Product], title: str, emoji: str) -> str:
        """Format products into a nice message"""
        if not products:
            return f"{emoji} <b>{title}</b>\n\n✅ Harika! Hiç ürün yok."
        
        message = f"{emoji} <b>{title}</b>\n"
        message += f"📊 Toplam: <b>{len(products)}</b> ürün\n\n"
        
        for i, product in enumerate(products, 1):
            # Limit to 30 products to avoid message length issues
            if i > 30:
                remaining = len(products) - 30
                message += f"\n... ve {remaining} ürün daha\n"
                break
            
            name = product.name[:40]  # Truncate long names
            barcode = product.barcode or 'N/A'
            stock = product.stock
            
            message += f"{i}. <b>{name}</b>\n"
            message += f"   └ Barkod: <code>{barcode}</code>\n"
            message += f"   └ Stok: <b>{stock}</b> adet\n"
            
            if product.selling_price:
                message += f"   └ Fiyat: {product.selling_price} ₺\n"
            
            message += "\n"
        
        return message
    
    def handle_stok_command(self, chat_id: str, message_id: int) -> bool:
        """Handle /stok command - show all low stock products"""
        try:
            products = Product.objects.filter(stock__lte=3).order_by('stock', 'name')
            
            if not products:
                text = "✅ <b>Harika!</b>\n\nTüm ürünlerin stoğu yeterli! 🎉"
                return self.send_message(chat_id, text, message_id)
            
            # Group by urgency
            critical = [p for p in products if p.stock == 0]
            urgent = [p for p in products if 0 < p.stock <= 1]
            warning = [p for p in products if 1 < p.stock <= 3]
            
            message = f"📦 <b>Stok Durumu</b>\n\n"
            message += f"Toplam düşük stok: <b>{products.count()}</b> ürün\n\n"
            
            if critical:
                message += f"🔴 Tükendi: <b>{len(critical)}</b>\n"
            if urgent:
                message += f"⚠️ Acil: <b>{len(urgent)}</b>\n"
            if warning:
                message += f"📦 Düşük: <b>{len(warning)}</b>\n"
            
            message += "\n💡 Detay için:\n"
            message += "/tukenen - Tükenen ürünler\n"
            message += "/acil - Acil sipariş gerekli (1 adet)\n"
            message += "/dusuk - Düşük stoklu ürünler (2-3 adet)"
            
            return self.send_message(chat_id, message, message_id)
            
        except Exception as e:
            logger.error(f"Error handling /stok command: {e}")
            return False
    
    def handle_tukenen_command(self, chat_id: str, message_id: int) -> bool:
        """Handle /tukenen command - show out of stock products"""
        try:
            products = list(Product.objects.filter(stock=0).order_by('name'))
            message = self.format_products_message(products, "Tükenen Ürünler", "🔴")
            return self.send_message(chat_id, message, message_id)
        except Exception as e:
            logger.error(f"Error handling /tukenen command: {e}")
            return False
    
    def handle_acil_command(self, chat_id: str, message_id: int) -> bool:
        """Handle /acil command - show urgent stock (0-1 items)"""
        try:
            products = list(Product.objects.filter(stock__gt=0, stock__lte=1).order_by('stock', 'name'))
            message = self.format_products_message(products, "Acil Sipariş Gerekli", "⚠️")
            return self.send_message(chat_id, message, message_id)
        except Exception as e:
            logger.error(f"Error handling /acil command: {e}")
            return False
    
    def handle_dusuk_command(self, chat_id: str, message_id: int) -> bool:
        """Handle /dusuk command - show low stock (2-3 items)"""
        try:
            products = list(Product.objects.filter(stock__gt=1, stock__lte=3).order_by('stock', 'name'))
            message = self.format_products_message(products, "Düşük Stoklu Ürünler", "📦")
            return self.send_message(chat_id, message, message_id)
        except Exception as e:
            logger.error(f"Error handling /dusuk command: {e}")
            return False
    
    def handle_yardim_command(self, chat_id: str, message_id: int) -> bool:
        """Handle /yardim command - show help message"""
        message = """
🤖 <b>Stok Yönetim Botu</b>

<b>Kullanılabilir Komutlar:</b>

/stok - Genel stok özeti
/tukenen - Tükenen ürünler (0 adet)
/acil - Acil sipariş gerekli (1 adet)
/dusuk - Düşük stok (2-3 adet)
/yardim - Bu yardım mesajı

<b>Otomatik Bildirimler:</b>
📅 Her gün saat 09:00 ve 15:00
🚫 Pazar günleri kapalı
"""
        return self.send_message(chat_id, message.strip(), message_id)
    
    def process_update(self, update: Dict[str, Any]) -> bool:
        """Process incoming Telegram update"""
        try:
            # Extract message data
            message = update.get('message', {})
            if not message:
                return False
            
            chat_id = str(message.get('chat', {}).get('id', ''))
            message_id = message.get('message_id')
            text = message.get('text', '').strip()
            
            if not text.startswith('/'):
                return False  # Not a command
            
            # Parse command
            command = text.split()[0].lower().replace('/', '')
            
            # Handle commands
            handlers = {
                'stok': self.handle_stok_command,
                'tukenen': self.handle_tukenen_command,
                'acil': self.handle_acil_command,
                'dusuk': self.handle_dusuk_command,
                'yardim': self.handle_yardim_command,
                'start': self.handle_yardim_command,
                'help': self.handle_yardim_command,
            }
            
            handler = handlers.get(command)
            if handler:
                logger.info(f"Processing command: /{command} from chat {chat_id}")
                return handler(chat_id, message_id)
            else:
                logger.warning(f"Unknown command: /{command}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing Telegram update: {e}")
            return False


def setup_webhook(webhook_url: str) -> bool:
    """
    Set up webhook for Telegram bot
    
    Args:
        webhook_url: Full URL where Telegram should send updates
                     Example: https://yeninesilevim.com/api/telegram-webhook
    
    Returns:
        True if webhook set successfully
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"Webhook set successfully: {webhook_url}")
            return True
        else:
            logger.error(f"Failed to set webhook: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False


def get_webhook_info() -> Dict[str, Any]:
    """Get current webhook information"""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get('result', {})
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return {}
