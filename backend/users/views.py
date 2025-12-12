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

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
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
    else:
        form = LoginForm()
    
    return render(request, "registration/login.html", {'form': form})

from payments.models import PaymentMethod
import uuid

@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'customer'  # Hardcode customer role
            user.save()
            
            # Save Payment Method
            card_number = form.cleaned_data['card_number']
            PaymentMethod.objects.create(
                user=user,
                card_type=form.cleaned_data['card_type'],
                card_last_four=card_number[-4:],
                card_holder_name=form.cleaned_data['card_holder'],
                expiry_month=form.cleaned_data['expiry_month'],
                expiry_year=form.cleaned_data['expiry_year'],
                payment_token=str(uuid.uuid4()),
                is_default=True
            )
            
            login(request, user)
            messages.success(request, "Compte créé avec succès et moyen de paiement enregistré!")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, "registration/register.html", {'form': form})

@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.success(request, "Déconnexion réussie")
    return redirect('login')

@require_http_methods(["GET"])
@login_required
def dashboard_view(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    
    user_data = {
        'username': request.user.username,
        'email': request.user.email,
        'role': request.user.role,
        'date_joined': request.user.date_joined,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name
    }
    
    
    # Recent orders - no permission check needed
    recent_orders = []
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    if request.user.role == 'customer':
        recent_orders = Order.objects.filter(
            user=request.user, 
            created_at__gte=thirty_days_ago
        ).exclude(status='cart').order_by('-created_at')[:5]
    elif request.user.role == 'vendor':
        recent_orders = Order.objects.filter(
            orderitem__product__shop__user=request.user,
            created_at__gte=thirty_days_ago
        ).exclude(status='cart').distinct().order_by('-created_at')[:5]
    elif request.user.role == 'admin':
        recent_orders = Order.objects.filter(
            created_at__gte=thirty_days_ago
        ).exclude(status='cart').order_by('-created_at')[:5]
    
    popular_products = Product.objects.annotate(
        order_count=Count('orderitem')
    ).order_by('-order_count')[:6]
    
    recent_products = []
    if request.user.role == 'vendor':
        recent_products = Product.objects.filter(
            shop__user=request.user
        ).order_by('-created_at')[:5]
    
    user_shop = None
    if request.user.role == 'vendor':
        user_shop = Shop.objects.filter(user=request.user).first()
    
    total_products = 0
    low_stock_products = 0
    out_of_stock_products = 0
    
    if request.user.role == 'vendor' and user_shop:
        total_products = Product.objects.filter(shop=user_shop).count()
        low_stock_products = Product.objects.filter(shop=user_shop, stock_quantity__lt=10).count()
        out_of_stock_products = Product.objects.filter(shop=user_shop, stock_quantity=0).count()
    
    context = {
        'user_data': user_data,
        'recent_orders': recent_orders,
        'popular_products': popular_products,
        'recent_products': recent_products,
        'user_shop': user_shop,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'notifications': request.user.notifications.all()[:5]
    }
    
    # Add cart items count
    cart = Order.objects.filter(user=request.user, status='cart').first()
    if cart:
        context['cart_items'] = cart.orderitem_set.count()
    else:
        context['cart_items'] = 0
    
    return render(request, "dashboard.html", context)

@require_http_methods(["GET", "POST"])
@login_required
def profile_update_view(request):
    if request.method == 'POST' and request.POST.get('_method') == 'PUT':
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
    
    return render(request, "users/profile.html", {'user': request.user})

def vendor_register_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        shop_name = request.POST.get('shop_name')
        shop_description = request.POST.get('shop_description')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='vendor'
            )
            

            Shop.objects.create(
                user=user,
                name=shop_name,
                description=shop_description
            )
            
            # Payment Method for Vendor
            card_number = request.POST.get('card_number', '0000')
            card_type = request.POST.get('card_type', 'credit_card')
            PaymentMethod.objects.create(
                user=user,
                card_type=card_type,
                card_last_four=card_number[-4:],
                card_holder_name=request.POST.get('card_holder', 'Unknown'),
                expiry_month=request.POST.get('expiry_month', 12),
                expiry_year=request.POST.get('expiry_year', 2025),
                payment_token=str(uuid.uuid4()),
                is_default=True
            )
            
            login(request, user)
            messages.success(request, "Compte vendeur créé avec succès!")
            return redirect('dashboard')
            
        except Exception as e:
            return render(request, "registration/vendor_register.html", {
                'error': f'Registration failed: {str(e)}'
            })
    
    return render(request, "registration/vendor_register.html")

@vendor_required
def vendor_dashboard_view(request):
    shop = get_object_or_404(Shop, user=request.user)
    
    total_products = Product.objects.filter(shop=shop).count()
    low_stock_products = Product.objects.filter(shop=shop, stock_quantity__lt=10).count()
    out_of_stock_products = Product.objects.filter(shop=shop, stock_quantity=0).count()
    
    recent_orders = Order.objects.filter(
        orderitem__product__shop=shop
    ).distinct().order_by('-created_at')[:10]
    
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
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/')

@login_required
def admin_user_management_view(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/users/compte/')

@login_required
def admin_shop_management_view(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/shop/shop/')

@login_required
def admin_product_management_view(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/products/product/')

@login_required
def admin_order_management_view(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Admin access required")
    return redirect('/admin/orders/order/')