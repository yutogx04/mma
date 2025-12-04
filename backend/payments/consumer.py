"""
RabbitMQ Consumer for Payment Processing
(Course pattern - Microservice Consommateur)

Uses config.py for RabbitMQ IP in multi-server deployment.
Run with: python manage.py start_consumer
"""
import pika
import requests
import json
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RABBITMQ_HOST, DJANGO_HOST, DJANGO_PORT


def process_payment(ch, method, properties, body):
    """
    Callback function to process payment messages
    (Course pattern - payment_Service/Consumer.py)
    """
    print(f"Paiement reçu: {body.decode()}")
    print("Traitement du paiement en cours...")
    
    try:
        payment_data = json.loads(body.decode())
        order_id = payment_data.get('order_id')
        amount = payment_data.get('amount')
        
        # Simulation du traitement
        print(f"Commande #{order_id} - Montant: {amount}")
        print("Paiement validé!")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Erreur de traitement: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consuming():
    """Start the RabbitMQ consumer"""
    print(f"Connexion à RabbitMQ: {RABBITMQ_HOST}")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue='payment', durable=True)
    
    channel.basic_consume(
        queue='payment',
        on_message_callback=process_payment,
        auto_ack=False
    )
    
    print("En attente de messages...")
    channel.start_consuming()


if __name__ == "__main__":
    start_consuming()
