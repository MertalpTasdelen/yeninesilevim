from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)  # Ürün ismi
    barcode = models.CharField(max_length=50, unique=True)  # Barkod alanı
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # Alış fiyatı
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)  # Satış fiyatı
    commution = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Komisyon oranı
    stock = models.PositiveIntegerField()  # Stok adedi
    image_url = models.CharField(max_length=1024, blank=True, null=True)  # Image URL
    created_at = models.DateTimeField(auto_now_add=True)  # Ürün eklenme zamanı
    purchase_barcode = models.CharField(
        "Alış barkodu",
        max_length=128,            # Barkod uzunluğunuza göre 64/128/255 seçebilirsiniz
        blank=True,
        null=True,
        db_index=True,             # Arama/filtrelerde performans için endeks
        help_text="Tedarikçinin/alış fişinin barkodu (opsiyonel)."
    )

    def __str__(self):
        return self.name

    def profit_margin(self):
        """Calculates profit margin for the product"""
        return self.selling_price - self.purchase_price

    class Meta:
        db_table = 'inventory_product'

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
        return self.name
    class Meta:
        db_table = 'profits'