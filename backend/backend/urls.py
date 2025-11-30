from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/invoices/', include('invoices.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('', lambda request: redirect('dashboard')),
    path('dashboard/', include('users.urls')),
]