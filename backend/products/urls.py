from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductModelViewSet, CategoryModelViewSet, product_list, product_detail, create_product_view, update_product_view, delete_product_view, vendor_products_view, add_to_cart_view

router = DefaultRouter()
router.register(r'product', ProductModelViewSet)
router.register(r'category', CategoryModelViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    
    path('', product_list, name='product_list'),
    path('create/', create_product_view, name='create_product'),
    path('<int:product_id>/', product_detail, name='product_detail'),
    path('<int:product_id>/update/', update_product_view, name='update_product'),
    path('<int:product_id>/delete/', delete_product_view, name='delete_product'),
    path('vendor/', vendor_products_view, name='vendor_products'),
    path('add-to-cart/', add_to_cart_view, name='add_to_cart'),
]
