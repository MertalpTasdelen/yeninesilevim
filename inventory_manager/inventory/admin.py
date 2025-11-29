from django.contrib import admin
from .models import Product, PurchaseItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'purchase_price', 'selling_price', 'stock', 'profit_margin')
    search_fields = ('name', 'barcode')  # Arama yapılacak alanlar

@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'purchase_barcode', 'purchase_price', 'quantity', 'created_at')
    search_fields = ('name', 'purchase_barcode')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
