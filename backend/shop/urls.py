from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShopModelViewSet

router = DefaultRouter()
router.register(r'shop', ShopModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
