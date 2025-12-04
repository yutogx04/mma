from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.db.models import Count, Sum
from products.models import Product
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from  orders.models import Order, OrderItem
from .models import User
from shop.models import Shop
from .forms import UserRegistrationForm, LoginForm
from shop.forms import ShopForm
from .decorators import vendor_required

# Template Views with request.method
@require_http_methods(["GET", "POST"])
def login_view(request):
    """GET: Show form, POST: Authenticate"""
    if request.method == 'POST':  # ✅ POST - Login
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue {username}!")
                return redirect('dashboard')
            else:
                form.add_error(None, 'Identifiants invalides')
    else:  # ✅ GET - Show form
        form = LoginForm()
    
    return render(request, "registration/login.html", {'form': form})

# REGISTER - GET/POST
@require_http_methods(["GET", "POST"])
def register_view(request):
    """GET: Show form, POST: Create user"""
    if request.method == 'POST':  # ✅ POST - Register
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé avec succès!")
            return redirect('dashboard')
    else:  # ✅ GET - Show form
        form = UserRegistrationForm()
    
    return render(request, "registration/register.html", {'form': form})

# LOGOUT - POST only
@require_http_methods(["POST"])
def logout_view(request):
    """POST: Logout user"""
    logout(request)
    messages.success(request, "Déconnexion réussie")
    return redirect('login')

# DASHBOARD - GET only
@require_http_methods(["GET"])
@login_required
def dashboard_view(request):
    """GET: Show dashboard"""
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    
    # Get user data
    user_data = {
        'username': request.user.username,
        'email': request.user.email,
        'role': request.user.role,
        'date_joined': request.user.date_joined,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name
    }
    
    # Recent orders (last 30 days)
    recent_orders = []
    if request.user.has_perm('orders.view_order'):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        if request.user.role == 'customer':
            recent_orders = Order.objects.filter(
                user=request.user, 
                created_at__gte=thirty_days_ago
            ).order_by('-created_at')[:5]
        elif request.user.role == 'vendor':
            recent_orders = Order.objects.filter(
                orderitem__product__shop__user=request.user,
                created_at__gte=thirty_days_ago
            ).distinct().order_by('-created_at')[:5]
        elif request.user.role == 'admin':
            recent_orders = Order.objects.filter(
                created_at__gte=thirty_days_ago
            ).order_by('-created_at')[:5]
    
    # Popular products
    popular_products = Product.objects.annotate(
        order_count=Count('orderitem')
    ).order_by('-order_count')[:6]
    
    # Recent products for vendors
    recent_products = []
    if request.user.role == 'vendor':
        recent_products = Product.objects.filter(
            shop__user=request.user
        ).order_by('-created_at')[:5]
    
    # Shop information for vendors
    user_shop = None
    if request.user.role == 'vendor':
        user_shop = Shop.objects.filter(user=request.user).first()
    
    # Vendor metrics
    total_products = 0
    low_stock_products = 0
    out_of_stock_products = 0
    
    if request.user.role == 'vendor' and user_shop:
        total_products = Product.objects.filter(shop=user_shop).count()
        low_stock_products = Product.objects.filter(shop=user_shop, stock_quantity__lt=10).count()
        out_of_stock_products = Product.objects.filter(shop=user_shop, stock_quantity=0).count()
    
    # Create the context dictionary
    context = {
        'user_data': user_data,
        'recent_orders': recent_orders,
        'popular_products': popular_products,
        'recent_products': recent_products,
        'user_shop': user_shop,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
    }
    
    return render(request, "dashboard.html", context)

