#!/usr/bin/env python
"""
Trendyol'a webhook kaydeder.

Kullanım:
    python register_trendyol_webhook.py

Gereksinimler:
    - Trendyol Satıcı Paneli -> Hesap Bilgilerim -> Entegrasyon Bilgileri'nden:
      * Supplier ID (Satıcı ID)
      * API Key
      * API Secret
    - Webhook URL'iniz (public erişilebilir olmalı)
"""

import requests
import json
import base64
import os
import sys

# Django settings'i yükle (opsiyonel - .env'den webhook auth için)
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_manager.settings')

try:
    import django
    django.setup()
    from django.conf import settings
    USE_DJANGO_SETTINGS = True
    print("✅ Django settings yüklendi - .env'deki webhook auth kullanılacak")
except:
    USE_DJANGO_SETTINGS = False
    print("⚠️  Django settings yüklenemedi, manuel ayarlar kullanılacak")

# ═══════════════════════════════════════════════════════════════════
# AYARLAR - .env dosyasından okunur veya Django settings'ten alınır
# ═══════════════════════════════════════════════════════════════════

if USE_DJANGO_SETTINGS:
    # Django settings'ten al
    SUPPLIER_ID = settings.TRENDYOL_SUPPLIER_ID
    API_KEY = settings.TRENDYOL_API_KEY
    API_SECRET = settings.TRENDYOL_API_SECRET
    WEBHOOK_URL = "https://yourdomain.com/notify/inventory/"  # Kendi domain'inizi yazın
    WEBHOOK_USERNAME = settings.TRENDYOL_WEBHOOK_USERNAME
    WEBHOOK_PASSWORD = settings.TRENDYOL_WEBHOOK_PASSWORD
    print(f"   Auth Type: BASIC_AUTHENTICATION")
    print(f"   Username: {WEBHOOK_USERNAME}")
else:
    # Manuel olarak .env'den oku
    from dotenv import load_dotenv
    load_dotenv()
    
    SUPPLIER_ID = os.getenv('TRENDYOL_SUPPLIER_ID', '')
    API_KEY = os.getenv('TRENDYOL_API_KEY', '')
    API_SECRET = os.getenv('TRENDYOL_API_SECRET', '')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://yourdomain.com/notify/inventory/')
    WEBHOOK_USERNAME = os.getenv('TRENDYOL_WEBHOOK_USERNAME', 'webhook_admin_2024')
    WEBHOOK_PASSWORD = os.getenv('TRENDYOL_WEBHOOK_PASSWORD', '')

# Hangi statuslarda bildirim almak istiyorsunuz?
# Boş bırakırsanız tüm statuslar otomatik eklenir
SUBSCRIBED_STATUSES = [
    "CREATED",      # Sipariş oluşturuldu - STOK DÜŞÜR
    # "PICKING",      # Paketleniyor
    # "INVOICED",     # Faturalandı
    # "CANCELLED",  # İptal - Stok geri eklenebilir
    # "RETURNED",   # İade - Stok geri eklenebilir
]

# ═══════════════════════════════════════════════════════════════════
# WEBHOOK KAYIT FONKSİYONU
# ═══════════════════════════════════════════════════════════════════

def register_webhook():
    """Trendyol'a webhook kaydeder"""
    
    # Endpoint
    url = f"https://apigw.trendyol.com/integration/webhook/sellers/{SUPPLIER_ID}/webhooks"
    
    # Basic Authentication header
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json",
        "User-Agent": "InventoryManager/1.0"
    }
    
    # Request body
    body = {
        "url": WEBHOOK_URL,
        "authenticationType": "BASIC_AUTHENTICATION",
        "username": WEBHOOK_USERNAME,
        "password": WEBHOOK_PASSWORD,
        "subscribedStatuses": SUBSCRIBED_STATUSES
    }
    
    print("=" * 70)
    print("🚀 TRENDYOL WEBHOOK KAYDI")
    print("=" * 70)
    print(f"Supplier ID: {SUPPLIER_ID}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Auth Type: BASIC_AUTHENTICATION")
    print(f"Username: {WEBHOOK_USERNAME}")
    print(f"Password: {'*' * len(WEBHOOK_PASSWORD)}")
    print(f"Statuses: {', '.join(SUBSCRIBED_STATUSES) if SUBSCRIBED_STATUSES else 'ALL'}")
    print("-" * 70)
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print("-" * 70)
        
        if response.status_code in [200, 201]:
            data = response.json()
            webhook_id = data.get('id', 'N/A')
            print("✅ WEBHOOK BAŞARIYLA KAYDED İ LDİ!")
            print(f"Webhook ID: {webhook_id}")
            print("\n⚠️  ÖNEMLİ: Bu Webhook ID'yi saklayın!")
            print("   Güncelleme veya silme işlemleri için gerekli olacak.")
            return webhook_id
        else:
            print("❌ WEBHOOK KAYDI BAŞARISIZ!")
            print(f"Hata: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ BAĞLANTI HATASI: {e}")
        return None
    finally:
        print("=" * 70)


def list_webhooks():
    """Kayıtlı webhook'ları listeler"""
    url = f"https://apigw.trendyol.com/integration/webhook/sellers/{SUPPLIER_ID}/webhooks"
    
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            webhooks = response.json()
            print("\n📋 KAYITLI WEBHOOK'LAR:")
            print("=" * 70)
            for webhook in webhooks:
                print(f"ID: {webhook.get('id')}")
                print(f"URL: {webhook.get('url')}")
                print(f"Status: {'Active' if webhook.get('active') else 'Inactive'}")
                print(f"Statuses: {webhook.get('subscribedStatuses', [])}")
                print("-" * 70)
        else:
            print(f"❌ Webhook listesi alınamadı: {response.text}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")


def delete_webhook(webhook_id):
    """Webhook'u siler"""
    url = f"https://apigw.trendyol.com/integration/webhook/sellers/{SUPPLIER_ID}/webhooks/{webhook_id}"
    
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 204]:
            print(f"✅ Webhook {webhook_id} silindi!")
        else:
            print(f"❌ Silme başarısız: {response.text}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")


# ═══════════════════════════════════════════════════════════════════
# ANA PROGRAM
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        TRENDYOL WEBHOOK KAYIT ARACI                           ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Seçenekler:
    1. Yeni webhook kaydet
    2. Mevcut webhook'ları listele
    3. Webhook sil
    4. Çıkış
    """)
    
    choice = input("Seçiminiz (1-4): ").strip()
    
    if choice == "1":
        # Ayarları kontrol et
        if not SUPPLIER_ID or not API_KEY or not API_SECRET:
            print("\n❌ HATA: .env dosyasında gerekli değişkenler tanımlı değil!")
            print("Gerekli değişkenler: TRENDYOL_SUPPLIER_ID, TRENDYOL_API_KEY, TRENDYOL_API_SECRET")
            sys.exit(1)
        
        if "yourdomain" in WEBHOOK_URL.lower():
            print("\n❌ HATA: WEBHOOK_URL'i kendi sunucu adresinizle değiştirin!")
            print("   Örnek: https://myserver.com/notify/inventory/")
            sys.exit(1)
        
        register_webhook()
        
    elif choice == "2":
        list_webhooks()
        
    elif choice == "3":
        webhook_id = input("Silinecek Webhook ID: ").strip()
        if webhook_id:
            delete_webhook(webhook_id)
        else:
            print("❌ Webhook ID girmediniz!")
    
    elif choice == "4":
        print("👋 Çıkılıyor...")
        sys.exit(0)
    
    else:
        print("❌ Geçersiz seçim!")
