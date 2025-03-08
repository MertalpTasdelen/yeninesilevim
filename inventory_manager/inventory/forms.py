from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'barcode', 'purchase_price', 'selling_price', 'commution', 'stock', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adını girin'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barkodu girin'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Alış fiyatını girin'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Satış fiyatını girin'}),
            'commution': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Komisyonu girin'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stok miktarını girin'}),
            'image_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resim URL\'sini girin'}),
        }
        labels = {
            'name': 'Ürün Adı',
            'barcode': 'Barkod',
            'purchase_price': 'Alış Fiyatı',
            'selling_price': 'Satış Fiyatı',
            'commution': 'Komisyon',
            'stock': 'Stok Miktarı',
            'image_url': 'Resim URL\'si',
        }