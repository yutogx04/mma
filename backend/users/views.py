from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from .models import User, Shop
from .forms import UserRegistrationForm, LoginForm, ShopForm
from .decorators import vendor_required, admin_required

# Template Views with request.method
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            response = requests.post(
                "http://127.0.0.1:8000/api/token/", 
                data={
                    "username": username,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                tokens = response.json()
                request.session['access_token'] = tokens['access']
                request.session['refresh_token'] = tokens['refresh']
                return redirect('dashboard')
            else:
                form.add_error(None, 'Identifiants invalides')
    else:
        form = LoginForm()
    
    return render(request, "registration/login.html", {'form': form})

def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Auto-login after registration
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, "registration/register.html", {'form': form})

def logout_view(request):
    if request.method == "POST":
        if 'access_token' in request.session:
            del request.session['access_token']
        if 'refresh_token' in request.session:
            del request.session['refresh_token']
        logout(request)
        return redirect('login')
    return render(request, "registration/logout.html")

@login_required
def dashboard_view(request):
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # Get user data
    user_response = requests.get(
        "http://127.0.0.1:8000/api/auth/profile/",
        headers=headers
    )
    user_data = user_response.json() if user_response.status_code == 200 else None
    
    return render(request, "dashboard.html", {
        'user_data': user_data
    })

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