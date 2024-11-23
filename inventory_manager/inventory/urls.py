from django.urls import path,re_path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.add_product, name='add_product'),
    re_path(r'^adjust_stock/(?P<product_id>[0-9]+)/(?P<amount>-?[0-9]+)/$', views.adjust_stock, name='adjust_stock'),
]
