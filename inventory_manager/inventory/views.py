from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import Product, ProfitCalculator, PurchaseItem, ListingComponent, TrendyolWebhookLog
from .forms import ProductForm, ListingComponentForm
from .notifications import LowStockNotificationService, send_telegram_notification
from .telegram_bot import TelegramBot, setup_webhook, get_webhook_info
from .trendyol_integration import (
    calculate_monthly_summary,
)
import datetime
import calendar
import logging
import traceback
import os
import json
from django.conf import settings

logger = logging.getLogger(__name__)


def _require_login(request):
    if not request.session.get('is_logged_in', False):
        return redirect('login')
    return None


def product_list(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort_by', '')
    page = request.GET.get('page', 1)

    products = Product.objects.all()

    if query:
        products = products.filter(
            name__icontains=query
        ) | products.filter(
            barcode__icontains=query
        ) | products.filter(
            purchase_barcode__icontains=query
        )

    if sort_by == 'stock_desc':
        products = products.order_by('-stock')
    elif sort_by == 'stock_asc':
        products = products.order_by('stock')
    elif sort_by == 'selling_price_desc':
        products = products.order_by('-selling_price')
    elif sort_by == 'selling_price_asc':
        products = products.order_by('selling_price')
    else:
        products = products.order_by('-created_at')

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(page)

    # AJAX isteklerinde sadece HTML fragment dön
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render(
            request,
            'inventory/product_list_results.html',
            {'page_obj': page_obj}
        ).content.decode()
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next()
        })

    # Web push için grup context’i -> template’te subscribe butonu için

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
    }
    return render(request, 'inventory/product_list.html', context)


def ajax_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query)[:10]
    results = [{'id': p.id, 'name': p.name, 'barcode': p.barcode} for p in products]
    return JsonResponse(results, safe=False)


def add_product(request):
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


def delete_product(request, id):
    resp = _require_login(request)
    if resp:
        return resp
    
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('product_list')


def camera_view(request):
    field = request.GET.get('field', 'product_search')
    return render(request, 'inventory/camera_view.html', {'field': field})


def scan_barcode(request):
    barcode = request.POST.get('barcode', '')
    field = request.POST.get('field', 'product_search')
    
    if barcode:
        return JsonResponse({
            'success': True,
            'barcode': barcode,
            'field': field
        })
    return JsonResponse({'success': False})


def profit_calculator(request):
    barcode = request.GET.get('barcode', '')
    
    context = {
        'barcode': barcode,
    }
    return render(request, 'inventory/profit_calculator.html', context)


def save_profit_calculation(request):
    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        selling_price = float(request.POST.get('selling_price', 0))
        commution = float(request.POST.get('commution', 0))
        purchase_cost = float(request.POST.get('purchase_cost', 0))
        shipping_cost = float(request.POST.get('shipping_cost', 0))
        packaging_cost = float(request.POST.get('packaging_cost', 0))
        other_costs = float(request.POST.get('other_costs', 0))
        vat_rate = float(request.POST.get('vat_rate', 0))
        
        paid_commission = selling_price * (commution / 100)
        total_cost = purchase_cost + shipping_cost + packaging_cost + other_costs + paid_commission
        paid_vat = (selling_price * (vat_rate / 100)) - (total_cost * (vat_rate / 100))
        net_profit = selling_price - total_cost - paid_vat
        profit_margin = (net_profit / selling_price * 100) if selling_price > 0 else 0
        
        try:
            profit = ProfitCalculator.objects.get(barcode=barcode)
            profit.selling_price = selling_price
            profit.commution = commution
            profit.purchase_cost = purchase_cost
            profit.shipping_cost = shipping_cost
            profit.packaging_cost = packaging_cost
            profit.other_costs = other_costs
            profit.vat_rate = vat_rate
            profit.paid_commission = paid_commission
            profit.paid_vat = paid_vat
            profit.total_cost = total_cost
            profit.net_profit = net_profit
            profit.profit_margin = profit_margin
            profit.save()
        except ProfitCalculator.DoesNotExist:
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
                profit_margin=profit_margin,
            )
        
        return redirect('profit_calculator_list')
    
    return redirect('profit_calculator')


