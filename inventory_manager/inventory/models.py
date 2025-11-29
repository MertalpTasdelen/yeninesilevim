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
    created_at = models.DateTimeField("Oluşturulma Tarihi", auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.purchase_barcode}"

    class Meta:
        db_table = "purchase_items"
        ordering = ['-created_at']
        verbose_name = "Satın Alınan Ürün"
        verbose_name_plural = "Satın Alınan Ürünler"

