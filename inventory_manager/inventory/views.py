from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import Product, ProfitCalculator
from .forms import ProductForm
from .trendyol_integration import (
    fetch_all_sales,
    create_15day_periods,
    fetch_all_cargo_from_periods,
    match_sales_with_cargo,
    create_pivot_results,
)
import logging
import traceback
import datetime

from webpush import send_group_notification

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
    webpush_context = {'group': 'low_stock'}  # 👈 kritik

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'webpush': webpush_context,
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
    selling_price = request.GET.get('selling_price', '')
    commution = request.GET.get('commution', '')
    
    product = None
    if barcode:
        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            pass
    
    context = {
        'barcode': barcode,
        'selling_price': selling_price,
        'commution': commution,
        'product': product,
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
    try:
        if product.stock < 3 and old_stock >= 3:
            payload = {
                "head": "Stok Uyarısı",
                "body": f"{product.name} ürününün stoğu {product.stock} adetin altına düştü.",
                # Bildirim ikonu (statik ikon dosyan olsun, yoksa path’i değiştir)
                "icon": "/static/img/icons/icon-192x192.png",
                # Bildirime tıklandığında gidilecek URL
                "url": request.build_absolute_uri(reverse('product_list')),
            }
            # "low_stock" grubuna abone olan herkese gönder
            send_group_notification(group_name="low_stock", payload=payload, ttl=1000)
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'stock': product.stock})

    return redirect('product_list')


def trendyol_profit(request):
    resp = _require_login(request)
    if resp:
        return resp

    results = []
    pivot_results = []
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
            # UTC timezone ekle
            start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, tzinfo=datetime.timezone.utc)
            
            logger.info(f"\n{'='*70}")
            logger.info(f"TRENDYOL KÂRI RAPORU İŞLEMİ BAŞLADI")
            logger.info(f"{'='*70}")
            logger.info(f"Seçilen Tarih Aralığı: {start_date} - {end_date}")
            
            seller_id = "973871"
            api_key = "uxKAGmeBsn35z1Pkyszs"
            api_secret = "A8eBLEct9tABS4Q5UB30"
            store_front_code = "TRENDYOLTR"
            user_agent = f"{seller_id}-OzlemFiratTasdelen"
            
            total_days = (end_dt - start_dt).days + 1
            logger.info(f"Toplam Gün Sayısı: {total_days}")
            
            logger.info(f"\n{'='*70}")
            logger.info(f"ADIM 1: TÜM SATIŞLAR ÇEKİLİYOR ({start_date} - {end_date})")
            logger.info(f"{'='*70}")
            
            start_ts = int(start_dt.timestamp() * 1000)
            end_ts = int(end_dt.timestamp() * 1000)
            
            all_sales = fetch_all_sales(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                start_date=start_ts,
                end_date=end_ts,
                store_front_code=store_front_code,
                user_agent=user_agent,
            )
            logger.info(f"Adım 1 Tamamlandı: {len(all_sales)} satış kaydı çekildi")
            
            logger.info(f"\n{'='*70}")
            logger.info(f"ADIM 2-4: 15 GÜNLÜK 3 PERİYOTLA KARGO FATURALARI ÇEKİLİYOR")
            logger.info(f"{'='*70}")
            
            cargo_periods = create_15day_periods(start_dt, end_dt)
            
            all_cargo_items = fetch_all_cargo_from_periods(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                periods=cargo_periods,
                store_front_code=store_front_code,
                user_agent=user_agent,
            )
            
            results = match_sales_with_cargo(all_sales, all_cargo_items)
            
            logger.info(f"Adım 1-4 Tamamlandı: {len(results)} ürün işlendi")
            
            logger.info(f"\n{'='*70}")
            logger.info(f"ADIM 5: SİPARİŞ BAZLI PİVOT TABLOSU OLUŞTURULUYOR")
            logger.info(f"{'='*70}")
            
            pivot_results = create_pivot_results(results)
            
            logger.info(f"\n{'='*70}")
            logger.info(f"ÖZET")
            logger.info(f"{'='*70}")
            logger.info(f"Toplam Satış: {len(all_sales)}")
            logger.info(f"Toplam Kargo Ürünü: {len(all_cargo_items)}")
            logger.info(f"Toplam Ürün Satırı: {len(results)}")
            logger.info(f"Toplam Sipariş: {len(pivot_results)}")
            
            cargo_found_count = sum(1 for r in pivot_results if r.get('cargoFound'))
            cargo_not_found_count = len(pivot_results) - cargo_found_count
            logger.info(f"Kargo Bulunan Sipariş: {cargo_found_count}")
            logger.info(f"Kargo Bulunamayan Sipariş: {cargo_not_found_count}")
            
            total_net_profit = sum(r.get('totalNetProfit', 0) for r in pivot_results)
            logger.info(f"Toplam Net Kâr: {round(total_net_profit, 2)} TL")
            logger.info(f"{'='*70}\n")

        except Exception as e:
            logger.error(f"Trendyol profit hesaplamasında hata: {str(e)}")
            traceback.print_exc()
            results = []
            pivot_results = []

    total_net_profit = 0
    if pivot_results:
        total_net_profit = sum(r.get('totalNetProfit', 0) for r in pivot_results)

    context = {
        'results': results,
        'pivot_results': pivot_results,
        'start_date': start_date,
        'end_date': end_date,
        'total_net_profit': round(total_net_profit, 2)
    }
    return render(request, 'inventory/trendyol_profit.html', context)

def login_view(request):
    error = None
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if password == '123456':
            request.session['is_logged_in'] = True
            return redirect('product_list')
        else:
            error = 'Şifre yanlış'
    
    return render(request, 'inventory/login.html', {'error': error})


def logout_view(request):
    if 'is_logged_in' in request.session:
        del request.session['is_logged_in']
    return redirect('product_list')