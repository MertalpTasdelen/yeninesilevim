from typing import List, Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
import logging
import datetime
from .models import Product

TURKISH_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

logger = logging.getLogger(__name__)


def fetch_settlements(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: int,
    end_date: int,
    transaction_type: str = "Sale",
    page: int = 0,
    size: int = 500,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Dict[str, Any]:
    url = f"{base_url}/{seller_id}/settlements"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "transactionType": transaction_type,
        "page": page,
        "size": size,
    }
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    auth = HTTPBasicAuth(api_key, api_secret)
    response = requests.get(
        url, params=params, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_other_financials(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: int,
    end_date: int,
    transaction_type: str,
    page: int = 0,
    size: int = 500,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Dict[str, Any]:
    url = f"{base_url}/{seller_id}/otherfinancials"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "transactionType": transaction_type,
        "page": page,
        "size": size,
    }
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    auth = HTTPBasicAuth(api_key, api_secret)
    response = requests.get(
        url, params=params, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_cargo_invoice_items(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    invoice_serial_number: str,
    page: int = 0,
    size: int = 500,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Dict[str, Any]:
    url = f"{base_url}/{seller_id}/cargo-invoice/{invoice_serial_number}/items"
    params = {
        "page": page,
        "size": size,
    }
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    auth = HTTPBasicAuth(api_key, api_secret)
    response = requests.get(
        url, params=params, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_order_by_number(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    order_number: str,
    start_date_ms: Optional[int] = None,
    end_date_ms: Optional[int] = None,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    orders_base_url: str = "https://apigw.trendyol.com/integration/order/sellers",
) -> Dict[str, Any]:
    """
    Fetches a shipment package by orderNumber.
    Orders API only supports the last ~1 month; pass start_date_ms/end_date_ms
    (millisecond timestamps) so older orders can be found.
    """
    url = f"{orders_base_url}/{seller_id}/orders"
    params: Dict[str, Any] = {"orderNumber": order_number}
    if start_date_ms is not None:
        params["startDate"] = start_date_ms
    if end_date_ms is not None:
        params["endDate"] = end_date_ms
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    auth = HTTPBasicAuth(api_key, api_secret)
    response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    return response.json()


def create_15day_periods(
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    extra_days_before: int = 7,
    extra_days_after: int = 60,
) -> List[tuple]:
    """
    Kargo faturaları satış tarihinden farklı bir tarihte kesilebilir.
    Arama penceresi start_date'den extra_days_before gün öncesine,
    end_date'den extra_days_after gün sonrasına genişletilir.
    """
    cargo_start = start_date - datetime.timedelta(days=extra_days_before)
    cargo_end = end_date + datetime.timedelta(days=extra_days_after)
    periods = _split_into_15day_periods(cargo_start, cargo_end)
    logger.info(
        f"Kargo arama penceresi: {cargo_start.date()} - {cargo_end.date()} "
        f"({len(periods)} periyot)"
    )
    return periods


def fetch_all_sales(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: int,
    end_date: int,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> List[Dict[str, Any]]:
    
    logger.info("ADIM 1: TÜM SATIŞLAR ÇEKİLİYOR")
    all_sales: List[Dict[str, Any]] = []
    page = 0
    size = 500
    
    while True:
        try:
            response_data = fetch_settlements(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                start_date=start_date,
                end_date=end_date,
                transaction_type="Sale",
                page=page,
                size=size,
                store_front_code=store_front_code,
                user_agent=user_agent,
                base_url=base_url,
            )
            
            if isinstance(response_data, dict):
                content = response_data.get("content", []) or []
                all_sales.extend(content)
                
                logger.info(f"  Sayfa {page}: {len(content)} satış kaydı çekildi")
                
                if not content or len(content) < size:
                    break
                
                page += 1
            else:
                break
                
        except Exception as e:
            logger.error(f"Satış çekilirken hata (Sayfa {page}): {str(e)}")
            break
    
    logger.info(f"ADIM 1 Tamamlandı: Toplam {len(all_sales)} satış kaydı")
    return all_sales


def fetch_deduction_invoices_for_period(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: int,
    end_date: int,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> List[Dict[str, Any]]:
    
    all_deductions: List[Dict[str, Any]] = []
    page = 0
    size = 500
    
    while True:
        try:
            response_data = fetch_other_financials(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                start_date=start_date,
                end_date=end_date,
                transaction_type="DeductionInvoices",
                page=page,
                size=size,
                store_front_code=store_front_code,
                user_agent=user_agent,
                base_url=base_url,
            )
            
            if isinstance(response_data, dict):
                content = response_data.get("content", []) or []
                all_deductions.extend(content)
                
                logger.info(f"    DeductionInvoices Sayfa {page}: {len(content)} kayıt")
                
                if not content or len(content) < size:
                    break
                
                page += 1
            else:
                break
                
        except Exception as e:
            logger.error(f"DeductionInvoices çekilirken hata (Sayfa {page}): {str(e)}")
            break
    
    return all_deductions


def filter_cargo_invoices(deductions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    
    cargo_invoices: List[Dict[str, Any]] = []
    
    for record in deductions:
        transaction_type = record.get("transactionType", "")
        if transaction_type in ["Kargo Fatura", "Kargo Faturası"]:
            cargo_invoices.append(record)
            logger.info(f"    Kargo Faturası bulundu - ID: {record.get('id')}")
    
    return cargo_invoices


def fetch_cargo_details_for_invoices(
    *,
    cargo_invoices: List[Dict[str, Any]],
    seller_id: str,
    api_key: str,
    api_secret: str,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> List[Dict[str, Any]]:
    
    all_cargo_items: List[Dict[str, Any]] = []
    
    for idx, cargo_invoice in enumerate(cargo_invoices, 1):
        invoice_id = cargo_invoice.get("id")
        if not invoice_id:
            continue
        
        try:
            logger.info(f"      Fatura {idx}/{len(cargo_invoices)}: {invoice_id}")
            
            cargo_response = fetch_cargo_invoice_items(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                invoice_serial_number=str(invoice_id),
                store_front_code=store_front_code,
                user_agent=user_agent,
                base_url=base_url,
            )
            
            if isinstance(cargo_response, dict):
                items = cargo_response.get("content", []) or []
                all_cargo_items.extend(items)
                logger.info(f"        Fatura {invoice_id}: {len(items)} ürün bulundu")
                
        except Exception as e:
            logger.error(f"        Fatura {invoice_id} çekilirken hata: {str(e)}")
            continue
    
    return all_cargo_items


def fetch_all_cargo_from_periods(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    periods: List[tuple],
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> List[Dict[str, Any]]:
    
    logger.info("ADIM 2: 15 GÜNLÜK 3 PERİYOT OLUŞTURULUYOR")
    for idx, (p_start, p_end) in enumerate(periods, 1):
        logger.info(f"  Periyot {idx}: {p_start.date()} - {p_end.date()}")
    
    all_cargo_items: List[Dict[str, Any]] = []
    
    for period_idx, (period_start, period_end) in enumerate(periods, 1):
        logger.info(f"\nPeriyot {period_idx}/{len(periods)} işleniyor: {period_start.date()} - {period_end.date()}")
        
        start_ts = int(period_start.timestamp() * 1000)
        end_ts = int((period_end + datetime.timedelta(days=1)).timestamp() * 1000) - 1
        
        try:
            logger.info(f"  Adım 2: DeductionInvoices çekiliyorsu...")
            period_deductions = fetch_deduction_invoices_for_period(
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                start_date=start_ts,
                end_date=end_ts,
                store_front_code=store_front_code,
                user_agent=user_agent,
                base_url=base_url,
            )
            logger.info(f"  {len(period_deductions)} DeductionInvoices bulundu")
            
            logger.info(f"  Adım 3: Kargo Faturalari filtreleniyor...")
            cargo_invoices_list = filter_cargo_invoices(period_deductions)
            logger.info(f"  {len(cargo_invoices_list)} Kargo Faturası filtrelendi")
            
            logger.info(f"  Adım 4: Kargo detaylari cargo-invoice endpoint'ine gidiliyor...")
            period_cargo_items = fetch_cargo_details_for_invoices(
                cargo_invoices=cargo_invoices_list,
                seller_id=seller_id,
                api_key=api_key,
                api_secret=api_secret,
                store_front_code=store_front_code,
                user_agent=user_agent,
                base_url=base_url,
            )
            all_cargo_items.extend(period_cargo_items)
            logger.info(f"  Periyot {period_idx} Tamamlandı: {len(period_cargo_items)} kargo ürünü")
            
        except Exception as e:
            logger.error(f"Periyot {period_idx} işlenirken hata: {str(e)}")
            continue
    
    logger.info(f"\nTüm Periyotlar Tamamlandı: Toplam {len(all_cargo_items)} kargo ürünü")
    return all_cargo_items


def match_sales_with_cargo(
    sales: List[Dict[str, Any]],
    cargo_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    
    logger.info("ADIM 5: SATIŞLAR VE KARGOLAR EŞLEŞTİRİLİYOR")
    
    cargo_map: Dict[str, float] = {}
    for item in cargo_items:
        order_number = str(item.get("orderNumber", ""))
        if order_number:
            amount = item.get("amount", 0)
            current_amount = cargo_map.get(order_number, 0.0)
            cargo_map[order_number] = round(current_amount + float(amount), 2)
    
    results: List[Dict[str, Any]] = []
    
    for sale in sales:
        barcode = sale.get("barcode")
        order_number = str(sale.get("orderNumber", ""))
        seller_revenue = sale.get("sellerRevenue")
        transaction_date_ms = sale.get("transactionDate")
        
        if not barcode or seller_revenue is None:
            continue
        
        transaction_date = None
        if transaction_date_ms:
            transaction_date = convert_timestamp_to_datetime(transaction_date_ms)
            logger.info(f"Sipariş {order_number} - İşlem Tarihi: {transaction_date}")
        
        purchase_price: float = 0.0
        shipping_fee: float = 0.0
        cargo_found = False
        
        try:
            product = Product.objects.get(barcode=barcode)
            purchase_price = float(product.purchase_price)
        except Product.DoesNotExist:
            pass
        
        if order_number in cargo_map:
            cargo_found = True
            shipping_fee = cargo_map[order_number]
        
        base_profit = float(seller_revenue) - purchase_price
        net_profit = base_profit - shipping_fee
        
        results.append({
            "barcode": barcode,
            "orderNumber": order_number,
            "transactionDate": transaction_date,
            "sellerRevenue": round(float(seller_revenue), 2),
            "purchasePrice": round(purchase_price, 2),
            "shippingFee": shipping_fee,
            "netProfit": round(net_profit, 2),
            "cargoFound": cargo_found,
        })
    
    logger.info(f"ADIM 5 Tamamlandı: {len(results)} satış işlendi")
    cargo_found_count = sum(1 for r in results if r.get('cargoFound'))
    total_net_profit = sum(r.get('netProfit', 0) for r in results)
    logger.info(f"  Kargo Bulundu: {cargo_found_count}")
    logger.info(f"  Kargo Bulunamadı: {len(results) - cargo_found_count}")
    logger.info(f"  Toplam Net Kâr: {round(total_net_profit, 2)} TL")
    
    return results


def create_pivot_results(
    results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    
    pivot_data: Dict[str, Dict[str, Any]] = {}
    
    for result in results:
        order_number = str(result.get("orderNumber", ""))
        
        if order_number not in pivot_data:
            pivot_data[order_number] = {
                "orderNumber": order_number,
                "transactionDate": result.get("transactionDate"),
                "items": [],
                "totalSellerRevenue": 0.0,
                "totalPurchasePrice": 0.0,
                "totalShippingFee": 0.0,
                "cargoFound": False,
            }
        
        pivot_data[order_number]["items"].append({
            "barcode": result.get("barcode"),
            "sellerRevenue": result.get("sellerRevenue"),
            "purchasePrice": result.get("purchasePrice"),
        })
        
        pivot_data[order_number]["totalSellerRevenue"] += float(result.get("sellerRevenue", 0))
        pivot_data[order_number]["totalPurchasePrice"] += float(result.get("purchasePrice", 0))
        pivot_data[order_number]["cargoFound"] = result.get("cargoFound", False)
    
    for order_number, data in pivot_data.items():
        if data["cargoFound"]:
            for result in results:
                if str(result.get("orderNumber", "")) == order_number:
                    data["totalShippingFee"] = float(result.get("shippingFee", 0))
                    break
    
    pivot_results = []
    for order_number in sorted(pivot_data.keys()):
        data = pivot_data[order_number]
        total_net_profit = (
            data["totalSellerRevenue"] - 
            data["totalPurchasePrice"] - 
            data["totalShippingFee"] -
            11
        )
        
        pivot_results.append({
            "orderNumber": order_number,
            "transactionDate": data["transactionDate"],
            "items": data["items"],
            "itemCount": len(data["items"]),
            "totalSellerRevenue": round(data["totalSellerRevenue"], 2),
            "totalPurchasePrice": round(data["totalPurchasePrice"], 2),
            "totalShippingFee": round(data["totalShippingFee"], 2),
            "totalNetProfit": round(total_net_profit, 2),
            "cargoFound": data["cargoFound"],
        })
    
    logger.info(f"Pivot sonuçlar oluşturuldu: {len(pivot_results)} sipariş")
    return pivot_results

def convert_timestamp_to_datetime(timestamp_ms: int) -> datetime.datetime:
    if not timestamp_ms:
        return None
    try:
        return datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)
    except Exception as e:
        logger.error(f"Timestamp dönüşümü hatası: {str(e)}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MONTHLY SUMMARY — new pipeline
# ─────────────────────────────────────────────────────────────────────────────

def _split_into_15day_periods(
    start_date: datetime.datetime,
    end_date: datetime.datetime,
) -> List[tuple]:
    """Split any date range into max-15-day chunks required by the Trendyol API."""
    periods = []
    current = start_date
    while current <= end_date:
        chunk_end = min(current + datetime.timedelta(days=14), end_date)
        periods.append((current, chunk_end))
        current = chunk_end + datetime.timedelta(seconds=1)
    return periods


def fetch_settlements_all_pages(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_ts: int,
    end_ts: int,
    transaction_types: List[str],
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> List[Dict[str, Any]]:
    """Fetch all pages of settlements for multiple transaction types (uses transactionTypes plural param)."""
    url = f"{base_url}/{seller_id}/settlements"
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    auth = HTTPBasicAuth(api_key, api_secret)
    size = 500
    all_items: List[Dict[str, Any]] = []
    page = 0

    while True:
        params = {
            "startDate": start_ts,
            "endDate": end_ts,
            "transactionTypes": ",".join(transaction_types),
            "page": page,
            "size": size,
        }
        try:
            response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"fetch_settlements_all_pages page={page} hata: {e}")
            break

        content = data.get("content", []) or []
        all_items.extend(content)
        total_pages = data.get("totalPages", 1)
        logger.info(f"  settlements page={page}/{total_pages - 1}: {len(content)} kayıt")

        if page >= total_pages - 1 or not content:
            break
        page += 1

    return all_items


def build_cargo_cost_by_order(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Dict[str, float]:
    """
    Returns {orderNumber: total_cargo_cost} by:
    1. Fetching DeductionInvoices across 15-day periods
    2. Filtering records where transactionType is 'Kargo Faturası' / 'Kargo Fatura'
    3. Fetching cargo-invoice items for each invoice serial

    Kargo faturaları sipariş tarihinden 2-3 ay sonra kesilebilir;
    bu yüzden arama penceresi start_date-7 / end_date+120 olarak genişletilir.
    """
    cargo_start = start_date - datetime.timedelta(days=7)
    cargo_end = end_date + datetime.timedelta(days=120)
    logger.info(
        f"build_cargo_cost_by_order arama penceresi: "
        f"{cargo_start.date()} - {cargo_end.date()}"
    )
    periods = _split_into_15day_periods(cargo_start, cargo_end)
    seen_serials: set = set()
    serials: List[str] = []

    for period_start, period_end in periods:
        start_ts = int(period_start.timestamp() * 1000)
        end_ts = int(period_end.timestamp() * 1000)
        deductions = fetch_deduction_invoices_for_period(
            seller_id=seller_id,
            api_key=api_key,
            api_secret=api_secret,
            start_date=start_ts,
            end_date=end_ts,
            store_front_code=store_front_code,
            user_agent=user_agent,
            base_url=base_url,
        )
        for record in deductions:
            if "kargo fatura" in (record.get("transactionType") or "").lower():
                invoice_id = str(record.get("id", ""))
                if invoice_id and invoice_id not in seen_serials:
                    serials.append(invoice_id)
                    seen_serials.add(invoice_id)

    logger.info(f"build_cargo_cost_by_order: {len(serials)} adet kargo faturası seri no bulundu")

    cargo_by_order: Dict[str, float] = {}

    for serial in serials:
        page = 0
        size = 500
        while True:
            try:
                resp = fetch_cargo_invoice_items(
                    seller_id=seller_id,
                    api_key=api_key,
                    api_secret=api_secret,
                    invoice_serial_number=serial,
                    page=page,
                    size=size,
                    store_front_code=store_front_code,
                    user_agent=user_agent,
                    base_url=base_url,
                )
            except Exception as e:
                logger.error(f"  kargo faturası {serial} page={page} hata: {e}")
                break

            content = resp.get("content", []) or []
            for item in content:
                order_num = str(item.get("orderNumber", ""))
                amount = float(item.get("amount", 0) or 0)
                if order_num:
                    cargo_by_order[order_num] = round(
                        cargo_by_order.get(order_num, 0.0) + amount, 2
                    )

            total_pages = resp.get("totalPages", 1)
            if page >= total_pages - 1 or not content:
                break
            page += 1

    logger.info(f"build_cargo_cost_by_order: {len(cargo_by_order)} sipariş için kargo maliyeti hesaplandı")
    return cargo_by_order


def get_cargo_cost_for_order(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    order_number: str,
    reference_date: datetime.datetime,
    scan_window_days: int = 90,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Optional[float]:
    """
    Belirli bir sipariş için kargo maliyetini döner.

    Trendyol API akışı (docs):
      1. Current Account Statement — otherfinancials?transactionType=DeductionInvoices
         → transactionType='Kargo Fatura' kayıtlarının 'id' alanı = invoiceSerialNumber
      2. Cargo Invoice Details — cargo-invoice/{invoiceSerialNumber}/items
         → orderNumber eşleşmesi ile amount (₺) bulunur

    Args:
        reference_date:   Siparişin settlement/teslim tarihi (arama merkezi).
        scan_window_days: reference_date'ten kaç gün sonraya kadar taransın.
                          Kargo faturaları gecikmeli kesilebilir; varsayılan 90 gün.

    Returns:
        float — kargo tutarı (₺), veya None (bu sipariş için Kargo Faturası bulunamadı).

    NOT: whoPays=None (Trendyol kargo öder) siparişler için Kargo Faturası
    hiçbir zaman DeductionInvoices'ta görünmez → return None beklenen sonuçtur.
    """
    cargo_map = build_cargo_cost_by_order(
        seller_id=seller_id,
        api_key=api_key,
        api_secret=api_secret,
        start_date=reference_date,
        end_date=reference_date + datetime.timedelta(days=scan_window_days),
        store_front_code=store_front_code,
        user_agent=user_agent,
        base_url=base_url,
    )
    return cargo_map.get(order_number)


def fetch_delivered_orders_without_cargo(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    legal_days: int = 7,
    lookback_days: int = 90,
    min_days: int = 60,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> List[Dict[str, Any]]:
    """
    DELIVERED veya RETURNED olmuş siparişler arasında kargo faturası
    henüz kesilmemiş olanları döner.

    Yasal süre (VUK md.231/5): teslimden itibaren 7 gün.
    Yalnızca yasal süreyi aşmış siparişler raporlanır.

    min_days: Settlement'tan bu kadar gün geçmemiş siparişler raporlanmaz.
              Trendyol'un kargo ödediği durumlarda fatura HIÇ kesilmez;
              min_days ile bu siparişleri false-positive olarak raporlamaktan
              kaçınılır. Varsayılan: 60 gün.

    Döner: List[dict] — her eleman:
        {
            order_number: str,
            barcode: str,
            seller_revenue: float,
            transaction_date: datetime,
            transaction_type: str,
            days_since_delivery: int,
            days_overdue: int,
        }
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    # Fatura kesilebilmesi için yasal süre dolmuş olmalı
    cutoff_date = now - datetime.timedelta(days=legal_days)
    # En fazla lookback_days geriye bak
    lookback_start = now - datetime.timedelta(days=lookback_days)

    logger.info(
        f"fetch_delivered_orders_without_cargo: "
        f"{lookback_start.date()} → {cutoff_date.date()} "
        f"(yasal süre={legal_days} gün, lookback={lookback_days} gün, min_days={min_days} gün)"
    )

    # 1. Bu aralıktaki tüm Sale + Return settlement'larını çek
    periods = _split_into_15day_periods(lookback_start, cutoff_date)
    all_settlements: List[Dict[str, Any]] = []

    for period_start, period_end in periods:
        start_ts = int(period_start.timestamp() * 1000)
        end_ts = int(period_end.timestamp() * 1000)
        chunk = fetch_settlements_all_pages(
            seller_id=seller_id,
            api_key=api_key,
            api_secret=api_secret,
            start_ts=start_ts,
            end_ts=end_ts,
            transaction_types=["Sale", "Return"],
            store_front_code=store_front_code,
            user_agent=user_agent,
            base_url=base_url,
        )
        all_settlements.extend(chunk)

    logger.info(f"  {len(all_settlements)} settlement kaydı toplandı")

    # 2. Benzersiz sipariş numaralarını + ilk göründükleri tarihi takip et
    # (aynı sipariş birden fazla satırda çıkabilir — birden fazla ürün)
    order_map: Dict[str, Dict[str, Any]] = {}
    for s in all_settlements:
        order_num = str(s.get("orderNumber", ""))
        if not order_num:
            continue
        tx_ms = s.get("transactionDate")
        tx_dt = convert_timestamp_to_datetime(tx_ms) if tx_ms else None
        if not tx_dt:
            continue

        if order_num not in order_map:
            order_map[order_num] = {
                "order_number": order_num,
                "barcode": s.get("barcode", ""),
                "seller_revenue": 0.0,
                "transaction_date": tx_dt,
                "transaction_type": s.get("transactionType", ""),
            }
        order_map[order_num]["seller_revenue"] += float(s.get("sellerRevenue") or 0)

    logger.info(f"  {len(order_map)} benzersiz sipariş bulundu")

    if not order_map:
        return []

    # 3. Bu siparişler için kargo fatura sorgusunu yap
    # Pencere: lookback_start - 7 gün / cutoff_date (build_cargo_cost_by_order +120 gün ekler)
    cargo_by_order = build_cargo_cost_by_order(
        seller_id=seller_id,
        api_key=api_key,
        api_secret=api_secret,
        start_date=lookback_start - datetime.timedelta(days=7),
        end_date=cutoff_date,
        store_front_code=store_front_code,
        user_agent=user_agent,
        base_url=base_url,
    )

    logger.info(f"  {len(cargo_by_order)} sipariş için kargo faturası bulundu")

    # 4. Kargo faturası gelmeyen siparişleri filtrele
    missing: List[Dict[str, Any]] = []
    for order_num, info in order_map.items():
        if order_num not in cargo_by_order:
            tx_dt = info["transaction_date"]
            days_since = (now - tx_dt).days
            days_overdue = days_since - legal_days
            # min_days'den daha yeni settlement'ları atla —
            # Trendyol kargo ödüyorsa fatura HİÇ kesilmez, false-positive olur
            if days_since < min_days:
                logger.debug(
                    f"  {order_num} atlandı: {days_since} gün önce settle edildi "
                    f"(min_days={min_days})"
                )
                continue
            missing.append({
                "order_number": order_num,
                "barcode": info["barcode"],
                "seller_revenue": round(info["seller_revenue"], 2),
                "transaction_date": tx_dt,
                "transaction_type": info["transaction_type"],
                "days_since_delivery": days_since,
                "days_overdue": days_overdue,
            })

    # En uzun süredir bekleyenler en üstte
    missing.sort(key=lambda x: x["days_overdue"], reverse=True)
    logger.info(f"  Kargo faturası eksik sipariş sayısı: {len(missing)}")
    return missing


def calculate_monthly_summary(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> tuple:
    """
    Aylık kasa özetini hesaplar.

    Geri döndürür:
      (monthly_list: List[Dict], missing_barcodes: List[str])

    Her monthly_list elemanı:
      {month_key, month_label, seller_revenue, cargo_cost, purchase_cost, net_profit}

    Formül: net_profit = seller_revenue - cargo_cost - purchase_cost
    - seller_revenue: settlements API'den dönen sellerRevenue toplamı
      (Sale pozitif, Return negatif — API zaten işaretler)
    - cargo_cost: cargo-invoice/items toplamı (gönderim + iade kargo)
    - purchase_cost: yerel DB'den barcode → purchase_price toplamı
    """
    logger.info("calculate_monthly_summary başlıyor...")

    # 1. Fetch Sale + Return settlements split into 15-day chunks
    periods = _split_into_15day_periods(start_date, end_date)
    all_settlements: List[Dict[str, Any]] = []

    for period_start, period_end in periods:
        start_ts = int(period_start.timestamp() * 1000)
        end_ts = int(period_end.timestamp() * 1000)
        chunk = fetch_settlements_all_pages(
            seller_id=seller_id,
            api_key=api_key,
            api_secret=api_secret,
            start_ts=start_ts,
            end_ts=end_ts,
            transaction_types=["Sale", "Return"],
            store_front_code=store_front_code,
            user_agent=user_agent,
            base_url=base_url,
        )
        all_settlements.extend(chunk)

    logger.info(f"  Toplam {len(all_settlements)} settlement kaydı (Sale + Return)")

    # 2. Build cargo cost per order across full date range
    cargo_by_order = build_cargo_cost_by_order(
        seller_id=seller_id,
        api_key=api_key,
        api_secret=api_secret,
        start_date=start_date,
        end_date=end_date,
        store_front_code=store_front_code,
        user_agent=user_agent,
        base_url=base_url,
    )

    # 3. Process settlements → monthly buckets + order-level pivot
    monthly: Dict[str, Dict[str, Any]] = {}
    orders: Dict[str, Dict[str, Any]] = {}
    missing_barcodes: set = set()
    # Track which orders' cargo cost has been attributed (to avoid double-counting multi-item orders)
    processed_cargo_orders: Dict[str, str] = {}

    for s in all_settlements:
        barcode = s.get("barcode") or ""
        order_number = str(s.get("orderNumber", ""))
        seller_revenue = float(s.get("sellerRevenue") or 0)
        transaction_date_ms = s.get("transactionDate")
        transaction_type = s.get("transactionType", "")

        if not transaction_date_ms:
            continue

        tx_dt = convert_timestamp_to_datetime(transaction_date_ms)
        if not tx_dt:
            continue

        month_key = tx_dt.strftime("%Y-%m")

        if month_key not in monthly:
            monthly[month_key] = {
                "month_key": month_key,
                "month_label": f"{TURKISH_MONTHS[tx_dt.month]} {tx_dt.year}",
                "seller_revenue": 0.0,
                "cargo_cost": 0.0,
                "purchase_cost": 0.0,
                "transaction_fee": 0.0,
                "order_count": 0,
                "net_profit": 0.0,
            }

        # sellerRevenue: positive for Sale, negative for Return (API signs it correctly)
        monthly[month_key]["seller_revenue"] += seller_revenue

        # Purchase cost from local DB
        purchase_price = 0.0
        if barcode:
            try:
                product = Product.objects.get(barcode=barcode)
                purchase_price = float(product.purchase_price or 0)
                if transaction_type in ["Return", "İade"]:
                    monthly[month_key]["purchase_cost"] -= purchase_price
                else:
                    monthly[month_key]["purchase_cost"] += purchase_price
            except Product.DoesNotExist:
                missing_barcodes.add(barcode)

        # Cargo cost + transaction fee — attribute once per order on first encounter
        if order_number and order_number not in processed_cargo_orders:
            cargo_amount = cargo_by_order.get(order_number, 0.0)
            monthly[month_key]["cargo_cost"] += cargo_amount
            monthly[month_key]["transaction_fee"] += 15.0
            monthly[month_key]["order_count"] += 1
            processed_cargo_orders[order_number] = month_key

        # Order-level pivot — built alongside monthly buckets
        if order_number:
            if order_number not in orders:
                orders[order_number] = {
                    "orderNumber": order_number,
                    "transactionDate": tx_dt,
                    "items": [],
                    "totalSellerRevenue": 0.0,
                    "totalPurchasePrice": 0.0,
                }
            orders[order_number]["items"].append({
                "barcode": barcode,
                "sellerRevenue": round(seller_revenue, 2),
                "purchasePrice": round(purchase_price, 2),
                "transactionType": transaction_type,
            })
            orders[order_number]["totalSellerRevenue"] += seller_revenue
            if transaction_type in ["Return", "İade"]:
                orders[order_number]["totalPurchasePrice"] -= purchase_price
            else:
                orders[order_number]["totalPurchasePrice"] += purchase_price

    # 4. Finalize order-level pivot
    for order_number, data in orders.items():
        cargo = cargo_by_order.get(order_number, 0.0)
        data["totalShippingFee"] = round(cargo, 2)
        data["cargoFound"] = cargo > 0
        data["itemCount"] = len(data["items"])
        data["totalNetProfit"] = round(
            data["totalSellerRevenue"] - data["totalPurchasePrice"] - cargo - 15.0, 2
        )
        data["totalSellerRevenue"] = round(data["totalSellerRevenue"], 2)
        data["totalPurchasePrice"] = round(data["totalPurchasePrice"], 2)

    order_list = sorted(
        orders.values(),
        key=lambda x: x.get("transactionDate") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc),
        reverse=True,
    )

    # 5. Calculate net profit and round monthly values
    for data in monthly.values():
        data["net_profit"] = round(
            data["seller_revenue"] - data["cargo_cost"] - data["purchase_cost"] - data["transaction_fee"], 2
        )
        data["seller_revenue"] = round(data["seller_revenue"], 2)
        data["cargo_cost"] = round(data["cargo_cost"], 2)
        data["purchase_cost"] = round(data["purchase_cost"], 2)
        data["transaction_fee"] = round(data["transaction_fee"], 2)

    monthly_list = sorted(monthly.values(), key=lambda x: x["month_key"])
    missing_list = sorted(missing_barcodes)

    logger.info(
        f"calculate_monthly_summary tamamlandı: {len(monthly_list)} ay, "
        f"{len(order_list)} sipariş, {len(missing_list)} eksik barkod"
    )
    return monthly_list, missing_list, order_list