def profit_calculator_list(request):
    records = ProfitCalculator.objects.all().order_by('-created_at')
    paginator = Paginator(records, 10)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {'records': page_obj}
    return render(request, 'inventory/profit_calculator_list.html', context)


def delete_profit_calculation(request, id):
    if request.method == 'DELETE':
        try:
            record = ProfitCalculator.objects.get(id=id)
            record.delete()
            return JsonResponse({'success': True})
        except ProfitCalculator.DoesNotExist:
            return JsonResponse({'success': False}, status=404)
    
    return JsonResponse({'success': False}, status=405)


def get_product_image(request):
    barcode = request.GET.get('barcode', '')
    try:
        product = Product.objects.get(barcode=barcode)
        return JsonResponse({'image_url': product.image_url})
    except Product.DoesNotExist:
        return JsonResponse({'image_url': None})


def get_product_by_barcode(request):
    barcode = request.GET.get('barcode', '')
    try:
        product = Product.objects.get(barcode=barcode)
        return JsonResponse({
            'found': True,
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'purchase_price': str(product.purchase_price),
            'selling_price': str(product.selling_price),
            'stock': product.stock,
            'image_url': product.image_url,
        })
    except Product.DoesNotExist:
        return JsonResponse({'found': False})


@require_http_methods(["POST"])
def adjust_stock(request, id, amount):
    resp = _require_login(request)
    if resp:
        return JsonResponse({'success': False}, status=401)

    product = get_object_or_404(Product, id=id)

    # Eski stok değerini kaydet
    old_stock = product.stock

    # Yeni stok değerini uygula
    product.stock += int(amount)
    if product.stock < 0:
        product.stock = 0
    product.save()

    # Eşik kontrolü: stok 3'ün altına düştüyse ve eski stok >= 3 idiyse bildirim gönder
    notifier = LowStockNotificationService()
    notifier.notify_if_needed(
        product=product,
        target_url=request.build_absolute_uri(reverse('product_list')),
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'stock': product.stock})

    return redirect('product_list')


def trendyol_profit(request):
    resp = _require_login(request)
    if resp:
        return resp

    # 'month' param format: "YYYY-MM" (from <input type="month">)
    selected_month = request.GET.get('month', '')
    month_submitted = bool(selected_month)

    # Default form value = current month
    if not selected_month:
        selected_month = datetime.datetime.now().strftime('%Y-%m')

    monthly_summary = []
    missing_barcodes = []
    order_details = []

    if month_submitted:
        try:
            year, month_num = map(int, selected_month.split('-'))
            last_day = calendar.monthrange(year, month_num)[1]
            start_dt = datetime.datetime(year, month_num, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
            end_dt = datetime.datetime(year, month_num, last_day, 23, 59, 59, tzinfo=datetime.timezone.utc)
            seller_id = settings.TRENDYOL_SUPPLIER_ID
            api_key = settings.TRENDYOL_API_KEY
            api_secret = settings.TRENDYOL_API_SECRET
            monthly_summary, missing_barcodes, order_details = calculate_monthly_summary(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                start_date=start_dt,
                end_date=end_dt,
                store_front_code="TRENDYOLTR",
                user_agent=f"{seller_id}-OzlemFiratTasdelen",
            )
        except Exception as e:
            logger.error(f"Aylık özet hesaplamasında hata: {str(e)}")
            traceback.print_exc()

    context = {
        'selected_month': selected_month,
        'month_submitted': month_submitted,
        'monthly_summary': monthly_summary,
        'missing_barcodes': missing_barcodes,
        'order_details': order_details,
    }
    return render(request, 'inventory/trendyol_profit.html', context)

def login_view(request):
    error = None
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if password == settings.APP_LOGIN_PASSWORD:
            request.session['is_logged_in'] = True
            return redirect('product_list')
        else:
            error = 'Şifre yanlış'
    
    return render(request, 'inventory/login.html', {'error': error})


def logout_view(request):
    if 'is_logged_in' in request.session:
        del request.session['is_logged_in']
    return redirect('product_list')


# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE ITEMS
# ─────────────────────────────────────────────────────────────────────────────

def purchase_items_list(request):
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)

    items = PurchaseItem.objects.all()
    if query:
        items = items.filter(name__icontains=query) | items.filter(purchase_barcode__icontains=query)

    paginator = Paginator(items, 12)
    page_obj = paginator.get_page(page)

    return render(request, 'inventory/purchase_items_list.html', {
        'page_obj': page_obj,
        'query': query,
    })


