import pika
import requests
import json
from config import RABBITMQ_HOST, DJANGO_HOST, DJANGO_PORT


def process_payment(ch, method, properties, body):
    payment_data = json.loads(body.decode())
    print(f"Paiement reçu: {payment_data}")
    
    order_id = payment_data.get('order_id')
    amount = payment_data.get('amount')
    
    try:
        res = requests.post(
            f"http://{DJANGO_HOST}:{DJANGO_PORT}/api/payments/",
            json=payment_data
        )
        if res.status_code in [200, 201]:
            print(f"Commande #{order_id} - Montant: {amount}")
            print("Paiement validé!")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print(f"Erreur API: {res.status_code}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    except Exception as e:
        print(f"Erreur: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


print(f"Connexion à RabbitMQ: {RABBITMQ_HOST}")
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
