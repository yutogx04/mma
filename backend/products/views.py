from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import Product, Category
from .forms import ProductForm
from mma.backend.users.decorators import can_create_product, can_edit_product, can_delete_product
from django.http import HttpResponseForbidden


# Template Views
def product_list(request):
    if request.method == "POST":
        return _create_product(request)
    
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(name__icontains=search_query)
    if category_id:
        products = products.filter(category_id=category_id)
    
    categories = Category.objects.all()
    
    return render(request, "products/list.html", {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id
    })

def _create_product(request):
    if not request.user.is_authenticated or request.user.role != 'vendor':
        return render(request, "products/list.html", {
            'error': 'Only vendors can create products'
        })
    
    form = ProductForm(request.POST)
    if form.is_valid():
        product = form.save(commit=False)
        shop = request.user.shop_set.first()
        if shop:
            product.shop = shop
            product.save()
            return redirect('product_list')
        else:
            form.add_error(None, 'Vous devez avoir un magasin pour créer des produits')
    
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, "products/list.html", {
        'products': products,
        'categories': categories,
        'form': form
    })

def product_detail(request, product_id):
    if request.method == "POST":
        return _add_to_cart(request, product_id)
    
    product = get_object_or_404(Product, id=product_id)
    
    token = request.session.get('access_token')
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"http://127.0.0.1:8000/api/products/{product_id}/",
            headers=headers
        )
        product_data = response.json() if response.status_code == 200 else None
    else:
        product_data = None
    
    return render(request, "products/detail.html", {
        'product': product,
        'product_data': product_data
    })

def _add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    quantity = int(request.POST.get("quantity", 1))
    
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.post(
        "http://127.0.0.1:8000/api/orders/create/",
        data={
            "product_id": product_id,
            "quantity": quantity
        },
        headers=headers
    )
    
    if response.status_code == 201:
        return redirect('cart_view')
    else:
        product = get_object_or_404(Product, id=product_id)
        return render(request, "products/detail.html", {
            'product': product,
            'error': 'Failed to add to cart'
        })

@login_required
def create_product_view(request):
    """Create product with permission check"""
    if not can_create_product(request.user):
        return HttpResponseForbidden("You don't have permission to create products")
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            shop = request.user.get_shop()
            if shop:
                product.shop = shop
                product.save()
                return redirect('product_list')
            else:
                form.add_error(None, 'Vous devez avoir un magasin pour créer des produits')
    else:
        form = ProductForm()
    
    return render(request, "products/create.html", {'form': form})

@login_required
def update_product_view(request, product_id):
    """Update product with permission check"""
    product = get_object_or_404(Product, id=product_id)
    
    if not can_edit_product(request.user, product):
        return HttpResponseForbidden("You don't have permission to edit this product")
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)
    
    return render(request, "products/update.html", {'form': form})

@login_required
def delete_product_view(request, product_id):
    """Delete product with permission check"""
    product = get_object_or_404(Product, id=product_id)
    
    if not can_delete_product(request.user, product):
        return HttpResponseForbidden("You don't have permission to delete this product")
    
    if request.method == "POST":
        token = request.session.get('access_token')
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        response = requests.delete(
            f"http://127.0.0.1:8000/api/products/{product_id}/delete/",
            headers=headers
        )
        
        if response.status_code == 204:
            return redirect('product_list')
        else:
            return render(request, "products/list.html", {
                'error': 'Failed to delete product'
            })
    
    return render(request, "products/delete_confirm.html", {
        'product': product
    })

# API Views
@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.all()
    data = [{
        'id': product.id,
        'name': product.name,
        'price': str(product.price),
        'stock_quantity': product.stock_quantity,
        'shop_name': product.shop.name,
        'category_name': product.category.name
    } for product in products]
    return Response(data)

@api_view(['GET'])
def product_detail_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    data = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),
        'stock_quantity': product.stock_quantity,
        'shop': {
            'id': product.shop.id,
            'name': product.shop.name
        },
        'category': {
            'id': product.category.id,
            'name': product.category.name
        },
        'created_at': product.created_at
    }
    return Response(data)

@api_view(['POST'])
@permission_required('products.add_product', raise_exception=True)
def product_create_api(request):
    if not can_create_product(request.user):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    name = request.data.get('name')
    price = request.data.get('price')
    description = request.data.get('description')
    stock_quantity = request.data.get('stock_quantity')
    category_id = request.data.get('category_id')
    shop_id = request.data.get('shop_id')
    
    if not all([name, price, description, stock_quantity, category_id, shop_id]):
        return Response(
            {'error': 'All fields are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    shop = get_object_or_404(request.user.shop_set, id=shop_id)
    category = get_object_or_404(Category, id=category_id)
    
    product = Product.objects.create(
        shop=shop,
        category=category,
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity
    )
    
    return Response({
        'id': product.id,
        'name': product.name,
        'message': 'Product created successfully'
    }, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_required('products.delete_product', raise_exception=True)
def product_delete_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not can_delete_product(request.user, product):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not can_edit_product(request.user, product):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    if 'name' in request.data:
        product.name = request.data['name']
    if 'description' in request.data:
        product.description = request.data['description']
    if 'price' in request.data:
        product.price = request.data['price']
    if 'stock_quantity' in request.data:
        product.stock_quantity = request.data['stock_quantity']
    if 'category_id' in request.data:
        category = get_object_or_404(Category, id=request.data['category_id'])
        product.category = category
    
    product.save()
    
    return Response({
        'id': product.id,
        'name': product.name,
        'message': 'Product updated successfully'
    })

@api_view(['DELETE'])
@permission_required('products.delete_product', raise_exception=True)
def product_delete_api(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop__user=request.user)
    
    if product.orderitem_set.exists():
        return Response(
            {'error': 'Cannot delete product with existing orders'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    product_name = product.name
    product.delete()
    
    return Response({
        'message': f'Product "{product_name}" deleted successfully'
    }, status=status.HTTP_204_NO_CONTENT)