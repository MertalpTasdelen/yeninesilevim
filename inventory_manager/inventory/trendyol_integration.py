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
import logging

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
    response = requests.get(
        url, params=params, headers=headers, auth=auth, timeout=30)
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
    user_agent: str = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Dict[str, float]:
    """
    Kargo faturalarını Trendyol API üzerinden çekerek sipariş numarasına göre
    kargo ücretlerini toplar.

    Adımlar:
    1. /otherfinancials endpoint'inden DeductionInvoices çağrısı yapılır.
    2. 'transactionType' değeri 'Kargo Fatura' veya 'Kargo Faturası' olan
       kayıtların 'id' alanları alınır.
    3. Her id için /cargo-invoice/{invoiceSerialNumber}/items çağrısı yapılır.
    4. Dönüşte 'shipmentPackageType' == 'Gönderi Kargo Bedeli' olan
       satırlardaki 'orderNumber' ve 'amount' alanları eşleştirilir.
    5. Aynı sipariş birden fazla satıra sahipse amount toplanır.
    6. Bütün sayfalar işlenene kadar döngü devam eder.
    """

    # Initialize the result dictionary
    shipping_fees: Dict[str, float] = {}

    # Base URL for /otherfinancials endpoint
    url_financials = f"{base_url}/{seller_id}/otherfinancials"

    # Prepare common headers and auth once
    headers = {
        "User-Agent": user_agent or f"{seller_id}-Integration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }
    auth = HTTPBasicAuth(api_key, api_secret)

    try:
        logger.info("STEP 1: /otherfinancials endpoint'ine istek gönderilmeye başlanıyor...")
        current_page: int = page
        total_pages: Optional[int] = None

        # Continue fetching pages until all pages are processed
        while True:
            # Set pagination parameters for this iteration
            params = {
                "startDate": start_date,
                "endDate": end_date,
                "transactionType": "DeductionInvoices",
                "page": current_page,
                "size": size,
            }

            response = requests.get(
                url_financials, params=params, headers=headers, auth=auth, timeout=30
            )
            response.raise_for_status()
            data = response.json() or {}

            # Determine total pages from response if available
            if total_pages is None:
                total_pages = data.get("totalPages")

            content = data.get("content", []) or []
            logger.info(
                f"STEP 2.{current_page}: /otherfinancials yanıtı alındı. Sayfa başına kayıt sayısı: {len(content)}"
            )

            # Filter records with transactionType matching cargo invoice names
            cargo_invoices = [
                item
                for item in content
                if str(item.get("transactionType", "")).lower().replace("ı", "i")
                in ["kargo fatura", "kargo faturasi"]
            ]
            logger.info(
                f"STEP 3.{current_page}: Bu sayfada kargo faturası olarak eşleşen kayıt sayısı: {len(cargo_invoices)}"
            )

            # For each cargo invoice, fetch its detail items
            for idx, invoice in enumerate(cargo_invoices, start=1):
                invoice_id = invoice.get("id")
                if not invoice_id:
                    logger.warning(
                        f"STEP 3.{current_page}.{idx}: Geçersiz id tespit edildi, kayıt atlandı."
                    )
                    continue
                url_cargo = f"{base_url}/{seller_id}/cargo-invoice/{invoice_id}/items"
                try:
                    logger.info(
                        f"STEP 4.{current_page}.{idx}: Kargo faturası detayları çekiliyor -> ID: {invoice_id}"
                    )
                    resp_cargo = requests.get(
                        url_cargo, headers=headers, auth=auth, timeout=30
                    )
                    resp_cargo.raise_for_status()
                    cargo_json = resp_cargo.json() or {}
                    cargo_items = cargo_json.get("content", []) or []

                    # Filter for 'Gönderi Kargo Bedeli' items and accumulate amounts per order
                    for item in cargo_items:
                        if item.get("shipmentPackageType") == "Gönderi Kargo Bedeli":
                            order_no = item.get("orderNumber")
                            amount = item.get("amount")
                            if not order_no or amount is None:
                                continue
                            current_amount = shipping_fees.get(order_no, 0.0)
                            shipping_fees[order_no] = round(current_amount + float(amount), 2)

                    logger.info(
                        f"STEP 5.{current_page}.{idx}: {invoice_id} için {len(cargo_items)} adet item işlendi."
                    )
                except requests.HTTPError as e:
                    logger.error(
                        f"STEP 4.{current_page}.{idx} HTTP hatası: {str(e)} | ID: {invoice_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"STEP 4.{current_page}.{idx} beklenmeyen hata: {str(e)} | ID: {invoice_id}"
                    )

            # Determine if we should fetch next page
            current_page += 1
            # Break if content is empty or we have processed all pages
            if not content:
                logger.info(
                    f"STEP 6: Daha fazla kayıt yok. Toplam {len(shipping_fees)} sipariş numarası için kargo ücreti toplandı."
                )
                break
            if total_pages is not None and current_page >= total_pages:
                logger.info(
                    f"STEP 6: Son sayfa işlendi. Toplam {len(shipping_fees)} sipariş numarası için kargo ücreti toplandı."
                )
                break

    except requests.HTTPError as e:
        logger.error(f"HTTP hatası (/otherfinancials): {str(e)}")
    except Exception as e:
        logger.error(f"Genel hata (/otherfinancials): {str(e)}")

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