def add_purchase_item(request):
    resp = _require_login(request)
    if resp:
        return resp

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        purchase_barcode = request.POST.get('purchase_barcode', '').strip()
        purchase_price = request.POST.get('purchase_price', 0)
        quantity = request.POST.get('quantity', 1)
        image_url = request.POST.get('image_url', '').strip()

        PurchaseItem.objects.create(
            name=name,
            purchase_barcode=purchase_barcode,
            purchase_price=purchase_price,
            quantity=quantity,
            image_url=image_url or None,
        )
        return redirect('purchase_items_list')

    return render(request, 'inventory/add_purchase_item.html')


@require_http_methods(["POST"])
def adjust_purchase_quantity(request, item_id, amount):
    resp = _require_login(request)
    if resp:
        return JsonResponse({'success': False}, status=401)

    item = get_object_or_404(PurchaseItem, id=item_id)
    item.quantity += int(amount)
    if item.quantity < 0:
        item.quantity = 0
    item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'quantity': item.quantity})
    return redirect('purchase_items_list')


@require_http_methods(["POST"])
def delete_purchase_item(request, item_id):
    resp = _require_login(request)
    if resp:
        return JsonResponse({'success': False}, status=401)

    item = get_object_or_404(PurchaseItem, id=item_id)
    item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('purchase_items_list')


@require_http_methods(["POST"])
def toggle_archive_purchase_item(request, item_id):
    resp = _require_login(request)
    if resp:
        return JsonResponse({'success': False}, status=401)

    item = get_object_or_404(PurchaseItem, id=item_id)
    item.is_archived = not item.is_archived
    item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_archived': item.is_archived})
    return redirect('purchase_items_list')


# ─────────────────────────────────────────────────────────────────────────────
# LISTING COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def listing_components(request):
    resp = _require_login(request)
    if resp:
        return resp

    products = Product.objects.prefetch_related('components__purchase_item').order_by('name')
    all_purchase_items = PurchaseItem.objects.filter(is_archived=False).order_by('name')

    return render(request, 'inventory/listing_components.html', {
        'products': products,
        'all_purchase_items': all_purchase_items,
    })


