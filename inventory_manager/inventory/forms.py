from django import forms
from .models import Product, ListingComponent, PurchaseItem

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'barcode', 'purchase_barcode', 'purchase_price', 'selling_price', 'commution', 'stock', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adını girin'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barkodu girin'}),
            'purchase_barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alış barkodunu girin'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Alış fiyatını girin'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Satış fiyatını girin'}),
            'commution': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Komisyonu girin'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stok miktarını girin'}),
            'image_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resim URL\'sini girin'}),
        }
        labels = {
            'name': 'Ürün Adı',
            'barcode': 'Barkod',
            'purchase_barcode': 'Alış Barkodu',
            'purchase_price': 'Alış Fiyatı',
            'selling_price': 'Satış Fiyatı',
            'commution': 'Komisyon',
            'stock': 'Stok Miktarı',
            'image_url': 'Resim URL\'si',
        }


class ListingComponentForm(forms.ModelForm):
    class Meta:
        model = ListingComponent
        fields = ['purchase_item', 'qty_per_listing']
        widgets = {
            'purchase_item': forms.Select(attrs={'class': 'form-select', 'id': 'id_purchase_item'}),
            'qty_per_listing': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adet girin',
                'min': '0.01',
                'step': '0.01',
                'value': '1',
            }),
        }
        labels = {
            'purchase_item': 'SKU (Alış Ürünü)',
            'qty_per_listing': 'Bu İlanda Kaç Adet',
        }