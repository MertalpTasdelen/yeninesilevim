from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    name = models.CharField(max_length=100)
    barcode = models.CharField(max_length=50, unique=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    commution = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stock = models.PositiveIntegerField()
    image_url = models.CharField(max_length=1024, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    low_stock_notified_at = models.DateTimeField(blank=True, null=True)
    purchase_barcode = models.CharField(
        "Alış barkodu",
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        help_text="Tedarikçinin/alış fişinin barkodu (opsiyonel).",
    )

    def __str__(self):
        return self.name

    def profit_margin(self):
        """Calculates profit margin for the product"""
        return self.selling_price - self.purchase_price

    class Meta:
        db_table = "inventory_product"


class ProfitCalculator(models.Model):
    barcode = models.CharField(max_length=50, unique=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    commution = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    packaging_cost = models.DecimalField(max_digits=10, decimal_places=2)
    other_costs = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    paid_commission = models.DecimalField(max_digits=10, decimal_places=2)
    paid_vat = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    net_profit = models.DecimalField(max_digits=10, decimal_places=2)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profit calculation for {self.barcode}"

    class Meta:
        db_table = "profits"


class PushSubscription(models.Model):
    """Web Push Notification subscription storage"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    group = models.CharField(max_length=50, default='default', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Push subscription for {self.user or 'anonymous'} - {self.group}"

    class Meta:
        db_table = "push_subscriptions"
        indexes = [
            models.Index(fields=['group']),
            models.Index(fields=['endpoint']),
        ]


class PurchaseItem(models.Model):
    """Satın alınan ürünler için model"""
    name = models.CharField("Ürün Adı", max_length=255)
    purchase_barcode = models.CharField("Alış Barkodu", max_length=128, db_index=True)
    purchase_price = models.DecimalField("Alış Fiyatı", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Miktar", default=1)
    image_url = models.CharField("Görsel URL", max_length=1024, blank=True, null=True)
    is_archived = models.BooleanField(default=False, db_index=True, help_text="Arşivlenmiş ürünler")
    created_at = models.DateTimeField("Oluşturulma Tarihi", auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.purchase_barcode}"

    class Meta:
        db_table = "purchase_items"
        ordering = ['-created_at']
        verbose_name = "Satın Alınan Ürün"
        verbose_name_plural = "Satın Alınan Ürünler"


class ListingComponent(models.Model):
    """Bir ilanın hangi SKU'lardan (purchase_items) oluştuğunu tutar."""
    inventory_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name="İlan",
    )
    purchase_item = models.ForeignKey(
        PurchaseItem,
        on_delete=models.RESTRICT,
        related_name='listing_usages',
        verbose_name="SKU (Alış Ürünü)",
    )
    qty_per_listing = models.DecimalField(
        "Bu ilanda kaç adet",
        max_digits=10,
        decimal_places=2,
        default=1,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.inventory_product.name} ← {self.purchase_item.name} x{self.qty_per_listing}"

    class Meta:
        db_table = "listing_components"
        unique_together = ('inventory_product', 'purchase_item')
        verbose_name = "İlan Bileşeni"
        verbose_name_plural = "İlan Bileşenleri"
        constraints = [
            models.CheckConstraint(
                check=models.Q(qty_per_listing__gt=0),
                name='qty_positive_check',
            ),
        ]


class TrendyolWebhookLog(models.Model):
    """Trendyol webhook isteklerini loglar"""
    order_number = models.CharField("Sipariş No", max_length=100, db_index=True)
    barcode = models.CharField("Barkod", max_length=100, db_index=True)
    status = models.CharField("Durum", max_length=50)  # shipmentPackageStatus
    line_item_status = models.CharField("Line Item Durumu", max_length=50, blank=True, null=True, db_index=True)  # orderLineItemStatusName
    quantity = models.IntegerField("Adet", default=1)
    
    # İşlem sonucu
    success = models.BooleanField("Başarılı", default=False)
    error_message = models.TextField("Hata Mesajı", blank=True, null=True)
    processed = models.BooleanField("İşlendi", default=True, db_index=True, help_text="Stok düşürme işlemi yapıldı mı?")
    
    # Etkilenen kayıtlar
    affected_product_id = models.IntegerField("Ürün ID", null=True, blank=True)
    affected_components = models.JSONField("Etkilenen Bileşenler", default=list, blank=True)
    
    # Raw data
    raw_payload = models.JSONField("Ham Veri", default=dict, blank=True)
    
    created_at = models.DateTimeField("Oluşturulma Tarihi", auto_now_add=True)

    def __str__(self):
        return f"{self.order_number} - {self.barcode} [{self.status}]"

    class Meta:
        db_table = "trendyol_webhook_logs"
        ordering = ['-created_at']
        verbose_name = "Trendyol Webhook Log"
        verbose_name_plural = "Trendyol Webhook Logları"
        indexes = [
            models.Index(fields=['order_number', 'barcode']),
            models.Index(fields=['line_item_status']),
        ]

