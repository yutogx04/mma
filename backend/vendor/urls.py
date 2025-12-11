from django.urls import path
from . import views

app_name = 'vendor'

urlpatterns = [
    path('orders/', views.vendor_orders_list, name='orders_list'),
    path('orders/<int:vendor_order_id>/', views.vendor_order_detail, name='order_detail'),
    path('earnings/', views.vendor_earnings, name='earnings'),
]
