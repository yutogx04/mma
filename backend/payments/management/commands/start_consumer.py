
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
                self._connect_and_consume(attempt, max_retries, retry_delay)
                break
                
            except pika.exceptions.AMQPConnectionError as e:
                self._handle_connection_error(e, attempt, max_retries, retry_delay)
                    
            except KeyboardInterrupt:
                print("[Payment Consumer] Arrêt...")
                break
                
            except Exception as e:
                self._handle_unexpected_error(e, attempt, max_retries, retry_delay)

    def _connect_and_consume(self, attempt, max_retries, retry_delay):
        """Establish connection and start consuming payment messages"""
        print("[Payment Consumer] Connexion à RabbitMQ: {}... (Tentative {}/{})".format(
            RABBITMQ_HOST, attempt + 1, max_retries))
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(RABBITMQ_HOST)
        )
        channel = connection.channel()
        channel.queue_declare(queue='payment', durable=True)
        
        print("[Payment Consumer] Connecté à RabbitMQ")
        print("[Payment Consumer] En attente de messages...")
        
        channel.basic_consume(
            queue='payment',
            on_message_callback=self._process_payment,
            auto_ack=False
        )
        
        channel.start_consuming()

    def _process_payment(self, ch, method, properties, body):
        """Process incoming payment messages"""
        print("[Payment Consumer] Paiement reçu: {}".format(body.decode()))
        try:
            payment_data = json.loads(body.decode())
            order_id = payment_data.get('order_id')
            
            self._handle_payment_order(order_id, ch, method)
            
        except json.JSONDecodeError as e:
            print("[Payment Consumer] JSON invalide: {}".format(e))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print("[Payment Consumer]  Erreur: {}".format(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _handle_payment_order(self, order_id, ch, method):
        """Handle payment processing for a specific order"""
        from orders.models import Order
        from payments.models import Payment
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            print("[Payment Consumer] Commande #{} introuvable".format(order_id))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        payment = Payment.objects.filter(order=order, status='pending').last()
        
        if not payment:
            print("[Payment Consumer]  Pas de paiement en attente trouvé pour la commande #{}".format(order_id))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        self._process_successful_payment(order, payment, ch, method)

    def _process_successful_payment(self, order, payment, ch, method):
        """Process successful payment and update order status"""
        print("[Payment Consumer] Traitement de la commande #{}...".format(order.id))
        
        order.status = 'paid'
        order.save()
        
        payment.status = 'succeeded'
        payment.save()
        
        self._update_stock_quantities(order)
        
        print("[Payment Consumer] Paiement validé et stocks mis à jour pour commande #{}".format(order.id))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _update_stock_quantities(self, order):
        """Update stock quantities for order items"""
        for item in order.orderitem_set.all():
            if item.product.stock_quantity >= item.quantity:
                item.product.stock_quantity -= item.quantity
                item.product.save()

    def _handle_connection_error(self, error, attempt, max_retries, retry_delay):
        """Handle RabbitMQ connection errors"""
        print("[Payment Consumer] Échec de connexion: {}".format(error))
        if attempt < max_retries - 1:
            print("[Payment Consumer] Nouvelle tentative dans {} secondes...".format(retry_delay))
            time.sleep(retry_delay)
        else:
            print("[Payment Consumer]  Nombre maximum de tentatives atteint. Arrêt.")
            raise

    def _handle_unexpected_error(self, error, attempt, max_retries, retry_delay):
        """Handle unexpected errors"""
        print("[Payment Consumer] Erreur inattendue: {}".format(error))
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
        else:
            raise

