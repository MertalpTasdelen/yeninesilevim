from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ProfitCalculator
from .forms import ProductForm
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Import Trendyol integration utilities and datetime for timestamp conversion
from .trendyol_integration import fetch_settlements, calculate_profit_for_settlements
import datetime

from pyzbar.pyzbar import decode
from PIL import Image
import base64
from io import BytesIO


def _require_login(request):
    """
    Helper function to enforce that a user has logged in via the custom
    password prompt.  If the session flag ``is_logged_in`` is not set, the
    caller will be redirected to the login page.  Views that mutate data or
    expose sensitive information should call this before proceeding.
    """
    if not request.session.get('is_logged_in'):
        # Redirect unauthenticated users to the login page.  Note: we avoid
        # storing the current URL for simplicity, but Django's built-in
        # authentication framework can provide this functionality if needed.
        return redirect('login')
    return None


def ajax_search(request):
    products = Product.objects.all()
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # 12 products per page

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'page_obj': products,
        'request': request,  # provide request for session access in templates
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

    # Sorting logic
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

    paginator = Paginator(products, 12)
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
    # Require login before allowing product creation
    resp = _require_login(request)
    if resp:
        return resp
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/product_form.html', {'form': form})


def edit_product(request, id):
    # Require login to edit
    resp = _require_login(request)
    if resp:
        return resp
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
    # Only allow deletion when logged in
    resp = _require_login(request)
    if resp:
        return resp
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('product_list')


@require_POST
def adjust_stock(request, id, amount):
    # Protect stock modifications from unauthenticated access
    resp = _require_login(request)
    if resp:
        return resp
    product = get_object_or_404(Product, id=id)
    product.stock = max(product.stock + int(amount), 0)
    product.save()
    # If the request comes via AJAX, return the new stock count as JSON so
    # the client-side script can update the page without a full reload.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'stock': product.stock})
    return redirect('product_list')


def camera_view(request):
    return render(request, 'inventory/camera_view.html')


def scan_barcode(request):
    if request.method == 'POST':
        try:
            image_data = request.json().get('image')
            image_data = image_data.split(",")[1]
            image_bytes = BytesIO(base64.b64decode(image_data))
            image = Image.open(image_bytes)
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
    # This view is used to calculate profit on a single item.  It accepts
    # barcode, selling_price and commution via query parameters to pre-fill
    # the form.  Access to the form itself does not expose sensitive
    # business information, so no login check is required.
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
    # Save a profit calculation to the database.  This does not reveal
    # sensitive inventory details, but it writes to the database.  Require
    # login before persisting.
    resp = _require_login(request)
    if resp:
        return resp
    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        selling_price = request.POST.get('selling_price')
        commution = request.POST.get('commution')
        purchase_cost = request.POST.get('purchase_cost')
        shipping_cost = request.POST.get('shipping_cost')
        packaging_cost = request.POST.get('packaging_cost')
        other_costs = request.POST.get('other_costs')
        vat_rate = request.POST.get('vat_rate')

        commission_rate = float(commution) / 100
        paid_commission = float(selling_price) * commission_rate
        total_cost = float(purchase_cost) + float(shipping_cost) + float(packaging_cost) + float(other_costs) + paid_commission
        paid_vat = (float(selling_price) * float(vat_rate) / 100) - (total_cost * float(vat_rate) / 100)
        net_profit = float(selling_price) - total_cost - paid_vat - commission_rate
        profit_margin = (net_profit / total_cost) * 100

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
    # Only logged-in users should see the detailed cost breakdowns stored in
    # ProfitCalculator records.  Redirect unauthenticated users to the login
    # page.
    resp = _require_login(request)
    if resp:
        return resp
    records = ProfitCalculator.objects.all()
    return render(request, 'inventory/profit_calculator_list.html', {'records': records, 'request': request})


def get_product_image(request):
    barcode = request.GET.get('barcode')
    product = get_object_or_404(Product, barcode=barcode)
    return JsonResponse({'image_url': product.image_url})


def delete_profit_calculation(request, id):
    # Deletion of profit calculations is a destructive operation; require login
    resp = _require_login(request)
    if resp:
        return resp
    if request.method == 'DELETE':
        record = get_object_or_404(ProfitCalculator, id=id)
        record.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


def trendyol_profit(request):
    """
    Retrieve settlement records from Trendyol for a given date range,
    match them with local products and compute net profit.
    Only authenticated users can access this view.
    """
    # Enforce authentication
    resp = _require_login(request)
    if resp:
        return resp
    results = []
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        try:
            # Parse input dates (YYYY-MM-DD) and convert to Unix timestamps in ms.
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            start_ts = int(start_dt.timestamp() * 1000)
            # Include full end date by extending to end of day.
            end_ts = int((end_dt + datetime.timedelta(days=1)).timestamp() * 1000) - 1
  
            seller_id = "XXXXXXX"
            api_key = "XX"
            api_secret = "XX"
            store_front_code = "TRENDYOLTR"
            user_agent = f"{seller_id}-XX"
            response_data = fetch_settlements(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                start_date=start_ts,
                end_date=end_ts,
                transaction_type="Sale",
                page=0,
                size=500,
                store_front_code=store_front_code,
                user_agent=user_agent
            )
            content = []
            if isinstance(response_data, dict):
                # Trendyol returns settlement list under `content`
                content = response_data.get('content', []) or []
            results = calculate_profit_for_settlements(content)
        except Exception:
            # Suppress errors and leave results empty
            results = []
    context = {
        'results': results,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'inventory/trendyol_profit.html', context)


def login_view(request):
    LOGIN_PASSWORD = '1111'
    if request.method == 'POST':
        password = request.POST.get('password')
        if password == LOGIN_PASSWORD:
            request.session['is_logged_in'] = True
            return redirect('product_list')
        else:
            return render(request, 'inventory/login.html', {'error': 'Invalid password'})
    return render(request, 'inventory/login.html')


def logout_view(request):
    if 'is_logged_in' in request.session:
        del request.session['is_logged_in']
    return redirect('product_list')