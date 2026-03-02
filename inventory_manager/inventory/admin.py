from django.contrib import admin
from .models import Product, PurchaseItem, ListingComponent, TrendyolWebhookLog

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


class ListingComponentInline(admin.TabularInline):
    model = ListingComponent
    extra = 1
    autocomplete_fields = ['purchase_item']


@admin.register(ListingComponent)
class ListingComponentAdmin(admin.ModelAdmin):
    list_display = ('inventory_product', 'purchase_item', 'qty_per_listing', 'created_at')
    search_fields = ('inventory_product__name', 'purchase_item__name', 'purchase_item__purchase_barcode')
    list_filter = ('created_at',)
    autocomplete_fields = ['inventory_product', 'purchase_item']


@admin.register(TrendyolWebhookLog)
class TrendyolWebhookLogAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'barcode', 'status', 'line_item_status', 'quantity', 'success', 'processed', 'created_at')
    list_filter = ('success', 'processed', 'status', 'line_item_status', 'created_at')
    search_fields = ('order_number', 'barcode', 'error_message')
    readonly_fields = ('order_number', 'barcode', 'status', 'line_item_status', 'quantity', 'success', 'processed',
                       'error_message', 'affected_product_id', 'affected_components', 'raw_payload', 'created_at')
    
    def has_add_permission(self, request):
        return False  # Webhook logları sadece sistem tarafından oluşturulur
    
    def has_change_permission(self, request, obj=None):
        return False  # Loglar değiştirilemez
