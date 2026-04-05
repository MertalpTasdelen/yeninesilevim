#!/usr/bin/env python3
"""
Trendyol Webhook Kayıt - Basit Versiyon
"""

import requests
import base64

# ═══════════════════════════════════════════════════════════════════
# AYARLAR
# ═══════════════════════════════════════════════════════════════════

SUPPLIER_ID = "973871"
API_KEY = "uxKAGmeBsn35z1Pkyszs"
API_SECRET = "A8eBLEct9tABS4Q5UB30"

WEBHOOK_URL = "https://yeninesilevim.com/notify/inventory/"
WEBHOOK_USERNAME = "webhook_admin_2024"
WEBHOOK_PASSWORD = "xTMsQoXEsj0KXRSKHBVToB/z31qrpTwGyK18wLLFPis="

# ═══════════════════════════════════════════════════════════════════
# WEBHOOK KAYDET
# ═══════════════════════════════════════════════════════════════════

def register():
    url = f"https://apigw.trendyol.com/integration/webhook/sellers/{SUPPLIER_ID}/webhooks"
    
    # Authorization header
    auth = f"{API_KEY}:{API_SECRET}"
    auth_b64 = base64.b64encode(auth.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # Body - Minimum gerekli alanlar
    payload = {
        "url": WEBHOOK_URL,
        "authenticationType": "BASIC_AUTHENTICATION",
        "username": WEBHOOK_USERNAME,
        "password": WEBHOOK_PASSWORD
    }
    
    print("Webhook kaydediliyor...")
    print(f"URL: {WEBHOOK_URL}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code in [200, 201]:
        print("\nBAŞARILI!")
        data = response.json()
        print(f"Webhook ID: {data.get('id')}")
    else:
        print("\nBAŞARISIZ!")

def list_webhooks():
    url = f"https://apigw.trendyol.com/integration/webhook/sellers/{SUPPLIER_ID}/webhooks"
    
    auth = f"{API_KEY}:{API_SECRET}"
    auth_b64 = base64.b64encode(auth.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    print("\n1. Webhook kaydet")
    print("2. Webhook listele")
    choice = input("\nSeçim: ")
    
    if choice == "1":
        register()
    elif choice == "2":
        list_webhooks()
