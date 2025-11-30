from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import Payment
from orders.models import Order
from django.shortcuts import redirect

@login_required
def payment_create_view(request, order_id):
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        
        token = request.session.get('access_token')
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        response = requests.post(
            "http://127.0.0.1:8000/api/payments/create/",
            data={
                "order_id": order_id,
                "payment_method": payment_method
            },
            headers=headers
        )
        
        if response.status_code == 201:
            return redirect('order_list')
        else:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            return render(request, "payments/create.html", {
                'order': order,
                'error': 'Payment failed'
            })
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "payments/create.html", {
        'order': order
    })

# API Views
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
    
    # Simulate payment processing
    payment.status = 'succeeded'
    payment.save()
    
    # Update order status
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