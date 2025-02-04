from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import ProductForm
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.paginator import Paginator

from pyzbar.pyzbar import decode
from PIL import Image
import base64
from io import BytesIO


def ajax_search(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(barcode__icontains=query)
        ).order_by('id')
    else:
        products = Product.objects.all().order_by('id')
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    html = render_to_string('inventory/product_list_results.html', {'page_obj': page_obj, 'query': query})
    return JsonResponse({'html': html})

def product_list(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort_by', 'id')
    sort_order = request.GET.get('sort_order', 'asc')
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(barcode__icontains=query)
        )
    else:
        products = Product.objects.all()
    
    if sort_order == 'desc':
        sort_by = f'-{sort_by}'
    
    products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory/product_list.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'sort_order': sort_order
    })

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

def camera_view(request):
    return render(request, 'inventory/camera_view.html')

def scan_barcode(request):
    if request.method == 'POST':
        try:
            # Get the image data from the request
            image_data = request.json().get('image')
            image_data = image_data.split(",")[1]  # Remove the data:image/png;base64, prefix
            image_bytes = BytesIO(base64.b64decode(image_data))
            image = Image.open(image_bytes)

            # Decode the barcode
            decoded_objects = decode(image)
            if decoded_objects:
                barcode_data = decoded_objects[0].data.decode('utf-8')
                return JsonResponse({'message': f'Barcode data: {barcode_data}'})
            else:
                return JsonResponse({'message': 'No barcode detected'})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'})
    return JsonResponse({'message': 'Invalid request'})
