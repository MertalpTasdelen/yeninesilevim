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

from typing import List, Dict, Any
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