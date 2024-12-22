from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('', views.product_list, name='product_list'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:id>/', views.delete_product, name='delete_product'),
    re_path(r'^product/adjust_stock/(?P<id>\d+)/(?P<amount>-?\d+)/$', views.adjust_stock, name='adjust_stock')
]
