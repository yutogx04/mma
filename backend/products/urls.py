from django.urls import path
from . import views

urlpatterns = [
    # Template Views
    path('', views.product_list, name='product_list'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('create/', views.create_product_view, name='product_create'),
    path('<int:product_id>/update/', views.update_product_view, name='product_update'),
    path('<int:product_id>/delete/', views.delete_product_view, name='product_delete'),
    
    # API Views
    path('api/', views.product_list_api, name='product_list_api'),
    path('api/<int:product_id>/', views.product_detail_api, name='product_detail_api'),
    path('api/create/', views.product_create_api, name='product_create_api'),
    path('api/<int:product_id>/update/', views.product_update_api, name='product_update_api'),
    path('api/<int:product_id>/delete/', views.product_delete_api, name='product_delete_api'),
]