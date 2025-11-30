from django.urls import path
from . import views

urlpatterns = [
    # Template Views
    path('<int:order_id>/create/', views.payment_create_view, name='payment_create'),
    
    # API Views
    path('api/create/', views.payment_create_api, name='payment_create_api'),
    path('api/<int:payment_id>/', views.payment_detail_api, name='payment_detail_api'),
]