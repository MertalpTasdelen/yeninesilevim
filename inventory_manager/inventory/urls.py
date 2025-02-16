from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('', views.product_list, name='product_list'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:id>/', views.delete_product, name='delete_product'),
    path('camera/', views.camera_view, name='camera_view'),
    path('scan-barcode/', views.scan_barcode, name='scan_barcode'),
    path('profit-calculator/', views.profit_calculator, name='profit_calculator'),
    path('save_profit_calculation/', views.save_profit_calculation, name='save_profit_calculation'),
    path('profit_calculator_list/', views.profit_calculator_list, name='profit_calculator_list'),
    path('get_product_image/', views.get_product_image, name='get_product_image'),
    re_path(r'^product/adjust_stock/(?P<id>\d+)/(?P<amount>-?\d+)/$', views.adjust_stock, name='adjust_stock')
]
