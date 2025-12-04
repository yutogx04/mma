from django.urls import path
from . import views

urlpatterns = [
    # Template Views
    path('frontend/<int:invoice_id>/', views.invoice_detail_view, name='invoice_detail'),
    
    # API Views
    path('api/create/', views.invoice_create_api, name='invoice_create_api'),
    path('api/<int:invoice_id>/', views.invoice_detail_api, name='invoice_detail_api'),
]