#!/usr/bin/env python
"""
Trendyol Webhook Authentication Test Scripti

Bu script webhook endpoint'inizin Basic Authentication kontrolünü test eder.
"""

import requests
import json
import base64

# ═══════════════════════════════════════════════════════════════════
# TEST AYARLARI
# ═══════════════════════════════════════════════════════════════════

WEBHOOK_URL = "https://yeninesilevim.com/notify/inventory/"  # Kendi URL'iniz
# WEBHOOK_URL = "http://localhost:8000/notify/inventory/"  # Local test için

# Basic Authentication test
TEST_USERNAME = "webhook_admin_2024"
TEST_PASSWORD = "VeryStr0ng!P@ssw0rd#2024"

# ═══════════════════════════════════════════════════════════════════
# TEST SİPARİŞ PAYLOAD
# ═══════════════════════════════════════════════════════════════════

test_order = {
    "orderNumber": "TEST-ORDER-123456",
    "shipmentPackageStatus": "CREATED",
    "lines": [
        {
            "barcode": "1234567890",  # Sisteminizdeki gerçek bir barcode ile değiştirin
            "quantity": 1,
            "productName": "Test Ürün",
            "sku": "TEST-SKU-001"
        }
    ]
}

# ═══════════════════════════════════════════════════════════════════
# TEST FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════════

def test_basic_auth():
    """Basic Authentication test"""
    print("\n" + "=" * 70)
    print("🔐 TEST 1: BASIC AUTHENTICATION (DOĞRU CREDENTIALS)")
    print("=" * 70)
    
    # Basic Auth header oluştur
    credentials = f"{TEST_USERNAME}:{TEST_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    print(f"URL: {WEBHOOK_URL}")
    print(f"Username: {TEST_USERNAME}")
    print(f"Password: {'*' * len(TEST_PASSWORD)}")
    print("-" * 70)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=test_order,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ TEST BAŞARILI - Basic Auth doğru çalışıyor!")
        elif response.status_code == 401:
            print("\n❌ AUTHENTICATION BAŞARISIZ - Kullanıcı adı/şifre yanlış!")
        else:
            print(f"\n⚠️  Beklenmeyen durum kodu: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ BAĞLANTI HATASI: {e}")
    
    print("=" * 70)


def test_no_auth():
    """Authentication olmadan test (başarısız olmalı)"""
    print("\n" + "=" * 70)
    print("🚫 TEST 2: AUTHENTICATION OLMADAN (BAŞARISIZ OLMALI)")
    print("=" * 70)
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"URL: {WEBHOOK_URL}")
    print("Auth: YOK")
    print("-" * 70)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=test_order,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("\n✅ GÜVENLIK TEST BAŞARILI - Auth olmadan erişim engellendi!")
        elif response.status_code == 200:
            print("\n⚠️  UYARI: Auth olmadan erişim başarılı - güvenlik açığı olabilir!")
        else:
            print(f"\n⚠️  Beklenmeyen durum kodu: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ BAĞLANTI HATASI: {e}")
    
    print("=" * 70)


def test_wrong_basic_auth():
    """Yanlış Basic Auth credentials ile test (başarısız olmalı)"""
    print("\n" + "=" * 70)
    print("❌ TEST 3: YANLIŞ BASIC AUTH (BAŞARISIZ OLMALI)")
    print("=" * 70)
    
    # Yanlış credentials
    wrong_credentials = f"{TEST_USERNAME}:wrong-password"
    encoded_credentials = base64.b64encode(wrong_credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    print(f"URL: {WEBHOOK_URL}")
    print(f"Username: {TEST_USERNAME}")
    print(f"Password: wrong-password")
    print("-" * 70)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=test_order,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("\n✅ GÜVENLIK TEST BAŞARILI - Yanlış credentials reddedildi!")
        elif response.status_code == 200:
            print("\n⚠️  UYARI: Yanlış credentials kabul edildi - güvenlik açığı!")
        else:
            print(f"\n⚠️  Beklenmeyen durum kodu: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ BAĞLANTI HATASI: {e}")
    
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════
# ANA PROGRAM
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     TRENDYOL WEBHOOK AUTHENTICATION TEST ARACI                ║
    ║              (Basic Authentication)                           ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Bu script webhook endpoint'inizin Basic Authentication kontrolünü test eder.
    """)
    
    choice = input("\nTüm testler çalıştırılsın mı? (E/H): ").strip().upper()
    
    if choice == 'E':
        test_basic_auth()
        test_no_auth()
        test_wrong_basic_auth()
    else:
        print("\n1. Basic Auth test (doğru credentials)")
        print("2. Auth olmadan test (başarısız olmalı)")
        print("3. Yanlış Basic Auth test (başarısız olmalı)")
        print("4. Çıkış")
        
        test_choice = input("\nSeçiminiz (1-4): ").strip()
        
        if test_choice == "1":
            test_basic_auth()
        elif test_choice == "2":
            test_no_auth()
        elif test_choice == "3":
            test_wrong_basic_auth()
        elif test_choice == "4":
            print("👋 Çıkılıyor...")
        else:
            print("❌ Geçersiz seçim!")
    
    print("\n📝 Not: Testler başarısızsa:")
    print("   1. Sunucu çalışıyor mu? (python manage.py runserver)")
    print("   2. .env dosyasındaki webhook username/password doğru mu?")
    print("   3. WEBHOOK_URL doğru mu?")
    print("   4. settings.py'de TRENDYOL_WEBHOOK_USERNAME/PASSWORD tanımlı mı?")
