from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import RedirectView
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', include('utils.urls')),
    
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    
    path('api/auth/', include('users.urls')),
    path('products/', include('products.urls')),
    path('api/shops/', include('shop.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/invoices/', include('invoices.urls')),
    path('api/reviews/', include('reviews.urls')),
    
    path('dashboard/', user_views.dashboard_view, name='dashboard'),
    path('auth/', include('users.urls')),
]