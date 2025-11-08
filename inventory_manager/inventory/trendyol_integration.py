"""
Updated Trendyol integration utilities.

This module wraps calls to the Trendyol Partner API for fetching
settlement records, deduction invoices and related cargo invoice
details.  The original implementation retrieved deduction invoices via
the general ``settlements`` endpoint with ``transactionType`` set to
``"DeductionInvoices"``.  However, according to Trendyol's
documentation, deduction invoices are exposed through a separate
``otherfinancials`` endpoint and should **not** be requested via
``settlements``.  The updated functions below implement this new
endpoint while preserving the existing public API for callers.
"""

from typing import List, Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth

from .models import Product


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
    """Fetch settlement records from Trendyol.

    This function calls the *Current Account Statement* ``/settlements``
    endpoint and returns the parsed JSON response.  Use the
    ``transaction_type`` parameter to filter by ``"Sale"`` or
    ``"Return"``; do **not** pass ``"DeductionInvoices"`` here, as
    deduction invoices are exposed via the ``/otherfinancials`` endpoint.

    Parameters are documented in the original version of this function.
    """
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
    response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
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
    """Fetch miscellaneous financial records from Trendyol.

    Trendyol exposes certain finance records such as deduction invoices
    through its ``/otherfinancials`` endpoint rather than the main
    account statement.  This helper wraps the endpoint and accepts
    the same time range and pagination parameters as
    :func:`fetch_settlements`.  The ``transaction_type`` argument
    specifies which type of records to return (e.g. ``"DeductionInvoices"``).

    Returns
    -------
    dict
        The parsed JSON response from the API.
    """
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
    response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_deduction_invoices(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: int,
    end_date: int,
    page: int = 0,
    size: int = 500,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> List[Dict[str, Any]]:
    """Fetch deduction invoices from Trendyol.

    Deduction invoices are no longer exposed via the ``/settlements``
    endpoint.  This function calls :func:`fetch_other_financials` with
    ``transaction_type="DeductionInvoices"`` and returns the
    ``content`` list from the response.  If the response does not
    conform to the expected structure, an empty list is returned.
    """
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
        return response_data.get("content", []) or []
    return []


def extract_cargo_invoice_numbers(deductions: List[Dict[str, Any]]) -> List[str]:
    """Extract cargo invoice serial numbers from deduction records.

    Iterates over the deduction invoice records and collects the ``Id`` (or
    ``id``) field for those entries whose ``transactionType`` is either
    ``"Kargo Faturası"`` or ``"Kargo Fatura"``.
    """
    invoice_numbers: List[str] = []
    for record in deductions:
        ttype = record.get("transactionType") or record.get("transaction_type")
        if ttype in {"Kargo Faturası", "Kargo Fatura"}:
            invoice_id = record.get("Id") or record.get("id")
            if invoice_id is not None:
                invoice_numbers.append(str(invoice_id))
    return invoice_numbers


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
) -> List[Dict[str, Any]]:
    """Kargo faturası detaylarını çeker"""
    
    url = f"{base_url}/{seller_id}/cargo-invoice/{invoice_serial_number}/items"
    
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    
    auth = HTTPBasicAuth(api_key, api_secret)
    response = requests.get(url, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    
    # Direkt response'u döndür, içeriği build_shipping_fee_map'te işleyeceğiz
    return response.json()

def build_shipping_fee_map(
    *,
    seller_id: str,
    api_key: str,
    api_secret: str,
    start_date: int,
    end_date: int,
    page: int = 0,
    size: int = 500,
    store_front_code: str = "TRENDYOLTR",
    user_agent: Optional[str] = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Dict[str, float]:
    """Kargo ücretlerini sipariş numarasına göre map'ler"""
    
    shipping_fees: Dict[str, float] = {}
    
    # Önce kargo faturalarını al
    url = f"{base_url}/{seller_id}/otherfinancials"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "transactionType": "DeductionInvoices",
        "page": page,
        "size": size,
    }
    
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    
    auth = HTTPBasicAuth(api_key, api_secret)
    
    try:
        # Kargo faturalarını al
        response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
        response.raise_for_status()
        deduction_invoices = response.json()
        
        # Kargo faturalarını filtrele
        cargo_invoices = [
            invoice for invoice in deduction_invoices.get('content', [])
            if invoice.get('transactionType') in ['Kargo Faturası', 'Kargo Fatura']
        ]
        
        print(f"Bulunan kargo faturası sayısı: {len(cargo_invoices)}")
        
        # Her kargo faturası için detayları al
        for invoice in cargo_invoices:
            invoice_id = invoice.get('id')
            if not invoice_id:
                continue
                
            try:
                # Kargo faturası detaylarını al
                cargo_items = fetch_cargo_invoice_items(
                    seller_id=seller_id,
                    api_key=api_key,
                    api_secret=api_secret,
                    invoice_serial_number=str(invoice_id)
                )
                
                # Her bir kargo detayını işle
                for item in cargo_items:
                    order_number = item.get('orderNumber')
                    amount = item.get('amount')
                    
                    if order_number and amount is not None:
                        # Aynı sipariş için birden fazla kargo ücreti olabilir, topla
                        current_amount = shipping_fees.get(order_number, 0.0)
                        shipping_fees[order_number] = current_amount + float(amount)
                        print(f"Kargo ücreti eklendi - Sipariş: {order_number}, Tutar: {amount}")
                        
            except Exception as e:
                print(f"Kargo faturası detayları alınırken hata: {invoice_id} - {str(e)}")
                continue
                
    except Exception as e:
        print(f"Kargo faturaları alınırken hata: {str(e)}")
    
    print(f"Toplam eşleşen sipariş sayısı: {len(shipping_fees)}")
    return shipping_fees


def calculate_profit_with_shipping(
    settlements: List[Dict[str, Any]],
    shipping_fees: Dict[str, float]
) -> List[Dict[str, Any]]:
    """Compute net profit after subtracting purchase and shipping costs.

    Extends :func:`calculate_profit_for_settlements` by allowing a
    precomputed mapping of shipping fees keyed by ``orderNumber``.  For each
    settlement record, this function subtracts both the product's purchase
    price and any associated shipping fee to calculate a final net profit.
    If a product cannot be found in the local database, the purchase price
    and shipping fee are assumed to be zero and the sale is still included
    in the results.
    """
    results: List[Dict[str, Any]] = []
    for record in settlements:
        barcode = record.get("barcode")
        seller_revenue = record.get("sellerRevenue")
        if not barcode or seller_revenue is None:
            continue
        purchase_price: float = 0.0
        shipping_fee: float = 0.0
        product_found = False
        try:
            product = Product.objects.get(barcode=barcode)
            purchase_price = float(product.purchase_price)
            product_found = True
        except Product.DoesNotExist:
            product_found = False
        order_no = record.get("orderNumber")
        if product_found:
            shipping_fee = shipping_fees.get(order_no, 0.0)
        base_profit = float(seller_revenue) - purchase_price
        net_profit = base_profit - shipping_fee
        results.append({
            "barcode": barcode,
            "orderNumber": order_no,
            "sellerRevenue": seller_revenue,
            "purchasePrice": purchase_price,
            "shippingFee": shipping_fee,
            "netProfit": net_profit,
        })
    return results


def calculate_profit_for_settlements(settlements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute net profit for each settlement record.

    Each settlement record returned by Trendyol includes the field
    ``sellerRevenue`` and ``barcode``.  This function subtracts the
    purchase price of the corresponding product from ``sellerRevenue``
    to derive the net profit.  Records without a matching product or
    without revenue information are skipped.
    """
    results: List[Dict[str, Any]] = []
    for record in settlements:
        barcode = record.get("barcode")
        seller_revenue = record.get("sellerRevenue")
        if not barcode or seller_revenue is None:
            continue
        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            continue
        purchase_price = float(product.purchase_price)
        profit = float(seller_revenue) - purchase_price
        results.append({
            "barcode": barcode,
            "orderNumber": record.get("orderNumber"),
            "sellerRevenue": seller_revenue,
            "purchasePrice": purchase_price,
            "profit": profit,
        })
    return results