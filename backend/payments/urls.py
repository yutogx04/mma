from django.urls import path
from . import views

urlpatterns = [
    # Template View (for payment form)
    path('frontend/<int:order_id>/create/', views.payment_create_view, name='payment_create'),
    
    # API Views (mounted under /api/payments/)
    path('create/', views.payment_create_api, name='payment_create_api'),
    path('<int:payment_id>/', views.payment_detail_api, name='payment_detail_api'),
]