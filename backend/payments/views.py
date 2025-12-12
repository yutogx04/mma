from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from orders.models import Order


import pika
import json
from config import RABBITMQ_HOST

def publish_payment_event(order_id, amount):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue='payment', durable=True)
    channel.queue_declare(queue='notifications', durable=True)
    
    message = json.dumps({'order_id': order_id, 'amount': str(amount)})
    
    # Publish to Payment Worker
    channel.basic_publish(
        exchange='',
        routing_key='payment',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2))
        
    # Publish to Notification Worker
    channel.basic_publish(
        exchange='',
        routing_key='notifications',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2))
    connection.close()

@login_required
def payment_create_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == "POST":
        # Get users default payment method
        default_method = request.user.payment_methods.filter(is_default=True).first()
        
        if not default_method:
             messages.error(request, "Aucun moyen de paiement enregistré.")
             return redirect('dashboard')
        
        # Validate card information
        card_last_four = request.POST.get('card_last_four')
        cvv = request.POST.get('cvv')
        
        if card_last_four != default_method.card_last_four:
            messages.error(request, "Les 4 derniers chiffres de la carte ne correspondent pas.")
            return redirect('payment_create', order_id=order.id)
        
        if not cvv or len(cvv) != 3:
            messages.error(request, "CVV invalide.")
            return redirect('payment_create', order_id=order.id)
        
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            payment_method='credit_card', # stored type
            payment_method_used=default_method, # Link to method
            status='pending'
        )
        

        # Async processing via RabbitMQ
        try:
            publish_payment_event(order.id, order.total_amount)
            messages.info(request, f"⏳ Paiement de ${order.total_amount} initié avec la carte finissant par {default_method.card_last_four}...")
        except Exception:
            payment.status = 'failed'
            payment.save()
            messages.error(request, "Erreur de connexion au service de paiement.")
            return redirect('order_list')
        
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
    
    try:
        publish_payment_event(order.id, order.total_amount)
        return Response({
            'id': payment.id,
            'status': 'pending',
            'message': 'Payment processing started'
        }, status=status.HTTP_202_ACCEPTED)

    except Exception:
        payment.status = 'failed'
        payment.save()
        return Response({
            'status': 'failed',
            'message': 'Payment processing failed'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


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