from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    order_list, order_detail, cart_view, add_to_cart_view,
    OrderViewSet, CartItemViewSet
)

router = DefaultRouter()
router.register(r'order', OrderViewSet)
router.register(r'cart-item', CartItemViewSet)

urlpatterns = [
    path('', order_list, name='order_list'),
    path('cart/', cart_view, name='cart_view'),
    path('<int:order_id>/', order_detail, name='order_detail'),
    path('add/', add_to_cart_view, name='add_to_cart'),
    
    path('api/', include(router.urls)),
]