# PROFILE UPDATE - GET/PUT
@require_http_methods(["GET", "POST"])
@login_required
def profile_update_view(request):
    """GET: Show form, POST/PUT: Update profile"""
    if request.method == 'POST' and request.POST.get('_method') == 'PUT':
        # ✅ PUT - Update profile
        user = request.user
        if 'email' in request.POST:
            user.email = request.POST['email']
        if 'first_name' in request.POST:
            user.first_name = request.POST['first_name']
        if 'last_name' in request.POST:
            user.last_name = request.POST['last_name']
        
        user.save()
        messages.success(request, "Profil mis à jour avec succès")
        return redirect('dashboard')
    
    # ✅ GET - Show form
    return render(request, "users/profile.html", {'user': request.user})

# Vendor Registration View
def vendor_register_view(request):
    """Handle vendor registration with shop creation"""
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        shop_name = request.POST.get('shop_name')
        shop_description = request.POST.get('shop_description')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='vendor'
            )
            
            # Create shop
            shop = Shop.objects.create(
                user=user,
                name=shop_name,
                description=shop_description
            )
            
            # Auto-login
            login(request, user)
            return redirect('dashboard')
            
        except Exception as e:
            return render(request, "registration/vendor_register.html", {
                'error': f'Registration failed: {str(e)}'
            })
    
    return render(request, "registration/vendor_register.html")

# Vendor-specific dashboard
@vendor_required
def vendor_dashboard_view(request):
    """Vendor-specific dashboard with shop metrics"""
    shop = get_object_or_404(Shop, user=request.user)
    
    # Vendor metrics
    total_products = Product.objects.filter(shop=shop).count()
    low_stock_products = Product.objects.filter(shop=shop, stock_quantity__lt=10).count()
    out_of_stock_products = Product.objects.filter(shop=shop, stock_quantity=0).count()
    
    # Recent orders for vendor's products
    recent_orders = Order.objects.filter(
        orderitem__product__shop=shop
    ).distinct().order_by('-created_at')[:10]
    
    # Sales data (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_sales = OrderItem.objects.filter(
        product__shop=shop,
        order__created_at__gte=thirty_days_ago,
        order__status__in=['paid', 'shipped', 'delivered']
    ).aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('price')
    )
    
    context = {
        'shop': shop,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'recent_orders': recent_orders,
        'recent_sales': recent_sales,
    }
    
    return render(request, "vendor_dashboard.html", context)

@vendor_required
def create_shop_view(request):
    if request.method == 'POST':
        form = ShopForm(request.POST)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.user = request.user
            shop.save()
            return redirect('vendor_dashboard')
    else:
        form = ShopForm()
    
    return render(request, "shops/create.html", {'form': form})

# API Views
@api_view(['POST'])
def user_login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
    return Response(
        {'error': 'Invalid credentials'}, 
        status=status.HTTP_401_UNAUTHORIZED
    )

@api_view(['POST'])
def user_register_api(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    role = request.data.get('role', 'customer')
    
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role
    )
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        },
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@login_required
def user_profile_api(request):
    user = request.user
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined
    }
    
    if user.role == 'vendor':
        shops = Shop.objects.filter(user=user)
        data['shops'] = [{
            'id': shop.id,
            'name': shop.name,
            'description': shop.description
        } for shop in shops]
    
    return Response(data)

@api_view(['PUT'])
@login_required
def user_update_api(request):
    user = request.user
    
    if 'email' in request.data:
        user.email = request.data['email']
    if 'first_name' in request.data:
        user.first_name = request.data['first_name']
    if 'last_name' in request.data:
        user.last_name = request.data['last_name']
    
    user.save()
    
    return Response({
        'message': 'Profile updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    })

@login_required
def admin_dashboard_view(request):
    """Redirect to Django admin"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/')

@login_required
def admin_user_management_view(request):
    """Redirect to Django admin users"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/users/compte/')

@login_required
def admin_shop_management_view(request):
    """Redirect to Django admin shops"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/shop/shop/')

@login_required
def admin_product_management_view(request):
    """Redirect to Django admin products"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/products/product/')

@login_required
def admin_order_management_view(request):
    """Redirect to Django admin orders"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/orders/order/')