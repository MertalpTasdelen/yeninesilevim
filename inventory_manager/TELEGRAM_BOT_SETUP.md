# Telegram Bot Komutları - Kurulum Rehberi

## 📋 Eklenen Özellikler

Bot artık şu komutları destekliyor:

### Komutlar:
- `/stok` - Genel stok durumu özeti
- `/tukenen` - Tükenen ürünler (0 adet)
- `/acil` - Acil sipariş gerekli (1 adet)
- `/dusuk` - Düşük stoklu ürünler (2-3 adet)
- `/yardim` veya `/help` - Yardım mesajı

## 🚀 Kurulum Adımları

### 1. Dosyaları Sunucuya Yükle

```bash
# Yeni dosyaları ve güncellemeleri yükle
scp inventory/telegram_bot.py root@188.245.97.131:/root/yeninesilevim/inventory_manager/inventory/
scp inventory/views.py root@188.245.97.131:/root/yeninesilevim/inventory_manager/inventory/
scp inventory/urls.py root@188.245.97.131:/root/yeninesilevim/inventory_manager/inventory/
```

### 2. Django'yu Yeniden Başlat

```bash
ssh root@188.245.97.131

# Django'yu restart et (uygulama yeniden yüklenir)
systemctl restart gunicorn
# veya
systemctl restart nginx
```

### 3. Webhook'u Ayarla

Bu adım sadece BIR KEZ yapılır. Tarayıcıdan veya curl ile:

```bash
# Tarayıcıdan:
https://yeninesilevim.com/api/telegram-setup

# Veya curl ile:
curl https://yeninesilevim.com/api/telegram-setup
```

Başarılı yanıt:
```json
{
  "success": true,
  "message": "✅ Webhook başarıyla ayarlandı!",
  "webhook_url": "https://yeninesilevim.com/api/telegram-webhook",
  "info": {
    "url": "https://yeninesilevim.com/api/telegram-webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### 4. Test Et

Telegram grubuna git ve komutları dene:

```
/stok
/tukenen
/acil
/dusuk
/yardim
```

## 🔍 Webhook Durumunu Kontrol Et

```bash
# Webhook durumunu kontrol et
curl https://yeninesilevim.com/api/telegram-info
```

## 🐛 Sorun Giderme

### Komutlar çalışmıyor?

1. **Webhook'u kontrol et:**
   ```bash
   curl https://yeninesilevim.com/api/telegram-info
   ```

2. **Logları incele:**
   ```bash
   ssh root@188.245.97.131
   tail -f /var/log/gunicorn/error.log
   tail -f /root/yeninesilevim/inventory_manager/logs/app.log
   ```

3. **Webhook'u yeniden ayarla:**
   ```bash
   curl https://yeninesilevim.com/api/telegram-setup
   ```

### Bot yanıt vermiyor?

- Bot'un grupta admin yetkisi olduğundan emin ol
- Bot'un mesajları okuma yetkisi olmalı
- Komutları tam olarak yaz (/) ile başlamalı

### 403 veya 401 hatası?

CSRF exempt zaten ayarlı, ama yine de hata alırsan:
```python
# settings.py içinde kontrol et
CSRF_TRUSTED_ORIGINS = ['https://yeninesilevim.com']
```

## 📊 Komut Örnekleri

### /stok
```
📦 Stok Durumu

Toplam düşük stok: 63 ürün

🔴 Tükendi: 15
⚠️ Acil: 12
📦 Düşük: 36

💡 Detay için:
/tukenen - Tükenen ürünler
/acil - Acil sipariş gerekli (1 adet)
/dusuk - Düşük stoklu ürünler (2-3 adet)
```

### /tukenen
```
🔴 Tükenen Ürünler
📊 Toplam: 15 ürün

1. Ürün Adı 1
   └ Barkod: 123456789
   └ Stok: 0 adet

2. Ürün Adı 2
   └ Barkod: 987654321
   └ Stok: 0 adet
...
```

### /acil
```
⚠️ Acil Sipariş Gerekli
📊 Toplam: 12 ürün

1. Ürün Adı 3
   └ Barkod: 111222333
   └ Stok: 1 adet
   └ Fiyat: 99.90 ₺
...
```

## 🔐 Güvenlik Notları

- Webhook endpoint'i CSRF'den muaf (csrf_exempt)
- Sadece POST isteklerini kabul eder
- Telegram'dan gelen update'ler JSON olarak parse edilir
- Tüm hatalar loglanır

## 🎯 Özet

✅ 5 komut ekledik (/stok, /tukenen, /acil, /dusuk, /yardim)
✅ Webhook sistemi kuruldu
✅ Bot otomatik yanıt veriyor
✅ 30 ürüne kadar gösterir (mesaj limiti için)
✅ HTML formatında güzel görünüm
✅ Reply ile yanıt verir (thread oluşur)

Şimdi grup üyeleri manuel olarak stokları sorgulayabilir! 🎉
