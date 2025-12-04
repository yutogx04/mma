"""
Utils App URLs
Health Check route for Consul
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health'),
]
