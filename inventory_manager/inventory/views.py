from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import ProductForm
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

def ajax_search(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(barcode__icontains=query)
        ).order_by('id')
    else:
        products = Product.objects.all().order_by('id')
    html = render_to_string('inventory/product_list_results.html', {'products': products})
    return JsonResponse({'html': html})

def product_list(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(barcode__icontains=query)
        ).order_by('id')
    else:
        products = Product.objects.all().order_by('id')
    return render(request, 'inventory/product_list.html', {'products': products, 'query': query})

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/product_form.html', {'form': form})

def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/product_form.html', {'form': form})

def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('product_list')

@csrf_exempt
def adjust_stock(request, id, amount):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        product.stock += int(amount)  # Convert amount to integer
        product.save()
    return redirect('product_list')