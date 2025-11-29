"""
Management command to copy data from inventory_product to purchase_items table.
Usage: python manage.py copy_to_purchase_items
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import Product, PurchaseItem


class Command(BaseCommand):
    help = 'Copy products from inventory_product to purchase_items table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear purchase_items table before copying',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be copied without actually copying',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_first = options['clear']

        self.stdout.write(self.style.WARNING('='*70))
        self.stdout.write(self.style.WARNING('INVENTORY_PRODUCT → PURCHASE_ITEMS KOPYALAMA'))
        self.stdout.write(self.style.WARNING('='*70))

        # Mevcut kayıtları say
        product_count = Product.objects.count()
        purchase_item_count = PurchaseItem.objects.count()

        self.stdout.write(f'\n📊 Mevcut Durum:')
        self.stdout.write(f'  - inventory_product tablosu: {product_count} kayıt')
        self.stdout.write(f'  - purchase_items tablosu: {purchase_item_count} kayıt')

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n🔍 DRY-RUN MODU: Hiçbir değişiklik yapılmayacak\n'))

        # Temizleme işlemi
        if clear_first and not dry_run:
            confirm = input('\n⚠️  purchase_items tablosunu temizlemek istediğinize emin misiniz? (yes/no): ')
            if confirm.lower() == 'yes':
                deleted_count = PurchaseItem.objects.all().delete()[0]
                self.stdout.write(self.style.WARNING(f'🗑️  {deleted_count} kayıt silindi'))
            else:
                self.stdout.write(self.style.NOTICE('❌ Temizleme iptal edildi'))
                return

        # Kopyalama işlemi başlat
        self.stdout.write(f'\n🚀 Kopyalama işlemi başlıyor...\n')

        success_count = 0
        skip_count = 0
        error_count = 0

        try:
            with transaction.atomic():
                for product in Product.objects.all():
                    try:
                        # purchase_barcode yoksa normal barcode kullan, o da yoksa id kullan
                        barcode = product.purchase_barcode or product.barcode or f"PROD-{product.id}"

                        if dry_run:
                            # Sadece göster, kaydetme
                            self.stdout.write(
                                f'  ✓ [{product.id}] {product.name[:30]:30} | '
                                f'Barcode: {barcode[:20]:20} | '
                                f'Fiyat: {product.purchase_price:>8} ₺ | '
                                f'Miktar: {product.stock:>4}'
                            )
                            success_count += 1
                            continue

                        # Yeni kayıt oluştur (duplicate barkodlara izin ver)
                        PurchaseItem.objects.create(
                            name=product.name,
                            purchase_barcode=barcode,
                            purchase_price=product.purchase_price,
                            quantity=product.stock,
                            image_url=product.image_url,
                            created_at=product.created_at
                        )

                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ [{product.id}] {product.name[:30]:30} | '
                                f'Barcode: {barcode[:20]:20} | '
                                f'Fiyat: {product.purchase_price:>8} ₺ | '
                                f'Miktar: {product.stock:>4}'
                            )
                        )

                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ [{product.id}] {product.name[:30]:30} - HATA: {str(e)}'
                            )
                        )

                if dry_run:
                    raise Exception("Dry-run mode - rolling back")

        except Exception as e:
            if not dry_run:
                self.stdout.write(self.style.ERROR(f'\n❌ İşlem başarısız: {str(e)}'))
                return

        # Sonuçları göster
        self.stdout.write('\n' + '='*70)
        self.stdout.write('📊 SONUÇ:')
        self.stdout.write('='*70)
        
        if dry_run:
            self.stdout.write(self.style.NOTICE(f'🔍 DRY-RUN tamamlandı (gerçek veri eklenmedi)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Başarılı: {success_count} kayıt'))
        
        self.stdout.write(self.style.WARNING(f'⊗  Atlanan: {skip_count} kayıt (zaten var)'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Hatalı: {error_count} kayıt'))

        # Yeni toplam
        if not dry_run:
            new_total = PurchaseItem.objects.count()
            self.stdout.write(f'\n📈 Yeni purchase_items toplam: {new_total} kayıt')

        self.stdout.write('='*70 + '\n')
