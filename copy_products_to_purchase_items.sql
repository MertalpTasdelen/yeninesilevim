-- inventory_product tablosundan purchase_items tablosuna veri kopyalama scripti
-- Tarih: 2025-11-29

-- Purchase Items tablosunu temizle (opsiyonel - dikkatli kullanın!)
-- TRUNCATE TABLE purchase_items;

-- Verileri kopyala
INSERT INTO purchase_items (name, purchase_barcode, purchase_price, quantity, image_url, created_at)
SELECT 
    name,
    COALESCE(purchase_barcode, barcode) as purchase_barcode,  -- purchase_barcode yoksa barcode kullan
    purchase_price,
    stock as quantity,  -- stock alanını quantity olarak kullan
    image_url,
    created_at
FROM inventory_product
ON CONFLICT (purchase_barcode) DO NOTHING;  -- Aynı barkod varsa atla

-- Sonuçları kontrol et
SELECT COUNT(*) as total_products FROM inventory_product;
SELECT COUNT(*) as total_purchase_items FROM purchase_items;

-- Son 10 kaydı göster
SELECT id, name, purchase_barcode, purchase_price, quantity, created_at 
FROM purchase_items 
ORDER BY created_at DESC 
LIMIT 10;
