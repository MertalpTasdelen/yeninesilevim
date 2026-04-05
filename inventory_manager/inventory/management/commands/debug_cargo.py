"""
Belirli bir sipariş için kargo faturasının neden bulunamadığını debug eder.

Kullanım:
    python manage.py debug_cargo --order 10853804864 --start 2026-01-01 --end 2026-01-31

Opsiyonel:
    --wide   : Geniş pencere kullan (start-30 gün / end+60 gün)
"""
import datetime
import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from requests.auth import HTTPBasicAuth
import requests


BASE_URL = "https://apigw.trendyol.com/integration/finance/che/sellers"


def _ts(dt: datetime.datetime) -> int:
    return int(dt.timestamp() * 1000)


def _split_periods(start: datetime.datetime, end: datetime.datetime):
    """Her biri max 15 gün olan periyotlara böler."""
    periods = []
    current = start
    while current < end:
        chunk_end = min(current + datetime.timedelta(days=14, hours=23, minutes=59, seconds=59), end)
        periods.append((current, chunk_end))
        current = chunk_end + datetime.timedelta(seconds=1)
    return periods


class Command(BaseCommand):
    help = "Belirli bir sipariş için kargo debug bilgisi verir"

    def add_arguments(self, parser):
        parser.add_argument("--order", required=True, help="Sipariş numarası (örn: 10853804864)")
        parser.add_argument("--start", required=True, help="Başlangıç tarihi YYYY-MM-DD")
        parser.add_argument("--end", required=True, help="Bitiş tarihi YYYY-MM-DD")
        parser.add_argument(
            "--wide", action="store_true",
            help="Geniş pencere: start-30 gün / end+60 gün"
        )

    def handle(self, *args, **options):
        order_no = str(options["order"])
        start_date = datetime.datetime.strptime(options["start"], "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, tzinfo=datetime.timezone.utc
        )
        end_date = datetime.datetime.strptime(options["end"], "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=datetime.timezone.utc
        )

        seller_id = getattr(settings, "TRENDYOL_SUPPLIER_ID", "") or os.getenv("TRENDYOL_SUPPLIER_ID", "")
        api_key = getattr(settings, "TRENDYOL_API_KEY", "") or os.getenv("TRENDYOL_API_KEY", "")
        api_secret = getattr(settings, "TRENDYOL_API_SECRET", "") or os.getenv("TRENDYOL_API_SECRET", "")

        if not seller_id:
            self.stderr.write(self.style.ERROR("TRENDYOL_SUPPLIER_ID boş! .env dosyasını kontrol et."))
            return

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"DEBUG: Sipariş {order_no} için kargo araştırması")
        self.stdout.write(f"Seller ID: {seller_id}")
        self.stdout.write(f"{'='*70}\n")

        # Arama penceresi
        if options["wide"]:
            cargo_start = start_date - datetime.timedelta(days=30)
            cargo_end = end_date + datetime.timedelta(days=60)
        else:
            cargo_start = start_date - datetime.timedelta(days=7)
            cargo_end = end_date + datetime.timedelta(days=30)

        self.stdout.write(f"Kargo arama penceresi: {cargo_start.date()} → {cargo_end.date()}")
        periods = _split_periods(cargo_start, cargo_end)
        self.stdout.write(f"Toplam {len(periods)} periyot\n")

        auth = HTTPBasicAuth(api_key, api_secret)
        headers = {
            "User-Agent": f"{seller_id}-SelfIntegration",
            "storeFrontCode": "TRENDYOLTR",
            "Content-Type": "application/json",
        }

        # ADIM 1: Settlements'ta sipariş var mı?
        self.stdout.write(f"{'─'*50}")
        self.stdout.write("ADIM 1: Settlements'ta sipariş aranıyor...")

        settle_start = start_date - datetime.timedelta(days=7)
        settle_end = end_date + datetime.timedelta(days=7)
        found_in_settlements = False

        for title, ttype in [("Sale", "Sale"), ("Return", "Return")]:
            page = 0
            while True:
                url = f"{BASE_URL}/{seller_id}/settlements"
                params = {
                    "startDate": _ts(settle_start),
                    "endDate": _ts(settle_end),
                    "transactionType": ttype,
                    "page": page,
                    "size": 500,
                }
                try:
                    r = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:
                    self.stderr.write(f"  {title} çekme hatası: {e}")
                    break

                content = data.get("content") or []
                for item in content:
                    if str(item.get("orderNumber", "")) == order_no:
                        found_in_settlements = True
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✓ Settlements'ta bulundu ({title}): barcode={item.get('barcode')}, "
                            f"sellerRevenue={item.get('sellerRevenue')}, "
                            f"transactionDate={item.get('transactionDate')}"
                        ))

                total_pages = data.get("totalPages", 1)
                if page >= total_pages - 1 or not content:
                    break
                page += 1

        if not found_in_settlements:
            self.stdout.write(self.style.WARNING(
                f"  ✗ Sipariş {order_no} settlements'ta bulunamadı! "
                f"(arama: {settle_start.date()} - {settle_end.date()})"
            ))

        # ADIM 2: DeductionInvoices çek, tüm transactionType'ları logla
        self.stdout.write(f"\n{'─'*50}")
        self.stdout.write("ADIM 2: DeductionInvoices çekiliyor (tüm transactionType'lar listeleniyor)...")

        all_transaction_types = {}
        cargo_serials = []

        for period_start, period_end in periods:
            url = f"{BASE_URL}/{seller_id}/otherfinancials"
            page = 0
            while True:
                params = {
                    "startDate": _ts(period_start),
                    "endDate": _ts(period_end),
                    "transactionType": "DeductionInvoices",
                    "page": page,
                    "size": 500,
                }
                try:
                    r = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:
                    self.stderr.write(f"  Hata ({period_start.date()}): {e}")
                    break

                content = data.get("content") or []
                for record in content:
                    ttype = record.get("transactionType", "BİLİNMİYOR")
                    all_transaction_types[ttype] = all_transaction_types.get(ttype, 0) + 1
                    # Kargo fatura kayıtlarını topla
                    if "kargo" in ttype.lower() or "cargo" in ttype.lower():
                        invoice_id = str(record.get("id", ""))
                        if invoice_id and invoice_id not in [s[0] for s in cargo_serials]:
                            cargo_serials.append((invoice_id, ttype, period_start.date()))

                total_pages = data.get("totalPages", 1)
                if page >= total_pages - 1 or not content:
                    break
                page += 1

        self.stdout.write("\n  Bulunan transactionType'lar:")
        for ttype, count in sorted(all_transaction_types.items(), key=lambda x: -x[1]):
            self.stdout.write(f"    {count:4d} adet  →  '{ttype}'")

        if not cargo_serials:
            self.stdout.write(self.style.ERROR(
                "\n  ✗ Hiç kargo faturası kaydı bulunamadı! "
                "transactionType filtresi yanlış olabilir."
            ))
            self.stdout.write("\n  İpucu: Yukarıdaki transactionType listesine bakın.")
            self.stdout.write("  Şu an filtre: ['Kargo Faturası', 'Kargo Fatura']")
            return

        self.stdout.write(f"\n  {len(cargo_serials)} adet kargo fatura seri no bulundu:")
        for sid, stype, sdate in cargo_serials[:10]:
            self.stdout.write(f"    ID={sid}  type='{stype}'  periyot={sdate}")
        if len(cargo_serials) > 10:
            self.stdout.write(f"    ... ve {len(cargo_serials) - 10} tane daha")

        # ADIM 3: cargo-invoice items'ta sipariş var mı?
        self.stdout.write(f"\n{'─'*50}")
        self.stdout.write(f"ADIM 3: {len(cargo_serials)} kargo faturasında sipariş {order_no} aranıyor...")

        found_in_cargo = False
        all_order_numbers_sample = set()

        for serial_id, serial_type, serial_period in cargo_serials:
            url = f"{BASE_URL}/{seller_id}/cargo-invoice/{serial_id}/items"
            page = 0
            invoice_order_nums = []
            while True:
                params = {"page": page, "size": 500}
                try:
                    r = requests.get(url, params=params, headers=headers, auth=auth, timeout=30)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:
                    self.stderr.write(f"  Fatura {serial_id} hata: {e}")
                    self.stderr.write(f"  URL: {url}")
                    break

                content = data.get("content") or []

                # İlk faturanın tüm field'larını göster
                if page == 0 and content and not all_order_numbers_sample:
                    self.stdout.write(f"\n  İlk fatura ({serial_id}) ilk item field'ları:")
                    self.stdout.write(f"  {list(content[0].keys())}")

                for item in content:
                    # Olası orderNumber field isimlerini dene
                    for field in ["orderNumber", "orderId", "orderNo", "order_number"]:
                        val = str(item.get(field, ""))
                        if val:
                            invoice_order_nums.append(val)
                            all_order_numbers_sample.add(val)
                            if val == order_no:
                                found_in_cargo = True
                                amount = item.get("amount", item.get("cost", item.get("fee", "?")))
                                self.stdout.write(self.style.SUCCESS(
                                    f"\n  ✓ BULUNDU! Fatura={serial_id}, field={field}, "
                                    f"orderNumber={val}, amount={amount}"
                                ))
                                self.stdout.write(f"  Tam satır: {json.dumps(item, ensure_ascii=False)}")
                            break

                total_pages = data.get("totalPages", 1)
                if page >= total_pages - 1 or not content:
                    break
                page += 1

            if invoice_order_nums and order_no not in invoice_order_nums:
                # Benzer sipariş numarası var mı?
                similar = [n for n in invoice_order_nums if order_no[:5] in n]
                if similar:
                    self.stdout.write(f"  Fatura {serial_id}: benzer numara var: {similar[:3]}")

        if not found_in_cargo:
            self.stdout.write(self.style.ERROR(
                f"\n  ✗ Sipariş {order_no} hiçbir kargo faturasında bulunamadı."
            ))
            # Örnek sipariş numaraları göster
            if all_order_numbers_sample:
                sample = list(all_order_numbers_sample)[:5]
                self.stdout.write(f"  Faturalarda bulunan örnek sipariş numaraları: {sample}")
                self.stdout.write(f"  Toplam {len(all_order_numbers_sample)} benzersiz sipariş numarası")
            else:
                self.stdout.write("  Hiç sipariş numarası bulunamadı - API yanıt yapısı beklenenden farklı olabilir.")

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write("DEBUG tamamlandı.")
        self.stdout.write(f"{'='*70}\n")
