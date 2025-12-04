from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Template Views (Course 2 pattern)
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('register/vendor/', views.vendor_register_view, name='vendor_register'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('vendor/dashboard/', views.vendor_dashboard_view, name='vendor_dashboard'),
    path('shops/create/', views.create_shop_view, name='create_shop'),
    
    # API Views (Course 2 - Microservices pattern)
    path('api/login/', views.user_login_api, name='user_login_api'),
    path('api/register/', views.user_register_api, name='user_register_api'),
    path('api/profile/', views.user_profile_api, name='user_profile_api'),
    path('api/profile/update/', views.user_update_api, name='user_update_api'),

    # JWT Token endpoints (Course 1 pattern)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]