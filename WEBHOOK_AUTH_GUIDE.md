# 🔐 Trendyol Webhook Authentication - Basic Auth Kılavuzu

## 📋 İçindekiler

1. [Authentication Nedir ve Neden Gerekli?](#1-nedir)
2. [Basic Authentication Nasıl Çalışır?](#2-basic-auth)
3. [Adım Adım Kurulum](#3-kurulum)
4. [Test Etme](#4-test)
5. [Sorun Giderme](#5-sorun-giderme)

---

## 1. Authentication Nedir ve Neden Gerekli? {#1-nedir}

### 🎯 Amaç

Webhook endpoint'iniz **public** bir URL'dir (Trendyol'un erişebilmesi için). Bu demektir ki:
- Herkes bu URL'i bilirse istek atabilir
- Kötü niyetli kişiler sahte siparişler gönderebilir
- Stoklarınız yanlış düşebilir

**Basic Authentication** ile sadece **doğru kullanıcı adı ve şifre ile gelen istekleri kabul edersiniz**.

---

## 2. Basic Authentication Nasıl Çalışır? {#2-basic-auth}

### 📌 İşleyiş

```
Trendyol                        Sizin Sunucu
   │                                 │
   ├─ POST request                   │
   ├─ Header: Authorization: Basic YWRta... │
   └─────────────────────────────────►│
                                      ├─ Base64 decode
                                      ├─ username:password çıkar
                                      ├─ Kontrol et
                                      │   ✅ Doğru → İşle
                                      │   ❌ Yanlış → 401
```

### 🔐 Güvenlik

- **Username + Password** kombinasyonu
- Base64 ile encode edilir (güvenlik için HTTPS zorunlu!)
- Trendyol her webhook isteğinde bu bilgileri gönderir
- Sizin sunucunuz kontrol eder

---

## 3. Adım Adım Kurulum {#3-kurulum}

### ✅ Tam Kurulum Checklist

#### Adım 1: .env Dosyası Hazırla

```bash
cd c:\Users\Taşdelen\Desktop\yeninesilevim
notepad .env  # veya favori editörünüzle
```

**.env** dosyasına ekleyin:

```env
# Trendyol Webhook Basic Authentication
TRENDYOL_WEBHOOK_USERNAME=webhook_admin_2024
TRENDYOL_WEBHOOK_PASSWORD=MySecurePassword!2024
```

💡 **Önemli**: Güçlü bir şifre kullanın! Örnek:
- En az 16 karakter
- Büyük/küçük harf karışık
- Rakam ve özel karakter içermeli
- Örnek: `VeryStr0ng!P@ssw0rd#2024`

#### Adım 2: Django Sunucuyu Başlat

```bash
cd inventory_manager
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

#### Adım 3: Webhook Kaydet

**Yeni terminal aç:**
```bash
cd inventory_manager
python register_trendyol_webhook.py
```

Menüden **1** seç → Webhook oluşturulacak

Script otomatik olarak .env dosyasındaki kullanıcı adı/şifreyi Trendyol'a gönderecek.

**Beklenen Output:**
```
✅ Django settings yüklendi - .env'deki webhook auth kullanılacak
   Username: webhook_admin_2024
   
🔄 Webhook oluşturuluyor...
✅ Webhook başarıyla oluşturuldu!
```

#### Adım 4: Test Et

```bash
python test_webhook_auth.py
```

Tüm testleri çalıştırmak için **E** tuşlayın.

**Beklenen Sonuçlar:**
```
✅ TEST BAŞARILI - Basic Auth doğru çalışıyor!
✅ GÜVENLIK TEST BAŞARILI - Auth olmadan erişim engellendi!
✅ GÜVENLIK TEST BAŞARILI - Yanlış credentials reddedildi!
```

---

## 4. Test Etme {#4-test}

### 🧪 Test 1: Otomatik Test Script

```bash
cd inventory_manager
python test_webhook_auth.py
```

Üç test yapılır:
1. **Doğru credentials** → ✅ Başarılı olmalı
2. **Auth olmadan** → ❌ 401 Unauthorized almalı
3. **Yanlış credentials** → ❌ 401 Unauthorized almalı

### 🧪 Test 2: Manuel cURL Test

**Doğru credentials ile:**
```bash
curl -X POST https://yeninesilevim.com/notify/inventory/ \
  -H "Content-Type: application/json" \
  -u "webhook_admin_2024:MySecurePassword!2024" \
  -d '{"orderNumber":"TEST-123","shipmentPackageStatus":"CREATED","lines":[]}'
```

**Beklenen:** `200 OK`

**Auth olmadan (başarısız olmalı):**
```bash
curl -X POST https://yeninesilevim.com/notify/inventory/ \
  -H "Content-Type: application/json" \
  -d '{"orderNumber":"TEST-123","shipmentPackageStatus":"CREATED","lines":[]}'
```

**Beklenen:** `401 Unauthorized`

**Yanlış şifre ile (başarısız olmalı):**
```bash
curl -X POST https://yeninesilevim.com/notify/inventory/ \
  -H "Content-Type: application/json" \
  -u "webhook_admin_2024:WrongPassword" \
  -d '{"orderNumber":"TEST-123","shipmentPackageStatus":"CREATED","lines":[]}'
```

**Beklenen:** `401 Unauthorized`

### 🧪 Test 3: Django Loglarını İzle

```bash
# Terminal'de Django sunucu çalışırken
python manage.py runserver

# Test yap, konsolda göreceksin:
✅ Basic authentication successful: webhook_admin_2024
# veya
❌ Invalid Basic Auth credentials
```

---

## 5. Sorun Giderme {#5-sorun-giderme}

### ❌ Problem: "401 Unauthorized" alıyorum ama credentials doğru

**Çözüm 1: .env dosyası yükleniyor mu?**
```python
# Django shell'de kontrol et:
python manage.py shell

>>> from django.conf import settings
>>> print(settings.TRENDYOL_WEBHOOK_USERNAME)
>>> print(settings.TRENDYOL_WEBHOOK_PASSWORD)
# Beklenen: Ayarladığın değerler çıkmalı
# Çıkan: Boş veya default → .env yüklenmiyor
```

**Çözüm 2: settings.py doğru mu?**
```python
# settings.py'de olmalı:
TRENDYOL_WEBHOOK_USERNAME = os.getenv('TRENDYOL_WEBHOOK_USERNAME', 'webhook_admin')
TRENDYOL_WEBHOOK_PASSWORD = os.getenv('TRENDYOL_WEBHOOK_PASSWORD', 'change-this-password-2024')
```

**Çözüm 3: Sunucuyu yeniden başlat**
```bash
# .env güncellediysen, Django'yu restart et:
Ctrl+C
python manage.py runserver
```

**Çözüm 4: Base64 encoding kontrolü**

Basic Auth şu formatta gönderilir:
```
Authorization: Basic <base64(username:password)>
```

Python'da test et:
```python
import base64
creds = "webhook_admin_2024:MySecurePassword!2024"
encoded = base64.b64encode(creds.encode()).decode()
print(f"Authorization: Basic {encoded}")
```

Bu değeri cURL ile test et:
```bash
curl -X POST https://yeninesilevim.com/notify/inventory/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <yukarıdaki-encoded-değer>" \
  -d '{"orderNumber":"TEST-123","shipmentPackageStatus":"CREATED","lines":[]}'
```

---

### ❌ Problem: Webhook kaydı başarısız

**Hata:** `Failed to create webhook`

**Olası Sebepler:**

1. **Trendyol API credentials yanlış**
   ```python
   # register_trendyol_webhook.py içinde:
   SUPPLIER_ID = "973871"  # Doğru mu?
   API_KEY = "..."  # Doğru mu?
   API_SECRET = "..."  # Doğru mu?
   ```

2. **Webhook URL erişilemiyor**
   ```bash
   # URL'nizi test edin:
   curl https://yeninesilevim.com/api/trendyol-webhook/
   # 405 Method Not Allowed olmalı (GET desteklenmez, bu normal)
   ```

3. **Aynı URL zaten kayıtlı**
   ```bash
   # Önce mevcut webhook'u silin:
   python register_trendyol_webhook.py
   # Menüden 3 seç (Delete webhook)
   # Sonra yeniden oluşturun (1 seç)
   ```

---

### ❌ Problem: "Django settings yüklenemedi"

Bu sadece bir uyarı, manuel ayarlar kullanılır.

**Düzeltmek için:**
```bash
# inventory_manager klasöründen çalıştır:
cd c:\Users\Taşdelen\Desktop\yeninesilevim\inventory_manager
python register_trendyol_webhook.py
```

---

### ❌ Problem: Trendyol webhook tetiklenmiyor

**Kontrol Listesi:**

1. **Webhook aktif mi?**
   ```bash
   python register_trendyol_webhook.py
   # Menüden 2 seç → Webhook listesini gör
   # "active": true olmalı
   ```

2. **URL erişilebilir mi?**
   ```bash
   curl https://yeninesilevim.com/notify/inventory/
   # 405 Method Not Allowed olmalı (GET desteklenmez, bu normal)
   
   # POST ile test:
   curl -X POST https://yeninesilevim.com/notify/inventory/ \
     -u "webhook_admin_2024:MySecurePassword!2024" \
     -H "Content-Type: application/json" \
     -d '{"orderNumber":"TEST","shipmentPackageStatus":"CREATED","lines":[]}'
   # 200 OK olmalı
   ```

3. **Auth ayarları Trendyol'a doğru gitti mi?**
   
   Webhook kaydederken gönderilen body:
   ```json
   {
     "url": "https://yeninesilevim.com/notify/inventory/",
     "authenticationType": "BASIC_AUTHENTICATION",
     "username": "webhook_admin_2024",
     "password": "MySecurePassword!2024"
   }
   ```
   
   Bu, Trendyol'a "her webhook isteğinde Authorization: Basic header'ını ekle" demektir.

4. **HTTPS kullanılıyor mu?**
   
   Basic Auth **mutlaka HTTPS** gerektirir! HTTP ile kullanırsanız güvenlik açığı oluşur.
   
   URL: `https://yeninesilevim.com/...` ✅ Doğru  
   URL: `http://yeninesilevim.com/...` ❌ Yanlış

---

## 📚 Özet: Hangi Dosyalar Değişti?

| Dosya | Değişiklik | Neden? |
|-------|-----------|--------|
| `.env` | Username/Password eklendi | Gizli bilgileri saklar |
| `settings.py` | `TRENDYOL_WEBHOOK_USERNAME/PASSWORD` | .env'den oku |
| `views.py` → `trendyol_order_webhook` | Basic Auth kontrolü | Her isteği doğrula |
| `register_trendyol_webhook.py` | Django settings entegrasyonu | .env'den ayar al |
| `test_webhook_auth.py` | Test scripti | Auth'u test et |

---

## 🎯 En İyi Uygulamalar

### ✅ Yapılacaklar

1. **Güçlü şifreler kullanın**
   - En az 16 karakter
   - Büyük/küçük harf, rakam, özel karakter karışımı
   - Örnek: `VeryStr0ng!P@ssw0rd#2024`

2. **Şifreleri GitHub'a koymayın**
   - `.env` dosyası `.gitignore`'da olmalı
   - Kodda hardcode etmeyin

3. **HTTPS kullanın**
   - Basic Auth HTTP üzerinde güvensizdir
   - SSL sertifikası zorunlu

4. **Logları izleyin**
   ```bash
   python manage.py runserver
   # Her auth denemesi loglanır
   ```

5. **Periyodik şifre değiştirin**
   - 3-6 ayda bir yenileyin
   - Webhook'u güncelle (silip yeniden oluştur)

### ❌ Yapılmayacaklar

1. **Şifreleri GitHub'a commit etme**
2. **Zayıf şifreler kullanma** (örn: "123456", "password")
3. **HTTP ile Basic Auth kullanma** (mutlaka HTTPS!)
4. **Auth olmadan webhook bırakma**
5. **Aynı şifreyi her yerde kullanma**

---

## 🚀 Hızlı Başlangıç (TL;DR)

```bash
# 1. .env düzenle
cd c:\Users\Taşdelen\Desktop\yeninesilevim
notepad .env
# Ekle:
# TRENDYOL_WEBHOOK_USERNAME=webhook_admin_2024
# TRENDYOL_WEBHOOK_PASSWORD=VeryStr0ng!P@ssw0rd#2024

# 2. Django başlat
cd inventory_manager
python manage.py runserver

# 3. Yeni terminal → Webhook kaydet
python register_trendyol_webhook.py  # Menü: 1

# 4. Test et
python test_webhook_auth.py  # Menü: E

# ✅ Hazır!
```

---

## ❓ Sık Sorulan Sorular

**S: Kullanıcı adı/şifreyi Trendyol mı sağlıyor?**  
C: Hayır! Sen belirliyorsun. Trendyol sadece senin verdiğin bilgileri kullanarak istek atacak.

**S: Şifreyi kayıpettim ne olur?**  
C: Yenisini oluştur (.env'de değiştir), webhook'u sil, yeniden kaydet.

**S: Auth zorunlu mu?**  
C: Teknik olarak hayır ama **şiddetle önerilir**. Yoksa herkes sahte sipariş gönderebilir.

**S: HTTP ile kullanabilir miyim?**  
C: Hayır! Basic Auth mutlaka HTTPS gerektirir. HTTP üzerinde şifreler açık gider.

**S: Şifre değiştirirsem webhook'u yeniden kaydetmem gerekir mi?**  
C: Evet. Önce webhook'u sil (menü: 3), sonra yeni credentials ile tekrar oluştur (menü: 1).

---

**🎉 Webhook Basic Authentication kurulumu tamamlandı! Artık güvenli bir şekilde sipariş alabilirsiniz.**
