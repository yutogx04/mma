from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.authentication import SessionAuthentication
import pika
import json
from config import RABBITMQ_HOST
from .models import Order, OrderItem, VendorOrder
from .serializers import OrderSerializer, OrderItemSerializer
from products.models import Product
from django.db.models import Sum, Count
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from django.contrib import messages


@require_http_methods(["GET"])
@login_required
def order_list(request):
    status_filter = request.GET.get('status', '')
    
    if request.user.role == 'customer':
        orders = Order.objects.filter(user=request.user)
    elif request.user.role == 'vendor':
        orders = Order.objects.filter(orderitem__product__shop__user=request.user).distinct()
    else:
        orders = Order.objects.all()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    orders = orders.order_by('-created_at')
    return render(request, "orders/list.html", {'orders': orders})



@require_http_methods(["GET", "POST"])
@login_required
def order_detail(request, order_id):
    order = _get_order_by_user_role(request, order_id)
    
    if request.method == 'POST':
        return _handle_order_post_actions(request, order)
    
    return render(request, "orders/detail.html", {'order': order})

def _get_order_by_user_role(request, order_id):
    """Get order based on user role and permissions"""
    if request.user.role == 'customer':
        return get_object_or_404(Order, id=order_id, user=request.user)
    elif request.user.role == 'vendor':
        return _get_vendor_order(order_id, request.user)
    else:
        return get_object_or_404(Order, id=order_id)

def _get_vendor_order(order_id, user):
    """Get order for vendor user"""
    order = Order.objects.filter(
        id=order_id,
        orderitem__product__shop__user=user
    ).distinct().first()
    if not order:
        raise Http404("Order not found")
    return order

def _handle_order_post_actions(request, order):
    """Handle POST actions for order detail"""
    action = request.POST.get("action")
    
    if action == "cancel_order":
        return _handle_cancel_order(request, order)
    elif action == "update_status":
        return _handle_update_status(request, order)

def _handle_cancel_order(request, order):
    """Handle order cancellation"""
    if order.status in ['cart', 'pending']:
        order.status = 'cancelled'
        order.save()
        messages.success(request, "Commande annulée avec succès")
    return redirect('order_list')

def _handle_update_status(request, order):
    """Handle order status updates"""
    new_status = request.POST.get("status")
    can_update = (request.user.role == 'vendor' and new_status in ['shipped', 'delivered']) or request.user.role == 'admin'
    
    if can_update:
        order.status = new_status
        order.save()
        messages.success(request, "Statut mis à jour: {}".format(new_status))
    
    return redirect('order_detail', order_id=order.id)



@require_http_methods(["GET", "POST"])
@login_required
def cart_view(request):
    cart = Order.objects.filter(user=request.user, status='cart').first()
    
    if request.method == 'POST':
        action = request.POST.get("action")
        
        if action == "update_quantity":
            _handle_update_quantity(request)
            return redirect('cart_view')
        elif action == "remove_item":
            _handle_remove_item(request)
            return redirect('cart_view')
        elif action == "checkout":
            return _handle_checkout(request, cart)
        elif action == "clear_cart":
            _handle_clear_cart(request, cart)
            return redirect('cart_view')
    
    return render(request, "orders/cart.html", {'cart': cart})

def _handle_update_quantity(request):
    """Handle cart quantity updates"""
    item_id = request.POST.get("item_id")
    quantity = int(request.POST.get("quantity", 1))
    cart_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        cart = Order.objects.filter(user=request.user, status='cart').first()
        if cart:
            cart.total_amount = sum(item.quantity * item.price for item in cart.orderitem_set.all())
            cart.save()
        messages.success(request, "Quantité mise à jour")

def _handle_remove_item(request):
    """Handle item removal from cart"""
    item_id = request.POST.get("item_id")
    cart_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    cart_item.delete()
    cart = Order.objects.filter(user=request.user, status='cart').first()
    if cart:
        cart.total_amount = sum(item.quantity * item.price for item in cart.orderitem_set.all())
        cart.save()
    messages.success(request, "Article retiré du panier")

def _handle_checkout(request, cart):
    """Handle checkout process"""
    if not cart or not cart.orderitem_set.exists():
        messages.error(request, "Panier vide")
        return redirect('cart_view')
    
    # Check stock availability before checkout
    stock_errors = _check_stock_availability(cart)
    if stock_errors:
        for error in stock_errors:
            messages.error(request, error)
        return redirect('cart_view')
    
    # Decrement stock quantities
    _decrement_stock_quantities(cart)
    
    # Change cart to order
    cart.status = 'pending'
    cart.save()
    
    # Process marketplace logic
    _process_marketplace_orders(cart, request.user)
    
    # Send to payment queue
    _send_to_payment_queue(cart, request.user)
    
    vendor_count = len(_group_items_by_vendor(cart))
    messages.success(request, "Commande passée avec succès! Répartie entre {} vendeur(s).".format(vendor_count))
    return redirect('order_list')

def _check_stock_availability(cart):
    """Check stock availability for all cart items"""
    errors = []
    for item in cart.orderitem_set.all():
        if item.quantity > item.product.stock_quantity:
            error = "Stock insuffisant pour {}. Disponible: {}".format(
                item.product.name, item.product.stock_quantity)
            errors.append(error)
    return errors

