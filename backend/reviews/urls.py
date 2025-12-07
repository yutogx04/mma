from django.urls import path
from . import views

urlpatterns = [
    path('<int:product_id>/create/', views.review_create_view, name='review_create'),
    
    path('api/create/', views.review_create_api, name='review_create_api'),
    path('api/<int:review_id>/delete/', views.review_delete_api, name='review_delete_api'),
    path('api/product/<int:product_id>/', views.product_reviews_api, name='product_reviews_api'),
]