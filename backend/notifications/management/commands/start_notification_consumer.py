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
                print(f"[Notification Consumer] Connecting to RabbitMQ at {RABBITMQ_HOST}... (Attempt {attempt + 1}/{max_retries})")
                
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=RABBITMQ_HOST)
                )
                channel = connection.channel()
                
                channel.queue_declare(queue='notifications', durable=True)
                
                print("[Notification Consumer] ✓ Connected to RabbitMQ")
                print("[Notification Consumer] Waiting for notification events...")

                def callback(ch, method, properties, body):
                    try:
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
                                message=f"Votre commande #{order_id} a été payée avec succès. Montant: {amount}€",
                                notification_type='payment'
                            )
                            
                            print(f"[Notification Consumer] ✅ Notification saved for Order #{order_id} (User: {user.username})")
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            
                        except Order.DoesNotExist:
                            print(f"[Notification Consumer] ❌ Order #{order_id} not found!")
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            
                    except json.JSONDecodeError as e:
                        print(f"[Notification Consumer] ❌ Invalid JSON: {e}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except Exception as e:
                        print(f"[Notification Consumer] ❌ Error processing notification: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
                channel.basic_consume(
                    queue='notifications',
                    on_message_callback=callback,
                    auto_ack=False
                )
                
                channel.start_consuming()
                
            except pika.exceptions.AMQPConnectionError as e:
                print(f"[Notification Consumer] ❌ Connection failed: {e}")
                if attempt < max_retries - 1:
                    print(f"[Notification Consumer] Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"[Notification Consumer] ❌ Max retries reached. Exiting.")
                    raise
                    
            except KeyboardInterrupt:
                print("[Notification Consumer] Shutting down...")
                break
                
            except Exception as e:
                print(f"[Notification Consumer] ❌ Unexpected error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
