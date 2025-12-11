import pika
import json
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from payments.models import Payment
from orders.models import Order
from config import RABBITMQ_HOST


def process_payment(ch, method, properties, body):
    payment_data = json.loads(body.decode())
    print(f"Paiement recu: {payment_data}")
    
    order_id = payment_data.get('order_id')
    amount = payment_data.get('amount')
    
    try:
        # Find the pending payment for this order
        payment = Payment.objects.filter(order_id=order_id, status='pending').first()
        
        if payment:
            # Mark payment as completed
            payment.status = 'completed'
            payment.transaction_id = f"TXN-{order_id}-{payment.id}"
            payment.save()
            
            # Update order status to paid
            order = payment.order
            order.status = 'paid'
            order.save()
            
            print(f"Commande #{order_id} - Montant: {amount}")
            print(f"Paiement valide! Transaction: {payment.transaction_id}")
        else:
            print(f"Aucun paiement en attente pour la commande #{order_id}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Erreur: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


print(f"Connexion a RabbitMQ: {RABBITMQ_HOST}")
with pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST)) as con:
    ch = con.channel()
    ch.queue_declare(queue="payment", durable=True)
    ch.basic_consume(
        queue="payment",
        on_message_callback=process_payment,
        auto_ack=False
    )
    print("En attente de messages...")
    ch.start_consuming()
