from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'barcode', 'purchase_price', 'selling_price', 'stock', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter barcode'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter purchase price'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter selling price'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter stock quantity'}),
            'image_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter image URL'}),
        }
        labels = {
            'name': 'Product Name',
            'barcode': 'Barcode',
            'purchase_price': 'Purchase Price',
            'selling_price': 'Selling Price',
            'stock': 'Stock Quantity',
            'image_url': 'Image URL',
        }