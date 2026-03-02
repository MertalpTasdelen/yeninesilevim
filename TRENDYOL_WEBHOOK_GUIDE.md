# Trendyol Webhook Entegrasyonu - Otomatik Stok Düşürme Sistemi

## 📋 Genel Bakış

Bu sistem, Trendyol'dan gelen siparişleri otomatik olarak yakalar ve SKU (purchase_items) stoklarını düşürür.

### Akış Şeması

```
Trendyol Sipariş
    ↓
Webhook POST → /notify/inventory/
    ↓
Barcode ile inventory_product bul
    ↓
Product → listing_components al
    ↓
Her component için:
    purchase_item.quantity -= (qty_per_listing × sipariş_adedi)
    ↓
Sonuç → trendyol_webhook_logs kaydedilir
```

## 🚀 Kurulum Adımları

### 1. Migration Oluştur ve Çalıştır

```bash
python manage.py makemigrations inventory
python manage.py migrate
```

Bu işlem `trendyol_webhook_logs` tablosunu oluşturur.

### 2. Trendyol API Bilgilerini Al

1. [Trendyol Satıcı Paneli](https://seller.trendyol.com/) → Giriş yap
2. **Hesap Bilgilerim** → **Entegrasyon Bilgileri** menüsüne git
3. Şu bilgileri not al:
   - **Supplier ID** (Satıcı ID)
   - **API Key**
   - **API Secret**

### 3. Webhook URL'ini Ayarla

Webhook'un çalışması için **public erişilebilir** bir URL'e ihtiyacınız var.

**Seçenekler:**

#### A) Canlı Sunucu (Production)
```
https://yourdomain.com/notify/inventory/
```

#### B) Geliştirme (ngrok ile test)
```bash
# ngrok kur: https://ngrok.com/download
ngrok http 8000

# Çıkan URL'i kullan:
# https://abc123.ngrok.io/notify/inventory/
```

### 4. Webhook Kaydı

#### Otomatik Kayıt (Önerilen)

`register_trendyol_webhook.py` scriptini düzenle:

```python
SUPPLIER_ID = "123456"  # Kendi Supplier ID'niz
API_KEY = "xxxxxxxx"    # Kendi API Key'iniz
API_SECRET = "xxxxxxxx" # Kendi API Secret'ınız
WEBHOOK_URL = "https://yourdomain.com/notify/inventory/"
```

Ve `.env` dosyasına webhook authentication bilgilerini ekle:

```env
TRENDYOL_WEBHOOK_USERNAME=webhook_admin_2024
TRENDYOL_WEBHOOK_PASSWORD=VeryStr0ng!P@ssw0rd#2024
```

Çalıştır:
```bash
cd inventory_manager
python register_trendyol_webhook.py
```

Menüden **1** (Yeni webhook kaydet) seçin.

#### Manuel Kayıt (Postman/cURL)

```bash
curl -X POST \
  https://apigw.trendyol.com/integration/webhook/sellers/{SUPPLIER_ID}/webhooks \
  -H 'Authorization: Basic BASE64(API_KEY:API_SECRET)' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://yourdomain.com/notify/inventory/",
    "authenticationType": "BASIC_AUTHENTICATION",
    "username": "webhook_admin_2024",
    "password": "VeryStr0ng!P@ssw0rd#2024",
    "subscribedStatuses": ["CREATED", "PICKING", "INVOICED"]
  }'
```

## 🧪 Test Etme

### 1. Local Test Endpoint

Django sunucusu çalışırken:

```bash
# Sunucuyu başlat
python manage.py runserver

# Başka bir terminalde test et:
curl -X GET http://localhost:8000/notify/inventory-test/
```

Bu endpoint örnek bir sipariş simüle eder.

### 2. Test Siparişi (Trendyol Panelinden)

1. Trendyol Satıcı Paneli → **Test Siparişi Oluştur**
2. Sisteminizdeki bir ürünün barcodunu kullan
3. Webhook otomatik tetiklenecek

### 3. Logları Kontrol Et

#### Django Admin
```
http://localhost:8000/admin/inventory/trendyolwebhooklog/
```

#### Konsol Logları
```bash
# Django server loglarını izle
python manage.py runserver
# Her webhook isteği konsola düşer
```

## 📊 Webhook Log Yapısı

Her webhook isteği `trendyol_webhook_logs` tablosuna kaydedilir:

| Alan | Açıklama |
|------|----------|
| `order_number` | Trendyol sipariş numarası |
| `barcode` | Ürün barkodu |
| `status` | Sipariş durumu (CREATED, PICKING, vb.) |
| `quantity` | Sipariş adedi |
| `success` | İşlem başarılı mı? |
| `error_message` | Hata varsa mesaj |
| `affected_product_id` | Etkilenen Product ID |
| `affected_components` | Hangi SKU'lar düştü (JSON) |
| `raw_payload` | Trendyol'dan gelen ham data |

### Örnek Log

```json
{
  "order_number": "106544123456",
  "barcode": "8683772071724",
  "status": "CREATED",
  "quantity": 1,
  "success": true,
  "affected_components": [
    {
      "sku_name": "Kutu Malzemesi",
      "sku_barcode": "KTX-001",
      "old_qty": 100,
      "new_qty": 95,
      "deducted": 5
    },
    {
      "sku_name": "Etiket",
      "sku_barcode": "ETK-002",
      "old_qty": 200,
      "new_qty": 199,
      "deducted": 1
    }
  ]
}
```

## ⚙️ Nasıl Çalışır?

### Örnek Senaryo

**Durum:**
- Trendyol'da "Premium Set" ürünü satıyorsunuz (Barcode: `PSET-001`)
- Bu set 2 adet "Kutu" (SKU: `KTX-001`) ve 1 adet "Etiket" (SKU: `ETK-002`) içeriyor

**Tanımlamalar:**

1. **inventory_product** tablosunda:
   - name: "Premium Set"
   - barcode: `PSET-001`

2. **listing_components** tablosunda:
   ```
   inventory_product_id → Premium Set
   purchase_item_id → Kutu (KTX-001)
   qty_per_listing → 2

   inventory_product_id → Premium Set
   purchase_item_id → Etiket (ETK-002)
   qty_per_listing → 1
   ```

3. **purchase_items** tablosunda:
   ```
   Kutu (KTX-001): quantity = 100
   Etiket (ETK-002): quantity = 500
   ```

**Sipariş Geldiğinde:**

Trendyol'dan 3 adet "Premium Set" siparişi gelir:

```json
{
  "lines": [
    {
      "barcode": "PSET-001",
      "quantity": 3
    }
  ]
}
```

**Otomatik İşlem:**

1. Barcode `PSET-001` → "Premium Set" bulunur
2. Listing components alınır:
   - Kutu: 2 adet/set × 3 sipariş = **6 adet düşür**
   - Etiket: 1 adet/set × 3 sipariş = **3 adet düşür**
3. Stoklar güncellenir:
   ```
   Kutu: 100 → 94
   Etiket: 500 → 497
   ```

## 🛡️ Güvenlik

### Basic Authentication

Webhook endpoint'iniz **otomatik olarak Basic Authentication** ile korunur!

**Nasıl Çalışır:**

1. `.env` dosyasında webhook kullanıcı adı/şifre tanımlarsınız
2. Webhook kaydederken bu bilgiler Trendyol'a gönderilir
3. Trendyol her webhook isteğinde Authorization header'ı ile gelir
4. views.py otomatik olarak kontrol eder

**Ayarlar:**

```env
# .env dosyası
TRENDYOL_WEBHOOK_USERNAME=webhook_admin_2024
TRENDYOL_WEBHOOK_PASSWORD=VeryStr0ng!P@ssw0rd#2024
```

**Doğrulama Kodu:**

```python
# views.py → trendyol_order_webhook fonksiyonu zaten içeriyor:

auth_header = request.headers.get('Authorization', '')
if not auth_header.startswith('Basic '):
    logger.warning("Missing or invalid Authorization header")
    return JsonResponse({'error': 'Unauthorized'}, status=401)

# Base64 decode ve kontrol
try:
    encoded_credentials = auth_header.split(' ')[1]
    decoded = base64.b64decode(encoded_credentials).decode('utf-8')
    username, password = decoded.split(':', 1)
    
    if username != settings.TRENDYOL_WEBHOOK_USERNAME or \
       password != settings.TRENDYOL_WEBHOOK_PASSWORD:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
except:
    return JsonResponse({'error': 'Invalid auth format'}, status=401)
```

✅ **Bu kontrol otomatik yapılır, ek bir şey eklemenize gerek yok!**

💡 **İpucu:** Detaylı authentication kılavuzu için `WEBHOOK_AUTH_GUIDE.md` dosyasına bakın.

## ❓ Sık Sorulan Sorular

### 1. "Barkod bulunamadı" hatası alıyorum

**Çözüm:** 
- `inventory_product` tablosunda ürünün barcode alanını kontrol edin
- Trendyol'daki barcode ile birebir aynı olmalı

### 2. "Bileşen tanımlı değil" uyarısı

**Çözüm:**
- Set Yönetimi ekranından (`/listing-components/`) ilgili ürün için bileşenler ekleyin
- Eğer ürün set değilse (tek başına satılıyorsa), bu normal bir uyarıdır

### 3. Webhook tetiklenmiyor

**Kontrol Listesi:**
- [ ] Webhook URL public erişilebilir mi?
- [ ] Django sunucusu çalışıyor mu?
- [ ] Firewall/güvenlik duvarı webhook portunu engelliyor mu?
- [ ] Trendyol webhook'u "Active" durumda mı? (panelden kontrol et)

### 4. Stoklar düşmüyor

**Debugging:**
1. Django admin'den webhook loglarını kontrol et
2. `success=False` kayıtlara bak
3. `error_message` alanını oku
4. Django console loglarını incele

### 5. İade/İptal durumlarında stok geri eklensin mi?

Şu anda sistem sadece stok düşürüyor. İade/iptal için otomatik stok ekleme istiyorsanız:

```python
# views.py → process_trendyol_order_line fonksiyonunda

if status in ['CANCELLED', 'RETURNED']:
    # Stok ekle (geri al)
    purchase_item.quantity += int(deduction_amount)
else:
    # Stok düşür
    purchase_item.quantity -= int(deduction_amount)
```

## 📞 Destek

Sorun yaşarsanız:
1. Django admin → Webhook Logs kontrol edin
2. `python manage.py runserver` console çıktısını inceleyin
3. Trendyol Satıcı Paneli → Webhook bölümünden durum kontrolü yapın

## 🔄 Webhook Güncelleme/Silme

### Mevcut Webhook'ları Listele
```bash
python register_trendyol_webhook.py
# Menüden 2 seçin
```

### Webhook Sil
```bash
python register_trendyol_webhook.py
# Menüden 3 seçin
# Webhook ID girin (listeden alın)
```

### Webhook Güncelle

Önce eski webhook'u silin, sonra yenisini kaydedin.

---

**✨ Sistem hazır! Trendyol'dan gelen her sipariş otomatik olarak SKU stoklarınızı düşürecek.**
