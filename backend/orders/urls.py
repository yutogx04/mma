from django.urls import path
from . import views

urlpatterns = [
    # Template Views
    path('', views.order_list, name='order_list'),
    path('cart/', views.cart_view, name='cart_view'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    
    # API Views
    path('api/', views.order_list_api, name='order_list_api'),
    path('api/<int:order_id>/', views.order_detail_api, name='order_detail_api'),
    path('api/create/', views.order_create_api, name='order_create_api'),
    path('api/<int:order_id>/update/', views.order_update_api, name='order_update_api'),
    path('api/<int:order_id>/delete/', views.order_delete_api, name='order_delete_api'),
    path('api/<int:order_id>/checkout/', views.order_checkout_api, name='order_checkout_api'),
]