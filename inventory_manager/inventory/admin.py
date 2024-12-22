from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'purchase_price', 'selling_price', 'stock', 'profit_margin')
    search_fields = ('name', 'barcode')  # Arama yapılacak alanlar
