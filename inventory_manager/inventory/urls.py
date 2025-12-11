from django.urls import path, re_path, include
from . import views
from django.contrib import admin

urlpatterns = [
    # List and search products
    path('', views.product_list, name='product_list'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),
    # CRUD operations on products
    path('product/add/', views.add_product, name='add_product'),
    path('product/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:id>/', views.delete_product, name='delete_product'),
    # Barcode scanning and camera
    path('camera/', views.camera_view, name='camera_view'),
    path('scan-barcode/', views.scan_barcode, name='scan_barcode'),
    # Traditional profit calculator
    path('profit-calculator/', views.profit_calculator, name='profit_calculator'),
    path('save_profit_calculation/', views.save_profit_calculation, name='save_profit_calculation'),
    path('profit_calculator_list/', views.profit_calculator_list, name='profit_calculator_list'),
    # Trendyol settlements profit calculation
    path('trendyol-profit/', views.trendyol_profit, name='trendyol_profit'),
    # Auxiliary endpoints
    path('get_product_image/', views.get_product_image, name='get_product_image'),
    path('api/get-product-by-barcode', views.get_product_by_barcode, name='get_product_by_barcode'),
    path('delete_profit_calculation/<int:id>/', views.delete_profit_calculation, name='delete_profit_calculation'),
    # Authentication endpoints
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Adjust stock via querystring; captured with regex to allow negative numbers
    re_path(r'^product/adjust_stock/(?P<id>\d+)/(?P<amount>-?\d+)/$', views.adjust_stock, name='adjust_stock'),
    # Service Worker (Root Scope)
    path('service-worker.js', views.service_worker, name='service_worker'),
    
    # Custom Push Subscription Endpoint (Debug)
    path('api/push-subscribe', views.save_push_subscription, name='save_push_subscription'),
    path('api/test-notification', views.test_notification, name='test_notification'),
    path('api/test-telegram', views.test_telegram_notification, name='test_telegram_notification'),
    
    # Telegram Bot Webhooks
    path('api/telegram-webhook', views.telegram_webhook, name='telegram_webhook'),
    path('api/telegram-setup', views.telegram_setup_webhook, name='telegram_setup_webhook'),
    path('api/telegram-info', views.telegram_webhook_info, name='telegram_webhook_info'),
    
    # Purchase Items URLs
    path('purchase-items/', views.purchase_items_list, name='purchase_items_list'),
    path('purchase-items/add/', views.add_purchase_item, name='add_purchase_item'),
    re_path(r'^purchase-items/adjust/(?P<item_id>\d+)/(?P<amount>-?\d+)/$', views.adjust_purchase_quantity, name='adjust_purchase_quantity'),
    path('purchase-items/delete/<int:item_id>/', views.delete_purchase_item, name='delete_purchase_item'),
    path('purchase-items/toggle-archive/<int:item_id>/', views.toggle_archive_purchase_item, name='toggle_archive_purchase_item'),
]
