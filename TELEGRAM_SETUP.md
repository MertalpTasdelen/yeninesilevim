# 🎯 Telegram Bot Entegrasyonu - Nasıl Kurulur?

## 📋 Adım 1: Telegram Bot Oluştur

1. Telegram'da [@BotFather](https://t.me/botfather) ile konuşun
2. `/newbot` komutunu gönderin
3. Bot için bir isim ve username seçin
4. BotFather size bir **token** verecek: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

## 👥 Adım 2: Grup Oluştur ve Bot'u Ekle

1. Telegram'da yeni bir grup oluşturun
2. Botunuzu gruba ekleyin (Add Members)
3. Botunuza grup admin yetkisi verin

## 🔑 Adım 3: Chat ID'yi Öğren

Grupta herhangi bir mesaj gönderdikten sonra, browser'da şu URL'yi açın:

```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

**Örnek:**
```
https://api.telegram.org/bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
```

Response'da şuna benzer bir şey göreceksiniz:
```json
{
  "ok": true,
  "result": [
    {
      "message": {
        "chat": {
          "id": -1001234567890,  ← BU CHAT ID
          "title": "Stok Uyarıları",
          "type": "supergroup"
        }
      }
    }
  ]
}
```

## ⚙️ Adım 4: Production'da Ayarla

1. `.env` dosyasını düzenleyin:
```bash
nano /root/yeninesilevim/.env
```

2. Şu satırları ekleyin/güncelleyin:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
```

3. Değişiklikleri deployment yapın:
```bash
cd /root/yeninesilevim
git pull origin main
cd inventory_manager
pip install -r requirements.txt
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

## ✅ Adım 5: Test Et

### Web üzerinden test:
```
https://yeninesilevim.com/api/test-telegram
```

### Terminal'den test:
```bash
cd /root/yeninesilevim/inventory_manager
python manage.py check_low_stock --telegram-only
```

## 🤖 Kullanım

### Otomatik Bildirim (Cron Job)

Her 6 saatte bir kontrol yapmak için:
```bash
crontab -e
```

Ekleyin:
```bash
0 */6 * * * cd /root/yeninesilevim/inventory_manager && /root/yeninesilevim/env/bin/python manage.py check_low_stock >> /var/log/django/cron.log 2>&1
```

### Manuel Kontrol

```bash
# Hem web push hem Telegram
python manage.py check_low_stock

# Sadece Telegram
python manage.py check_low_stock --telegram-only

# Sadece Web Push
python manage.py check_low_stock --web-push-only
```

## 📱 Bildirim Formatı

Telegram'a gönderilen mesaj örneği:

```
🚨 Stok Uyarısı 🚨

📦 3 ürünün stoğu düşük:

⚠️ İçi Üç Boyutlu Renkli Hayvan Figürlü Tombul Cam Kupa
   └ Barkod: figürlü04
   └ Stok: 2 adet
   └ Fiyat: 399.00 ₺

🔴 Akasya Detaylı Cam Demlik
   └ Barkod: demlik02
   └ Stok: 0 adet

🕒 06.12.2024 15:30
```

## 🔧 Troubleshooting

### Bildirim gelmiyor?

1. Bot token'ı doğru mu?
```bash
curl "https://api.telegram.org/botYOUR_TOKEN/getMe"
```

2. Chat ID doğru mu?
```bash
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/sendMessage" \
  -d "chat_id=YOUR_CHAT_ID" \
  -d "text=Test"
```

3. Loglara bakın:
```bash
tail -f /var/log/django/app.log | grep -i telegram
```

## 📊 Özellikler

✅ HTML formatında zengin mesajlar
✅ Emoji ile görsel bilgi
✅ Ürün başına detaylı bilgi (barkod, stok, fiyat)
✅ Timestamp ile zaman bilgisi
✅ Hata logları ve retry mekanizması
✅ Web push ile paralel çalışma
✅ Esnek CLI parametreleri

---

**Not:** Bot'unuz gruba mesaj gönderebilmesi için mutlaka **admin** yetkisine sahip olmalı!
