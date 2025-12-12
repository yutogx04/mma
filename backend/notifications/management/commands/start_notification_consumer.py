
from django.core.management.base import BaseCommand
import pika
import json
import time
from config import RABBITMQ_HOST

class Command(BaseCommand):
    help = 'Starts the notification consumer to listen for payment events'

    def handle(self, *args, **kwargs):
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self._connect_and_consume(attempt, max_retries, retry_delay)
                break
                
            except pika.exceptions.AMQPConnectionError as e:
                self._handle_connection_error(e, attempt, max_retries, retry_delay)
                    
            except KeyboardInterrupt:
                print("[Notification Consumer] Shutting down...")
                break
                
            except Exception as e:
                self._handle_unexpected_error(e, attempt, max_retries, retry_delay)

    def _connect_and_consume(self, attempt, max_retries, retry_delay):
        """Establish connection and start consuming messages"""
        print("[Notification Consumer] Connecting to RabbitMQ at {}... (Attempt {}/{})".format(
            RABBITMQ_HOST, attempt + 1, max_retries))
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        channel = connection.channel()
        
        channel.queue_declare(queue='notifications', durable=True)
        
        print("[Notification Consumer] ✓ Connected to RabbitMQ")
        print("[Notification Consumer] Waiting for notification events...")

        channel.basic_consume(
            queue='notifications',
            on_message_callback=self._callback,
            auto_ack=False
        )
        
        channel.start_consuming()

    def _callback(self, ch, method, properties, body):
        """Process incoming notification messages"""
        try:
            self._process_notification_message(ch, method, body)
            
        except json.JSONDecodeError as e:
            print("[Notification Consumer]  Invalid JSON: {}".format(e))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print("[Notification Consumer]  Error processing notification: {}".format(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _process_notification_message(self, ch, method, body):
        """Process individual notification message"""
        data = json.loads(body.decode())
        order_id = data.get('order_id')
        amount = data.get('amount')
        
        from orders.models import Order
        from notifications.models import Notification
        
        try:
            order = Order.objects.get(id=order_id)
            user = order.user
            
            Notification.objects.create(
                user=user,
                title="Paiement Confirmé",
                message="Votre commande #{} a été payée avec succès. Montant: {}€".format(order_id, amount),
                notification_type='payment'
            )
            
            print("[Notification Consumer]  Notification saved for Order #{} (User: {})".format(
                order_id, user.username))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Order.DoesNotExist:
            print("[Notification Consumer]  Order #{} not found!".format(order_id))
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def _handle_connection_error(self, error, attempt, max_retries, retry_delay):
        """Handle RabbitMQ connection errors"""
        print("[Notification Consumer]  Connection failed: {}".format(error))
        if attempt < max_retries - 1:
            print("[Notification Consumer] Retrying in {} seconds...".format(retry_delay))
            time.sleep(retry_delay)
        else:
            print("[Notification Consumer]  Max retries reached. Exiting.")
            raise

    def _handle_unexpected_error(self, error, attempt, max_retries, retry_delay):
        """Handle unexpected errors"""
        print("[Notification Consumer]  Unexpected error: {}".format(error))
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
        else:
            raise
