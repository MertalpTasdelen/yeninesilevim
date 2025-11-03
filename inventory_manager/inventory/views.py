from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ProfitCalculator
from .forms import ProductForm
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pyzbar.pyzbar import decode
from PIL import Image
import base64
from io import BytesIO


def ajax_search(request):
    products = Product.objects.all()
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # Her sayfada 12 ürün
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': products,
        'request': request,  # Login durumunu kontrol etmek için request'i context'e ekleyin
    }
    
    return render(request, 'inventory/product_list_results.html', context)

def product_list(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort_by', 'id')
    page_number = request.GET.get('page', 1)

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(barcode__icontains=query) |
            Q(purchase_barcode__icontains=query)
        )
    else:
        products = Product.objects.all()

    # Sıralama işlemleri
    if sort_by == 'stock_desc':
        products = products.order_by('-stock')
    elif sort_by == 'stock_asc':
        products = products.order_by('stock')
    elif sort_by == 'selling_price_desc':
        products = products.order_by('-selling_price')
    elif sort_by == 'selling_price_asc':
        products = products.order_by('selling_price')
    else:
        products = products.order_by('id')

    paginator = Paginator(products, 12)  # Her sayfada 12 ürün
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'inventory/product_list_results.html',
            {'page_obj': page_obj, 'request': request},
            request=request
        )
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next()
        })

    return render(request, 'inventory/product_list.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by
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

@require_POST
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('product_list')

@require_POST
def adjust_stock(request, id, amount):
    product = get_object_or_404(Product, id=id)
    product.stock = max(product.stock + int(amount), 0)
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

def profit_calculator(request):
    if not request.session.get('is_logged_in'):
        # Eğer giriş yapılmamışsa sadece satış fiyatını göster
        barcode = request.GET.get('barcode')
        selling_price = request.GET.get('selling_price')
        context = {
            'barcode': barcode,
            'selling_price': selling_price,
        }
    else:
        # Giriş yapılmışsa tüm bilgileri göster
        barcode = request.GET.get('barcode')
        selling_price = request.GET.get('selling_price')
        commution = request.GET.get('commution')
        context = {
            'barcode': barcode,
            'selling_price': selling_price,
            'commution': commution,
        }
    return render(request, 'inventory/profit_calculator.html', context)

@csrf_exempt
def save_profit_calculation(request):
    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        selling_price = request.POST.get('selling_price')
        commution = request.POST.get('commution')
        purchase_cost = request.POST.get('purchase_cost')
        shipping_cost = request.POST.get('shipping_cost')
        packaging_cost = request.POST.get('packaging_cost')
        other_costs = request.POST.get('other_costs')
        vat_rate = request.POST.get('vat_rate')

        # Calculate the results
        commission_rate = float(commution) / 100
        paid_commission = float(selling_price) * commission_rate
        total_cost = float(purchase_cost) + float(shipping_cost) + float(packaging_cost) + float(other_costs) + paid_commission
        paid_vat = (float(selling_price) * float(vat_rate) / 100) - (total_cost * float(vat_rate) / 100)
        net_profit = float(selling_price) - total_cost - paid_vat - commission_rate
        profit_margin = (net_profit / total_cost) * 100

        # product = get_object_or_404(Product, barcode=barcode)

        # Save to the database
        ProfitCalculator.objects.create(
            barcode=barcode,
            selling_price=selling_price,
            commution=commution,
            purchase_cost=purchase_cost,
            shipping_cost=shipping_cost,
            packaging_cost=packaging_cost,
            other_costs=other_costs,
            vat_rate=vat_rate,
            paid_commission=paid_commission,
            paid_vat=paid_vat,
            total_cost=total_cost,
            net_profit=net_profit,
            profit_margin=profit_margin
        )

        return redirect('profit_calculator')

    return render(request, 'inventory/profit_calculator.html')

def profit_calculator_list(request):
    records = ProfitCalculator.objects.all()
    return render(request, 'inventory/profit_calculator_list.html', {'records': records})

def get_product_image(request):
    barcode = request.GET.get('barcode')
    product = get_object_or_404(Product, barcode=barcode)
    return JsonResponse({'image_url': product.image_url})

def delete_profit_calculation(request, id):
    if request.method == 'DELETE':
        record = get_object_or_404(ProfitCalculator, id=id)
        record.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def login_view(request):
    LOGIN_PASSWORD = '020524'

    if request.method == 'POST':
        password = request.POST.get('password')
        if password == LOGIN_PASSWORD:
            request.session['is_logged_in'] = True
            return redirect('product_list')  # Redirect to the profit_calculator_list page
        else:
            return render(request, 'inventory/login.html', {'error': 'Invalid password'})
    return render(request, 'inventory/login.html')

def logout_view(request):
    if 'is_logged_in' in request.session:
        del request.session['is_logged_in']
    return redirect('product_list')
