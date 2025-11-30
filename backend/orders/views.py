from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import Order, OrderItem
from products.models import Product
from users.decorators import vendor_required

# Template Views
@login_required
def order_list(request):
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.get(
        "http://127.0.0.1:8000/api/orders/",
        headers=headers
    )
    
    orders = response.json() if response.status_code == 200 else []
    
    return render(request, "orders/list.html", {
        'orders': orders
    })

@login_required
def cart_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "update_quantity":
            return _update_cart_quantity(request)
        elif action == "remove_item":
            return _remove_cart_item(request)
        elif action == "checkout":
            return _checkout_cart(request)
    
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.get(
        "http://127.0.0.1:8000/api/orders/cart/",
        headers=headers
    )
    
    cart_data = response.json() if response.status_code == 200 else None
    
    return render(request, "orders/cart.html", {
        'cart': cart_data
    })

def _update_cart_quantity(request):
    item_id = request.POST.get("item_id")
    quantity = int(request.POST.get("quantity", 1))
    
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.put(
        f"http://127.0.0.1:8000/api/order-items/{item_id}/update/",
        data={"quantity": quantity},
        headers=headers
    )
    
    return redirect('cart_view')

def _remove_cart_item(request):
    item_id = request.POST.get("item_id")
    
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.delete(
        f"http://127.0.0.1:8000/api/order-items/{item_id}/delete/",
        headers=headers
    )
    
    return redirect('cart_view')

def _checkout_cart(request):
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.get(
        "http://127.0.0.1:8000/api/orders/cart/",
        headers=headers
    )
    
    if response.status_code == 200:
        cart_data = response.json()
        order_id = cart_data.get('id')
        
        checkout_response = requests.post(
            f"http://127.0.0.1:8000/api/orders/{order_id}/checkout/",
            headers=headers
        )
        
        if checkout_response.status_code == 200:
            return redirect('order_list')
        else:
            return render(request, "orders/cart.html", {
                'cart': cart_data,
                'error': 'Checkout failed'
            })
    
    return redirect('cart_view')

@login_required
def order_detail(request, order_id):
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "cancel_order":
            return _cancel_order(request, order_id)
        elif action == "update_status":
            return _update_order_status(request, order_id)
    
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.get(
        f"http://127.0.0.1:8000/api/orders/{order_id}/",
        headers=headers
    )
    
    order_data = response.json() if response.status_code == 200 else None
    
    return render(request, "orders/detail.html", {
        'order': order_data
    })

def _cancel_order(request, order_id):
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.delete(
        f"http://127.0.0.1:8000/api/orders/{order_id}/delete/",
        headers=headers
    )
    
    if response.status_code == 204:
        return redirect('order_list')
    else:
        return render(request, "orders/detail.html", {
            'error': 'Failed to cancel order'
        })

def _update_order_status(request, order_id):
    new_status = request.POST.get("status")
    
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.put(
        f"http://127.0.0.1:8000/api/orders/{order_id}/update/",
        data={"status": new_status},
        headers=headers
    )
    
    return redirect('order_detail', order_id=order_id)

# API Views
@api_view(['GET'])
@login_required
def order_list_api(request):
    if request.user.role == 'customer':
        orders = Order.objects.filter(user=request.user)
    elif request.user.role == 'vendor':
        orders = Order.objects.filter(orderitem__product__shop__user=request.user).distinct()
    else:
        orders = Order.objects.all()
    
    data = []
    for order in orders:
        order_data = {
            'id': order.id,
            'status': order.status,
            'total_amount': str(order.total_amount),
            'created_at': order.created_at,
            'user': order.user.username,
            'items': []
        }
        
        items = OrderItem.objects.filter(order=order)
        for item in items:
            order_data['items'].append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': str(item.price),
                'subtotal': str(item.quantity * item.price)
            })
        
        data.append(order_data)
    
    return Response(data)

@api_view(['GET'])
@login_required
def order_detail_api(request, order_id):
    if request.user.role == 'customer':
        order = get_object_or_404(Order, id=order_id, user=request.user)
    elif request.user.role == 'vendor':
        order = get_object_or_404(Order, id=order_id, orderitem__product__shop__user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)
    
    items = OrderItem.objects.filter(order=order)
    
    data = {
        'id': order.id,
        'status': order.status,
        'total_amount': str(order.total_amount),
        'created_at': order.created_at,
        'updated_at': order.updated_at,
        'user': {
            'id': order.user.id,
            'username': order.user.username,
            'email': order.user.email
        },
        'items': [{
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': str(item.price),
            'subtotal': str(item.quantity * item.price)
        } for item in items]
    }
    
    return Response(data)

@api_view(['POST'])
@login_required
def order_create_api(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    
    product = get_object_or_404(Product, id=product_id)
    
    cart, created = Order.objects.get_or_create(
        user=request.user,
        status='cart',
        defaults={'total_amount': 0}
    )
    
    order_item, item_created = OrderItem.objects.get_or_create(
        order=cart,
        product=product,
        defaults={'quantity': quantity, 'price': product.price}
    )
    
    if not item_created:
        order_item.quantity += quantity
        order_item.save()
    
    cart_total = sum(item.quantity * item.price for item in cart.orderitem_set.all())
    cart.total_amount = cart_total
    cart.save()
    
    return Response({
        'order_id': cart.id,
        'message': 'Product added to cart',
        'cart_total': str(cart_total),
        'items_count': cart.orderitem_set.count()
    }, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@login_required
def order_update_api(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.user.role == 'customer' and order.user == request.user:
        new_status = request.data.get('status')
        if new_status == 'cancelled' and order.status in ['cart', 'pending']:
            order.status = new_status
            order.save()
    
    elif request.user.role == 'vendor':
        if order.orderitem_set.filter(product__shop__user=request.user).exists():
            new_status = request.data.get('status')
            if new_status in ['shipped', 'delivered']:
                order.status = new_status
                order.save()
    
    elif request.user.role == 'admin':
        new_status = request.data.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
    
    return Response({
        'id': order.id,
        'status': order.status,
        'message': 'Order updated successfully'
    })

@api_view(['DELETE'])
@login_required
def order_delete_api(request, order_id):
    if request.user.role == 'customer':
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status not in ['cart', 'pending']:
            return Response(
                {'error': 'Cannot delete order in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    elif request.user.role == 'admin':
        order = get_object_or_404(Order, id=order_id)
    else:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    order.delete()
    return Response(
        {'message': 'Order deleted successfully'},
        status=status.HTTP_204_NO_CONTENT
    )

@api_view(['POST'])
@login_required
def order_checkout_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, status='cart')
    
    if not order.orderitem_set.exists():
        return Response(
            {'error': 'Cart is empty'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    for item in order.orderitem_set.all():
        if item.quantity > item.product.stock_quantity:
            return Response({
                'error': f'Not enough stock for {item.product.name}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    order.status = 'pending'
    order.save()
    
    for item in order.orderitem_set.all():
        item.product.stock_quantity -= item.quantity
        item.product.save()
    
    return Response({
        'order_id': order.id,
        'message': 'Checkout successful',
        'total_amount': str(order.total_amount)
    })