"""
Utility functions for integrating with the Trendyol Partner API.

This module encapsulates the logic required to call Trendyol's
Current Account Statement (settlements) endpoint and compute the
net profit for each sale by matching settlement records with
local products stored in the database.  It is intentionally
decoupled from Django views to make the integration logic
reusable and testable.

Note
----
The Trendyol Partner API requires Basic Authentication using your
API key and secret, as well as a `User-Agent` header that identifies
your seller ID and integration type.  Do **not** commit your
credentials to version control.  Instead, provide them at runtime
via environment variables or Django settings.
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
    user_agent: str | None = None,
    base_url: str = "https://apigw.trendyol.com/integration/finance/che/sellers",
) -> Dict[str, Any]:
    """Fetch settlement records from Trendyol.

    Parameters
    ----------
    seller_id : str
        The numeric identifier of your Trendyol store.  This is part of
        the URL path.
    api_key : str
        The Trendyol API key for your seller account.  Used for Basic Auth.
    api_secret : str
        The Trendyol API secret for your seller account.  Used for Basic Auth.
    start_date : int
        Start of the time range (Unix timestamp in milliseconds).  The
        API will return records whose transaction dates are greater than
        or equal to this timestamp.
    end_date : int
        End of the time range (Unix timestamp in milliseconds).  The
        API will return records whose transaction dates are less than or
        equal to this timestamp.
    transaction_type : str, optional
        Either ``"Sale"`` or ``"Return"``.  Defaults to ``"Sale"`` to
        retrieve sales transactions.
    page : int, optional
        Pagination index (zero‑based).  Defaults to 0.
    size : int, optional
        Number of records to return per page.  Acceptable values are
        500 or 1000.  Defaults to 500.
    store_front_code : str, optional
        The storefront code (e.g. ``"TRENDYOLTR"``) to specify the
        marketplace.  Defaults to ``"TRENDYOLTR"``.
    user_agent : str, optional
        A custom ``User-Agent`` header identifying your seller ID and
        integration.  If not provided, a sensible default of
        ``"{seller_id}-SelfIntegration"`` is used.
    base_url : str, optional
        Base endpoint for the finance integration.  You should not need
        to change this unless Trendyol modifies their API domains.

    Returns
    -------
    dict
        Parsed JSON response from Trendyol containing settlement records.

    Raises
    ------
    requests.HTTPError
        If the request fails with an HTTP error status.
    requests.RequestException
        For any other network related errors.
    """
    # Construct full endpoint URL
    url = f"{base_url}/{seller_id}/settlements"

    # Assemble query parameters according to Trendyol API spec
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "transactionType": transaction_type,
        "page": page,
        "size": size,
    }

    # Compose required headers
    headers = {
        "User-Agent": user_agent or f"{seller_id}-SelfIntegration",
        "storeFrontCode": store_front_code,
        "Content-Type": "application/json",
    }

    # Use Basic Auth with API key and secret
    auth = HTTPBasicAuth(api_key, api_secret)

    # Issue GET request
    response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
    # Raise an exception for non‑2xx status codes
    response.raise_for_status()
    return response.json()


# -----------------------------------------------------------------------------
# Additional utilities for pulling deduction invoices and cargo invoice items
#
# Trendyol issues separate invoices for shipping costs (kargo faturası).  These
# invoices are not returned alongside sales settlements; instead, you must
# request the ``DeductionInvoices`` transaction type via the Current Account
# Statement API to obtain the invoice serial numbers.  According to the
# documentation, any record in the ``DeductionInvoices`` response whose
# ``transactionType`` is ``"Kargo Faturası"`` or ``"Kargo Fatura"`` has an
# ``Id`` field that corresponds to the ``invoiceSerialNumber`` for that cargo
# invoice【386676864912269†L54-L59】.  Once you have the serial number, you can
# call the cargo‑invoice endpoint to retrieve detailed line items, including
# shipment package type and amount【386676864912269†L61-L96】.  The helper
# functions below encapsulate these steps.

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
    """Fetch deduction invoices from Trendyol using otherfinancials endpoint."""
    
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
    response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    if isinstance(data, dict):
        return data.get("content", []) or []
    return []


def extract_cargo_invoice_numbers(deductions: List[Dict[str, Any]]) -> List[str]:
    """Extract cargo invoice serial numbers from deduction records.

    Iterates over the deduction invoice records and collects the ``Id`` (or
    ``id``) field for those entries whose ``transactionType`` is either
    ``"Kargo Faturası"`` or ``"Kargo Fatura"``【386676864912269†L54-L59】.

    Parameters
    ----------
    deductions : list of dict
        Records returned by :func:`fetch_deduction_invoices`.

    Returns
    -------
    list of str
        A list of invoice serial numbers as strings.
    """
    invoice_numbers: List[str] = []
    for record in deductions:
        ttype = record.get("transactionType") or record.get("transaction_type")
        if ttype in {"Kargo Faturası", "Kargo Fatura"}:
            # some responses use 'Id', others 'id'; attempt both
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
    """Fetch items for a specific cargo invoice.

    Given an ``invoice_serial_number``, this function calls the Trendyol
    cargo invoice items endpoint and returns the ``content`` list of
    line items【386676864912269†L61-L96】.

    Parameters
    ----------
    seller_id, api_key, api_secret : str
        Credentials and seller identifier required for Basic Auth.
    invoice_serial_number : str
        Serial number of the cargo invoice as obtained from
        :func:`extract_cargo_invoice_numbers`.
    page, size : int, optional
        Pagination parameters.  Defaults align with other API calls.
    store_front_code : str, optional
        The storefront code.  Included for consistency; not required
        by the cargo invoice endpoint but accepted in practice.
    user_agent : str, optional
        Custom user agent header.  If not provided a default of
        ``"{seller_id}-SelfIntegration"`` is used.
    base_url : str, optional
        Base path for Trendyol finance integration.  Override only if
        Trendyol changes domains.

    Returns
    -------
    list of dict
        List of cargo invoice item dictionaries.
    """
    # Build the cargo invoice endpoint URL
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
    response = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        return data.get("content", []) or []
    return []


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
    """Retrieve cargo invoices and aggregate shipping fees per order.

    This helper orchestrates the entire flow of fetching deduction invoices,
    extracting cargo invoice serial numbers, fetching the corresponding cargo
    invoice items, and summing the amounts for shipment package type
    ``"Gönderi Kargo Bedeli"`` by order number【386676864912269†L61-L96】.

    Parameters
    ----------
    seller_id, api_key, api_secret : str
        Credentials for Trendyol API.
    start_date, end_date : int
        Time range in milliseconds (Unix epoch) to search for deduction
        invoices.  The same timestamps used for settlements should be
        provided to ensure matching orders.
    page, size, store_front_code, user_agent, base_url
        Optional parameters forwarded to the underlying fetch functions.

    Returns
    -------
    dict
        A mapping from order numbers to their total shipping fee (float).
    """
    shipping_fees: Dict[str, float] = {}
    deductions = fetch_deduction_invoices(
        seller_id=seller_id,
        api_key=api_key,
        api_secret=api_secret,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
        store_front_code=store_front_code,
        user_agent=user_agent,
        base_url=base_url,
    )
    invoice_numbers = extract_cargo_invoice_numbers(deductions)
    for inv in invoice_numbers:
        items = fetch_cargo_invoice_items(
            seller_id=seller_id,
            api_key=api_key,
            api_secret=api_secret,
            invoice_serial_number=inv,
            page=page,
            size=size,
            store_front_code=store_front_code,
            user_agent=user_agent,
            base_url=base_url,
        )
        for item in items:
            # We're interested only in shipping charges of type "Gönderi Kargo Bedeli"
            if item.get("shipmentPackageType") == "Gönderi Kargo Bedeli":
                order_no = item.get("orderNumber")
                amt = item.get("amount")
                if order_no and amt is not None:
                    shipping_fees[order_no] = shipping_fees.get(order_no, 0.0) + float(amt)
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

    Parameters
    ----------
    settlements : list of dict
        Records returned from the settlements API (``content`` list).
    shipping_fees : dict
        Mapping from order number to shipping fee (float) built by
        :func:`build_shipping_fee_map`.

    Returns
    -------
    list of dict
        A list of dictionaries with additional fields ``purchasePrice``,
        ``shippingFee`` and ``netProfit`` alongside the standard settlement fields.
    """
    results: List[Dict[str, Any]] = []
    for record in settlements:
        barcode = record.get("barcode")
        seller_revenue = record.get("sellerRevenue")
        if not barcode or seller_revenue is None:
            # Skip entries without a barcode or revenue field
            continue
        # Default values if the product is not present in our database
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
            # Only apply shipping fee when a product match exists
            shipping_fee = shipping_fees.get(order_no, 0.0)
        # Profit before shipping
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

    Parameters
    ----------
    settlements : list of dict
        The ``content`` list from the Trendyol settlements API response.

    Returns
    -------
    list of dict
        A list of dictionaries containing fields:
        ``barcode``, ``orderNumber``, ``sellerRevenue``, ``purchasePrice``
        and ``profit``.  ``profit`` is the difference between
        ``sellerRevenue`` and the product's purchase price.
    """
    results: List[Dict[str, Any]] = []
    for record in settlements:
        barcode = record.get("barcode")
        seller_revenue = record.get("sellerRevenue")
        if not barcode or seller_revenue is None:
            continue  # Skip records without barcode or revenue
        try:
            product = Product.objects.get(barcode=barcode)
        except Product.DoesNotExist:
            continue  # Skip if there is no local product with this barcode
        # Convert both values to float for arithmetic; Django Decimal cannot
        # be reliably subtracted from float
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