def _decrement_stock_quantities(cart):
    """Decrement stock quantities for all cart items"""
    for item in cart.orderitem_set.all():
        item.product.stock_quantity -= item.quantity
        item.product.save()

def _group_items_by_vendor(cart):
    """Group cart items by vendor"""
    from collections import defaultdict
    items_by_vendor = defaultdict(list)
    for item in cart.orderitem_set.all():
        vendor = item.product.shop.user
        items_by_vendor[vendor].append(item)
    return items_by_vendor

def _process_marketplace_orders(cart, user):
    """Process marketplace order splitting and vendor notifications"""
    from collections import defaultdict
    from orders.models import VendorOrder
    from django.utils import timezone
    
    items_by_vendor = _group_items_by_vendor(cart)
    
    # Create VendorOrders
    for vendor, items in items_by_vendor.items():
        vendor_total = sum(item.quantity * item.price for item in items)
        platform_fee = vendor_total * Decimal('0.10')  # 10% commission
        vendor_payout = vendor_total - platform_fee
        
        vendor_order = VendorOrder.objects.create(
            order=cart,
            vendor=vendor,
            vendor_total=vendor_total,
            platform_fee=platform_fee,
            vendor_payout=vendor_payout,
            status='pending'
        )
        
        # Link items to vendor order
        for item in items:
            item.vendor_order = vendor_order
            item.status = 'pending'
            item.save()
        
        # Notify vendor
        _notify_vendor(vendor, vendor_order, vendor_total)

def _notify_vendor(vendor, vendor_order, vendor_total):
    """Send notification to vendor"""
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user=vendor,
            type='new_order',
            message="Nouvelle commande! VendorOrder #{} - ${}".format(vendor_order.id, vendor_total),
            related_id=vendor_order.id
        )
    except:
        pass

def _send_to_payment_queue(cart, user):
    """Send payment message to RabbitMQ queue"""
    message = {
        "order_id": cart.id,
        "user_id": user.id,
        "amount": str(cart.total_amount),
        "status": "en attente de paiement"
    }
    

    try:
        with pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue='payment', durable=True)
            channel.basic_publish(
                exchange='',
                routing_key='payment',
                body=json.dumps(message)
            )
    except pika.exceptions.AMQPConnectionError as e:
        print("RabbitMQ connection error: {}".format(e))

def _handle_clear_cart(request, cart):
    """Handle cart clearing"""
    if cart:
        cart.orderitem_set.all().delete()
        cart.total_amount = 0
        cart.save()
        messages.success(request, "Panier vidé")


@require_http_methods(["POST"])
@login_required
def add_to_cart_view(request):
    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 1))
    
    if not product_id:
        messages.error(request, "Produit non spécifié")
        return redirect('product_list')
    
    product = get_object_or_404(Product, id=product_id)
    

    if quantity > product.stock_quantity:
        messages.error(request, f"Stock insuffisant. Disponible: {product.stock_quantity}")
        return redirect('product_detail', product_id=product_id)
    
    cart, _ = Order.objects.get_or_create(
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
    
    cart.total_amount = sum(item.quantity * item.price for item in cart.orderitem_set.all())
    cart.save()
    
    messages.success(request, f"{product.name} ajouté au panier")
    return redirect('cart_view')


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
        
        for item in order.orderitem_set.all():
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
        } for item in order.orderitem_set.all()]
    }
    
    return Response(data)


@api_view(['POST'])
@login_required
def order_create_api(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    

    product = get_object_or_404(Product, id=product_id)
    
    cart, _ = Order.objects.get_or_create(
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
    
    cart.total_amount = sum(item.quantity * item.price for item in cart.orderitem_set.all())
    cart.save()
    
    return Response({
        'order_id': cart.id,
        'message': 'Product added to cart',
        'cart_total': str(cart.total_amount),
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
        if new_status:
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
    
    order.status = 'cancelled'
    order.save()
    
    return Response(
        {'message': 'Order cancelled successfully'},
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


@api_view(['GET'])
@login_required
def cart_api(request):
    cart = Order.objects.filter(user=request.user, status='cart').first()
    
    if not cart:
        return Response({'message': 'Cart is empty'}, status=status.HTTP_200_OK)
    
    data = {
        'id': cart.id,
        'total_amount': str(cart.total_amount),
        'items': [{
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': str(item.price),
            'subtotal': str(item.quantity * item.price)
        } for item in cart.orderitem_set.all()]
    }
    
    return Response(data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return Order.objects.filter(user=user)
        elif user.role == 'vendor':
            return Order.objects.filter(orderitem__product__shop__user=user).distinct()
        return Order.objects.all()


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def get_queryset(self):
        return OrderItem.objects.filter(
            order__user=self.request.user,
            order__status='cart'
        )
    
    def perform_update(self, serializer):
        instance = serializer.save()
        cart = instance.order
        cart.total_amount = sum(
            item.quantity * item.price 
            for item in cart.orderitem_set.all()
        )
        cart.save()
    
    def perform_destroy(self, instance):
        cart = instance.order
        instance.delete()
        cart.total_amount = sum(
            item.quantity * item.price 
            for item in cart.orderitem_set.all()
        )
        cart.save()