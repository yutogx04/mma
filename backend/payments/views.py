from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from orders.models import Order


@login_required
def payment_create_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "credit_card")
        
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            payment_method=payment_method,
            status='pending'
        )
        
        payment.status = 'succeeded'
        payment.save()
        
        order.status = 'paid'
        order.save()
        
        for item in order.orderitem_set.all():
            if item.product.stock_quantity >= item.quantity:
                item.product.stock_quantity -= item.quantity
                item.product.save()
        
        messages.success(request, f"✅ Paiement de ${order.total_amount} effectué avec succès!")
        return redirect('order_list')
    
    return render(request, "payments/create.html", {'order': order})


@api_view(['POST'])
@login_required
def payment_create_api(request):
    order_id = request.data.get('order_id')
    payment_method = request.data.get('payment_method')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    payment = Payment.objects.create(
        order=order,
        amount=order.total_amount,
        payment_method=payment_method,
        status='pending'
    )
    
    payment.status = 'succeeded'
    payment.save()
    
    order.status = 'paid'
    order.save()
    
    return Response({
        'id': payment.id,
        'status': payment.status,
        'message': 'Payment processed successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@login_required
def payment_detail_api(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    
    data = {
        'id': payment.id,
        'order_id': payment.order.id,
        'amount': str(payment.amount),
        'payment_method': payment.payment_method,
        'status': payment.status,
        'transaction_id': payment.transaction_id,
        'created_at': payment.created_at
    }
    
    return Response(data)