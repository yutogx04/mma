from django.core.management.base import BaseCommand
import pika
import json
import time
from config import RABBITMQ_HOST


class Command(BaseCommand):
    help = 'Lance le consommateur RabbitMQ'
    
    def handle(self, *args, **kwargs):
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print(f"[Payment Consumer] Connexion à RabbitMQ: {RABBITMQ_HOST}... (Tentative {attempt + 1}/{max_retries})")
                
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(RABBITMQ_HOST)
                )
                channel = connection.channel()
                channel.queue_declare(queue='payment', durable=True)
                
                print("[Payment Consumer] ✓ Connecté à RabbitMQ")
                print("[Payment Consumer] En attente de messages...")
                
                def process(ch, method, properties, body):
                    print(f"[Payment Consumer] Paiement reçu: {body.decode()}")
                    try:
                        payment_data = json.loads(body.decode())
                        order_id = payment_data.get('order_id')
                        
                        from orders.models import Order
                        from payments.models import Payment
                        
                        order = Order.objects.get(id=order_id)
                        payment = Payment.objects.filter(order=order, status='pending').last()
                        
                        if not payment:
                            print(f"[Payment Consumer] ⚠️  Pas de paiement en attente trouvé pour la commande #{order_id}")
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            return

                        print(f"[Payment Consumer] Traitement de la commande #{order_id}...")
                        
                        order.status = 'paid'
                        order.save()
                        
                        payment.status = 'succeeded'
                        payment.save()
                        
                        for item in order.orderitem_set.all():
                            if item.product.stock_quantity >= item.quantity:
                                item.product.stock_quantity -= item.quantity
                                item.product.save()
                        
                        print(f"[Payment Consumer] ✅ Paiement validé et stocks mis à jour pour commande #{order_id}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except Order.DoesNotExist:
                        print(f"[Payment Consumer] ❌ Commande #{order_id} introuvable")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except json.JSONDecodeError as e:
                        print(f"[Payment Consumer] ❌ JSON invalide: {e}")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except Exception as e:
                        print(f"[Payment Consumer] ❌ Erreur: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
                channel.basic_consume(
                    queue='payment',
                    on_message_callback=process,
                    auto_ack=False
                )
                
                channel.start_consuming()
                
            except pika.exceptions.AMQPConnectionError as e:
                print(f"[Payment Consumer] ❌ Échec de connexion: {e}")
                if attempt < max_retries - 1:
                    print(f"[Payment Consumer] Nouvelle tentative dans {retry_delay} secondes...")
                    time.sleep(retry_delay)
                else:
                    print(f"[Payment Consumer] ❌ Nombre maximum de tentatives atteint. Arrêt.")
                    raise
                    
            except KeyboardInterrupt:
                print("[Payment Consumer] Arrêt...")
                break
                
            except Exception as e:
                print(f"[Payment Consumer] ❌ Erreur inattendue: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

