from typing import List, Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
import logging
import datetime
from .models import Product

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


def create_15day_periods(
    start_date: datetime.datetime,
    end_date: datetime.datetime
) -> List[tuple]:
    periods = []
    
    period1_start = start_date
    period1_end = start_date + datetime.timedelta(days=14)
    periods.append((period1_start, period1_end))
    logger.info(f"Periyot 1 oluşturuldu: {period1_start.date()} - {period1_end.date()}")
    
    period2_start = start_date + datetime.timedelta(days=15)
    period2_end = start_date + datetime.timedelta(days=29)
    periods.append((period2_start, period2_end))
    logger.info(f"Periyot 2 oluşturuldu: {period2_start.date()} - {period2_end.date()}")
    
    period3_start = start_date + datetime.timedelta(days=30)
    period3_end = start_date + datetime.timedelta(days=44)
    periods.append((period3_start, period3_end))
    logger.info(f"Periyot 3 oluşturuldu: {period3_start.date()} - {period3_end.date()}")
    
    logger.info(f"Toplam 3 periyot oluşturuldu")
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
        
        if not barcode or seller_revenue is None:
            continue
        
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
    
    for result in results:
        result['totalNetProfit'] = round(total_net_profit, 2)
    
    return results