def save_listing_components(request, product_id):
    resp = _require_login(request)
    if resp:
        return JsonResponse({'success': False}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    product = get_object_or_404(Product, id=product_id)

    try:
        data = json.loads(request.body)
        components = data.get('components', [])

        ListingComponent.objects.filter(inventory_product=product).delete()

        for comp in components:
            purchase_item_id = comp.get('purchase_item_id')
            qty = comp.get('qty_per_listing', 1)
            if purchase_item_id:
                purchase_item = get_object_or_404(PurchaseItem, id=purchase_item_id)
                ListingComponent.objects.create(
                    inventory_product=product,
                    purchase_item=purchase_item,
                    qty_per_listing=qty,
                )

        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"save_listing_components hata: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def add_listing_component(request, product_id):
    resp = _require_login(request)
    if resp:
        return JsonResponse({'success': False}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    product = get_object_or_404(Product, id=product_id)

    try:
        data = json.loads(request.body)
        purchase_item_id = data.get('purchase_item_id')
        qty = data.get('qty_per_listing', 1)

        purchase_item = get_object_or_404(PurchaseItem, id=purchase_item_id)
        component, created = ListingComponent.objects.get_or_create(
            inventory_product=product,
            purchase_item=purchase_item,
            defaults={'qty_per_listing': qty},
        )
        if not created:
            component.qty_per_listing = qty
            component.save()

        return JsonResponse({'success': True, 'created': created})
    except Exception as e:
        logger.error(f"add_listing_component hata: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def delete_listing_component(request, component_id):
    resp = _require_login(request)
    if resp:
        return JsonResponse({'success': False}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    component = get_object_or_404(ListingComponent, id=component_id)
    component.delete()
    return JsonResponse({'success': True})


def api_product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    components = list(product.components.select_related('purchase_item').values(
        'id', 'qty_per_listing',
        'purchase_item__id', 'purchase_item__name', 'purchase_item__purchase_barcode',
        'purchase_item__purchase_price', 'purchase_item__quantity',
    ))
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'barcode': product.barcode,
        'components': components,
    })


def api_purchase_item_detail(request, item_id):
    item = get_object_or_404(PurchaseItem, id=item_id)
    return JsonResponse({
        'id': item.id,
        'name': item.name,
        'purchase_barcode': item.purchase_barcode,
        'purchase_price': str(item.purchase_price),
        'quantity': item.quantity,
        'is_archived': item.is_archived,
    })


# ─────────────────────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def telegram_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        update = json.loads(request.body)
        bot = TelegramBot()
        bot.process_update(update)
        return JsonResponse({'ok': True})
    except Exception as e:
        logger.error(f"telegram_webhook hata: {e}")
        return JsonResponse({'ok': False}, status=500)


def telegram_setup_webhook(request):
    resp = _require_login(request)
    if resp:
        return resp

    webhook_url = request.build_absolute_uri('/api/telegram-webhook')
    success = setup_webhook(webhook_url)
    return JsonResponse({'success': success, 'webhook_url': webhook_url})


def telegram_webhook_info(request):
    resp = _require_login(request)
    if resp:
        return resp

    info = get_webhook_info()
    return JsonResponse(info)


def test_telegram_notification(request):
    resp = _require_login(request)
    if resp:
        return resp

    try:
        success = send_telegram_notification("🔔 Test bildirimi: Sistem çalışıyor.")
        return JsonResponse({'success': success})
    except Exception as e:
        logger.error(f"test_telegram_notification hata: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# TRENDYOL ORDER WEBHOOK (otomatik stok düşürme)
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def trendyol_order_webhook(request):
    """
    Trendyol'dan gelen sipariş webhook'unu işler.
    
    Akış:
    1. Authentication kontrolü (API Key veya Basic Auth)
    2. Webhook'tan gelen JSON'u parse et
    3. Her line item için:
       - Barcode ile inventory_product bul
       - Product'ın listing_components'larını al
       - Her component için purchase_item.quantity'yi düşür
    4. Sonucu logla
    """
    # HEAD isteği - Trendyol'un URL doğrulaması için (body olmadan)
    if request.method == 'HEAD':
        response = HttpResponse(status=200)
        response['Content-Type'] = 'application/json'
        return response
    
    # GET isteği - Test amaçlı
    if request.method == 'GET':
        return JsonResponse({
            'status': 'ok',
            'service': 'inventory-notification'
        })
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # ═══ BASIC AUTHENTICATION KONTROLÜ ═══
    import base64
    
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Basic '):
        logger.error("❌ Missing or invalid Authorization header")
        return JsonResponse({'error': 'Unauthorized - Basic Auth required'}, status=401)
    
    try:
        # Base64 decode
        encoded_credentials = auth_header.replace('Basic ', '')
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
        
        # Credentials kontrolü
        expected_username = settings.TRENDYOL_WEBHOOK_USERNAME
        expected_password = settings.TRENDYOL_WEBHOOK_PASSWORD
        
        if username != expected_username or password != expected_password:
            logger.error(f"❌ Invalid credentials for user: {username}")
            return JsonResponse({'error': 'Unauthorized - Invalid credentials'}, status=401)
        
        logger.info(f"✅ Basic Auth successful: {username}")
        
    except Exception as e:
        logger.error(f"❌ Basic Auth parsing error: {e}")
        return JsonResponse({'error': 'Unauthorized - Invalid auth format'}, status=401)

    try:
        # Gelen veriyi parse et
        payload = json.loads(request.body)

        # Trendyol gerçek webhook: {"content": [{...}]} formatında gelir
        content = payload.get('content', None)
        if content and isinstance(content, list) and len(content) > 0:
            order_data = content[0]
        else:
            order_data = payload  # curl test / düz format fallback

        order_number = order_data.get('orderNumber', 'UNKNOWN')
        status = order_data.get('shipmentPackageStatus', 'UNKNOWN')
        lines = order_data.get('lines', [])

        logger.info(f"📦 Trendyol Webhook: Order {order_number}, Status: {status}, Lines: {len(lines)}")

        # ═══ DUPLICATE KONTROLÜ ═══
        # Aynı sipariş numarası ile daha önce işlem yapılmış mı?
        existing_log = TrendyolWebhookLog.objects.filter(
            order_number=order_number,
            processed=True
        ).first()
        
        if existing_log:
            logger.warning(f"⚠️ Duplicate webhook: Order {order_number} daha önce işlendi, stok düşürülmeyecek")
            # ⚠️ Duplicate için Telegram bildirimi GÖNDERİLMEZ
            return JsonResponse({
                'success': True,
                'message': f'Sipariş {order_number} daha önce işlendi (duplicate)',
                'order_number': order_number,
                'duplicate': True
            }, status=200)

        # ═══ ÜST-LEVEL LOG — her gelen webhook kaydedilsin ═══
        TrendyolWebhookLog.objects.create(
            order_number=order_number,
            barcode='',
            status=status,
            line_item_status='webhook_received',
            quantity=len(lines),
            success=False,
            processed=False,
            raw_payload=payload
        )

        results = []
        processed_count = 0  # Kaç line item gerçekten işlendi
        
        for line in lines:
            barcode = line.get('barcode')
            quantity = line.get('quantity', 1)
            product_name = line.get('productName', 'N/A')
            line_item_status = line.get('orderLineItemStatusName', 'UNKNOWN')
            
            if not barcode:
                logger.warning(f"⚠️ Barcode bulunamadı: {line}")
                continue
            
            # ═══ SADECE APPROVED OLANLARI İŞLE ═══
            should_process = line_item_status == "Approved"
            
            if not should_process:
                logger.info(f"⏭️ Atlandı: {barcode} - Status: {line_item_status} (Sadece 'Approved' işlenir)")
                # Log kaydet ama stok düşürme
                TrendyolWebhookLog.objects.create(
                    order_number=order_number,
                    barcode=barcode,
                    status=status,
                    line_item_status=line_item_status,
                    quantity=quantity,
                    success=False,
                    processed=False,
                    error_message=f"Atlandı: orderLineItemStatusName '{line_item_status}' (Sadece 'Approved' işlenir)",
                    raw_payload=payload
                )
                results.append({
                    'success': False,
                    'message': f"Atlandı: Status '{line_item_status}'",
                    'barcode': barcode,
                    'line_item_status': line_item_status,
                    'processed': False
                })
                continue
                
            # İşlemi yap ve logla
            result = process_trendyol_order_line(
                order_number=order_number,
                barcode=barcode,
                quantity=quantity,
                status=status,
                line_item_status=line_item_status,
                raw_payload=payload
            )
            results.append(result)
            
            if result.get('processed'):
                processed_count += 1
            
            logger.info(f"{'✅' if result['success'] else '❌'} {barcode}: {result['message']}")

        # Genel özet
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        # ═══ TELEGRAM BİLDİRİMİ ═══
        # Sadece gerçekten stok düşen (processed=True) kayıtlar varsa bildirim gönder
        if results and processed_count > 0:
            try:
                telegram_message = f"🛒 <b>Yeni Trendyol Siparişi</b>\n\n"
                telegram_message += f"📋 Sipariş No: <code>{order_number}</code>\n"
                telegram_message += f"📊 Durum: <b>{status}</b>\n"
                telegram_message += f"📦 Toplam Line: <b>{total_count}</b>\n"
                telegram_message += f"✅ Başarılı: <b>{success_count}</b>\n"
                telegram_message += f"🔄 İşlenen (Stok Düşen): <b>{processed_count}</b>\n\n"
                
                # Her ürün için detay
                for i, result in enumerate(results, 1):
                    # Processed olup olmadığını göster
                    processed_icon = "🔄" if result.get('processed') else "⏭️"
                    
                    if result.get('success'):
                        telegram_message += f"{processed_icon} <b>{i}. {result.get('product_name', 'Ürün')}</b>\n"
                        telegram_message += f"   └ Barkod: <code>{result.get('barcode', 'N/A')}</code>\n"
                        telegram_message += f"   └ Adet: {result.get('order_quantity', 1)}\n"
                        
                        # Line item status göster
                        if result.get('line_item_status'):
                            telegram_message += f"   └ Line Status: {result.get('line_item_status')}\n"
                        
                        # Etkilenen SKU'lar varsa göster
                        affected_items = result.get('affected_items', [])
                        if affected_items:
                            telegram_message += f"   └ Düşürülen SKU'lar:\n"
                            for item in affected_items[:3]:  # İlk 3 SKU
                                telegram_message += f"      • {item['sku_name']}: {item['old_qty']} → {item['new_qty']} (-{item['deducted']})\n"
                            if len(affected_items) > 3:
                                telegram_message += f"      • ... ve {len(affected_items) - 3} SKU daha\n"
                        else:
                            telegram_message += f"   └ ⚠️ Bileşen tanımlı değil, stok düşürülmedi\n"
                        telegram_message += "\n"
                    else:
                        telegram_message += f"❌ {i}. {result.get('message', 'Bilinmeyen hata')}\n"
                        telegram_message += f"   └ Barkod: <code>{result.get('barcode', 'N/A')}</code>\n"
                        if result.get('line_item_status'):
                            telegram_message += f"   └ Line Status: {result.get('line_item_status')}\n"
                        telegram_message += "\n"
                
                # Mesajı gönder
                send_telegram_notification(telegram_message)
                logger.info("✅ Telegram bildirimi gönderildi")
            except Exception as e:
                logger.error(f"❌ Telegram bildirimi gönderilemedi: {e}")
        else:
            # Bildirim gönderilmedi çünkü:
            # - Tüm line item'lar Approved değil VEYA
            # - Hiç ürün işlenemedi
            if results and processed_count == 0:
                logger.info("ℹ️ Telegram bildirimi gönderilmedi: Hiç ürün işlenmedi (tüm line item'lar Approved değil)")
        
        return JsonResponse({
            'success': True,
            'message': f'{success_count}/{total_count} line item işlendi',
            'order_number': order_number,
            'results': results
        }, status=200)

    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON payload")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def process_trendyol_order_line(order_number, barcode, quantity, status, line_item_status, raw_payload):
    """
    Tek bir sipariş satırını işler - stok düşürme mantığı burada.
    Returns:
        dict: {'success': bool, 'message': str, 'processed': bool, 'affected_items': list}
    """
    try:
        # 1. Barcode ile inventory_product bul
        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            TrendyolWebhookLog.objects.create(
                order_number=order_number,
                barcode=barcode,
                status=status,
                line_item_status=line_item_status,
                quantity=quantity,
                success=False,
                processed=False,
                error_message=f"Barkod '{barcode}' sistemde bulunamadı",
                raw_payload=raw_payload
            )
            return {
                'success': False,
                'message': f"Barkod '{barcode}' bulunamadı",
                'barcode': barcode,
                'line_item_status': line_item_status,
                'processed': False
            }

        # 2. Product'ın listing_components'larını al
        components = ListingComponent.objects.filter(
            inventory_product=product
        ).select_related('purchase_item')

        if not components.exists():
            TrendyolWebhookLog.objects.create(
                order_number=order_number,
                barcode=barcode,
                status=status,
                line_item_status=line_item_status,
                quantity=quantity,
                success=True,
                processed=True,
                error_message=f"'{product.name}' için bileşen tanımlı değil (listing_components boş)",
                affected_product_id=product.id,
                raw_payload=raw_payload
            )
            return {
                'success': True,
                'message': f"'{product.name}' için bileşen yok - stok düşürülmedi",
                'barcode': barcode,
                'product_id': product.id,
                'product_name': product.name,
                'order_quantity': quantity,
                'line_item_status': line_item_status,
                'processed': True
            }

        # 3. Her component için purchase_item.quantity'yi düşür
        affected_items = []
        for component in components:
            purchase_item = component.purchase_item
            deduction_amount = component.qty_per_listing * quantity
            old_quantity = purchase_item.quantity
            purchase_item.quantity -= int(deduction_amount)
            if purchase_item.quantity < 0:
                purchase_item.quantity = 0
            purchase_item.save()
            affected_items.append({
                'sku_name': purchase_item.name,
                'sku_barcode': purchase_item.purchase_barcode,
                'old_qty': old_quantity,
                'new_qty': purchase_item.quantity,
                'deducted': int(deduction_amount)
            })

        # 4. Başarılı log kaydet
        TrendyolWebhookLog.objects.create(
            order_number=order_number,
            barcode=barcode,
            status=status,
            line_item_status=line_item_status,
            quantity=quantity,
            success=True,
            processed=True,
            affected_product_id=product.id,
            affected_components=affected_items,
            raw_payload=raw_payload
        )
        return {
            'success': True,
            'message': f"'{product.name}' için {len(affected_items)} SKU stoku düşürüldü",
            'barcode': barcode,
            'product_id': product.id,
            'product_name': product.name,
            'order_quantity': quantity,
            'line_item_status': line_item_status,
            'processed': True,
            'affected_items': affected_items
        }

    except Exception as e:
        TrendyolWebhookLog.objects.create(
            order_number=order_number,
            barcode=barcode,
            status=status,
            line_item_status=line_item_status,
            quantity=quantity,
            success=False,
            processed=False,
            error_message=str(e),
            raw_payload=raw_payload
        )
        logger.error(f"Process error for {barcode}: {e}", exc_info=True)
        return {
            'success': False,
            'message': f"İşlem hatası: {str(e)}",
            'barcode': barcode,
            'line_item_status': line_item_status,
            'processed': False
        }


@csrf_exempt
def test_trendyol_webhook(request):
    """Webhook'u test etmek için örnek sipariş gönderir"""
    test_payload = {
        "orderNumber": "TEST-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "shipmentPackageStatus": "CREATED",
        "lines": [
            {
                "barcode": "1234567890",  # Kendi test barcodunu buraya yaz
                "quantity": 1,
                "productName": "Test Ürün",
                "sku": "TEST-SKU-001",
                "orderLineItemStatusName": "Approved"  # ✅ Approved status ekle
            }
        ]
    }
    
    # Kendi webhook endpoint'ine POST at
    response = trendyol_order_webhook(request.__class__(
        body=json.dumps(test_payload).encode(),
        method='POST'
    ))
    
    return JsonResponse({
        'test_payload': test_payload,
        'webhook_response': json.loads(response.content)
    })
