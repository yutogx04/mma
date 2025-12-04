"""
Django management command to start the RabbitMQ consumer
(Course pattern - payment_service/management/commands/start_consumer.py)

Uses config.py for RabbitMQ IP in multi-server deployment.
Usage: python manage.py start_consumer
"""
from django.core.management.base import BaseCommand
import pika
import json
from config import RABBITMQ_HOST


class Command(BaseCommand):
    help = 'Lance le consommateur RabbitMQ'
    
    def handle(self, *args, **kwargs):
        print(f"Connexion à RabbitMQ: {RABBITMQ_HOST}")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(RABBITMQ_HOST)
        )
        channel = connection.channel()
        channel.queue_declare(queue='payment', durable=True)
        
        def process(ch, method, properties, body):
            print("Paiement reçu:", body.decode())
            try:
                payment_data = json.loads(body.decode())
                order_id = payment_data.get('order_id')
                amount = payment_data.get('amount')
                
                print(f"Commande #{order_id} - Montant: {amount}")
                print("Traitement du paiement en cours...")
                print("Paiement validé!")
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Erreur: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        channel.basic_consume(
            queue='payment',
            on_message_callback=process,
            auto_ack=False
        )
        
        print("En attente de messages...")
        channel.start_consuming()
