# Inventory Manager - Stok Yönetim Sistemi

Django tabanlı stok yönetim ve Trendyol entegrasyonlu envanter sistemi.

## 🚀 Özellikler

- 📦 Ürün stok takibi ve yönetimi
- 🔔 Düşük stok bildirimleri (Telegram Bot)
- 🏪 Trendyol webhook entegrasyonu
- 📊 Kâr hesaplama ve raporlama
- 🔍 Barkod okuyucu desteği
- 🔐 Güvenli kimlik doğrulama
- 📱 Web Push bildirimleri (VAPID)

## 📋 Gereksinimler

- Python 3.8+
- Django 5.1+
- PostgreSQL (Production) veya SQLite (Development)
- Telegram Bot (Opsiyonel - Bildirimler için)
- Trendyol Satıcı Hesabı (Opsiyonel - Entegrasyon için)

## 🔧 Kurulum

### 1. Projeyi Klonlayın

```bash
git clone <repository-url>
cd yeninesilevim
```

### 2. Virtual Environment Oluşturun

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# veya
.venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Environment Variables Ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın ve değerleri doldurun:

```bash
cp .env.example .env
```

#### Gerekli Environment Variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Trendyol API (Entegrasyon için)
TRENDYOL_SUPPLIER_ID=your_supplier_id
TRENDYOL_API_KEY=your_api_key
TRENDYOL_API_SECRET=your_api_secret

# Trendyol Webhook Authentication
TRENDYOL_WEBHOOK_USERNAME=webhook_admin_2024
TRENDYOL_WEBHOOK_PASSWORD=your_strong_password

# Application Login
APP_LOGIN_PASSWORD=your_secure_password

# Telegram Bot (Opsiyonel)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# VAPID Keys (Web Push - Opsiyonel)
VAPID_PUBLIC_KEY=your_public_key
VAPID_PRIVATE_KEY=your_private_key
VAPID_ADMIN_EMAIL=admin@yourdomain.com
```

### 5. Veritabanı Kurulumu

```bash
cd inventory_manager
python manage.py migrate
python manage.py createsuperuser
```

### 6. Static Dosyaları Toplayın

```bash
python manage.py collectstatic
```

### 7. Geliştirme Sunucusunu Başlatın

```bash
python manage.py runserver
```

## 🔑 API Keys ve Credentials Nasıl Alınır?

### Django SECRET_KEY

Python ile rastgele bir key oluşturun:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Trendyol API Credentials

1. [Trendyol Satıcı Paneli](https://partner.trendyol.com) 'ne giriş yapın
2. **Hesap Bilgilerim** > **Entegrasyon Bilgileri** menüsüne gidin
3. **Supplier ID**, **API Key**, ve **API Secret** değerlerini kopyalayın

### Telegram Bot

1. Telegram'da [@BotFather](https://t.me/botfather) ile konuşun
2. `/newbot` komutu ile yeni bot oluşturun
3. Bot Token'ı kopyalayın
4. Chat ID'yi almak için:
   - Bot'a bir mesaj gönderin
   - `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` adresini ziyaret edin
   - `chat.id` değerini kopyalayın

### VAPID Keys (Web Push)

Proje içindeki script ile oluşturabilirsiniz:

```bash
python generate_vapid_keys.py
```

## 🔗 Trendyol Webhook Kurulumu

Trendyol'dan sipariş bildirimleri almak için:

```bash
cd inventory_manager
python register_trendyol_webhook.py
```

Veya basit versiyon:

```bash
python simple_webhook_register.py
```

## 📁 Proje Yapısı

```
yeninesilevim/
├── inventory_manager/          # Ana Django projesi
│   ├── inventory/              # Envanter uygulaması
│   │   ├── templates/          # HTML şablonları
│   │   ├── static/             # CSS, JS, vb.
│   │   ├── management/         # Django komutları
│   │   ├── views.py            # View fonksiyonları
│   │   ├── models.py           # Veritabanı modelleri
│   │   ├── telegram_bot.py    # Telegram bot entegrasyonu
│   │   └── trendyol_integration.py
│   └── inventory_manager/      # Proje ayarları
│       ├── settings.py         # Django ayarları
│       └── urls.py             # URL yapılandırması
├── .env                        # Environment variables (GİT'E EKLENMEMELİ)
├── .env.example                # Örnek environment dosyası
├── .gitignore                  # Git ignore kuralları
└── requirements.txt            # Python bağımlılıkları
```

## 🔐 Güvenlik Notları

⚠️ **ÖNEMLİ:** Aşağıdaki dosyaların asla Git'e eklenmediğinden emin olun:

- `.env` - Tüm hassas bilgiler burada
- `db.sqlite3` - Veritabanı dosyası
- `qr_codes/` - Oluşturulan barkod görselleri
- `*.csv` - Export edilen dosyalar

Bu dosyalar zaten `.gitignore` içinde tanımlı.

## 🚀 Production'a Dağıtım

Production ortamına deploy ederken:

1. `DEBUG=False` olarak ayarlayın
2. `SECRET_KEY`'i güçlü bir değer ile değiştirin
3. `ALLOWED_HOSTS`'u güncelleyin
4. PostgreSQL gibi production-ready bir veritabanı kullanın
5. Nginx/Apache gibi bir web sunucu kullanın
6. Gunicorn/uWSGI gibi WSGI server kullanın
7. HTTPS kullanın (Let's Encrypt ile ücretsiz)

## 📝 Lisans

Bu proje özel kullanım içindir.

## 🤝 Katkıda Bulunma

Katkıda bulunmak için lütfen bir Pull Request açın.

## 📧 İletişim

Sorularınız için: [E-posta adresiniz]

---

**Not:** Bu proje hassas API anahtarları içermez. Tüm credentials `.env` dosyasında saklanmalıdır.
