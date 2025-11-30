from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Template Views
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('shops/create/', views.create_shop_view, name='create_shop'),
    
    # API Views
    path('api/login/', views.user_login_api, name='user_login_api'),
    path('api/register/', views.user_register_api, name='user_register_api'),
    path('api/profile/', views.user_profile_api, name='user_profile_api'),
    path('api/profile/update/', views.user_update_api, name='user_update_api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]