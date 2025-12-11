#!/bin/bash
# Stok kontrol scripti - Her gün sabah 9 ve öğleden sonra 3'te çalışır (Pazar hariç)
# Kullanım: ./check_stock_cron.sh

# Script dizinine git
cd /root/yeninesilevim/inventory_manager

# Virtual environment'ı aktif et
source /root/yeninesilevim/inventory_manager/env/bin/activate

# Django management komutunu çalıştır
python manage.py check_low_stock

# Log dosyasına kaydet (proje içinde)
echo "Stock check completed at $(date)" >> /root/yeninesilevim/inventory_manager/stock_check.log
