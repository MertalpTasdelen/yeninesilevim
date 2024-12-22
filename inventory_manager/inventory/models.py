from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)  # Ürün ismi
    barcode = models.CharField(max_length=50, unique=True)  # Barkod alanı
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # Alış fiyatı
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)  # Satış fiyatı
    stock = models.PositiveIntegerField()  # Stok adedi
    created_at = models.DateTimeField(auto_now_add=True)  # Ürün eklenme zamanı

    def __str__(self):
        return self.name

    def profit_margin(self):
        """Calculates porfit margin for the product"""
        return self.selling_price - self.purchase_price
    
    class Meta:
        db_table = 'inventory_product'
