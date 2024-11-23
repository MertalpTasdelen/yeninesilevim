from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm
from django.http import HttpResponseBadRequest

def product_list(request):
    products = Product.objects.all()
    return render(request, 'inventory/product_list.html', {'products': products})

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/add_product.html', {'form': form})

def adjust_stock(request, product_id, amount):
    try:
        # Convert `amount` to an integer (handles negative values)
        amount = int(amount)
    except ValueError:
        # Return a bad request if `amount` is not a valid integer
        return HttpResponseBadRequest("Invalid amount value")

    # Get the product or return 404 if it doesn't exist
    product = get_object_or_404(Product, id=product_id)

    # Adjust stock
    product.stock += amount
    product.save()

    # Redirect back to the product list
    return redirect('product_list')
