from django.urls import path
from . import views

urlpatterns = [
    path('frontend/<int:order_id>/create/', views.payment_create_view, name='payment_create'),
    
    path('create/', views.payment_create_api, name='payment_create_api'),
    path('<int:payment_id>/', views.payment_detail_api, name='payment_detail_api'),
]