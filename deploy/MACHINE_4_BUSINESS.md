# Machine 4: Business Logic + RabbitMQ

**Owner:** TBD  
**IP:** 10.237.235.___  
**Role:** Core Business Services + Message Queue

---

## What This Machine Does

Runs the main business logic:
- Products, Orders, Payments
- Reviews, Invoices, Notifications
- RabbitMQ message broker
- Payment & Notification workers

---

## Services (6 Django + 2 Workers)

| Service | Port | Routes |
|---------|------|--------|
| products-service | 8000 | /api/products, /api/categories |
| orders-service | 8001 | /api/orders, /api/cart |
| payments-service | 8002 | /api/payments |
| reviews-service | 8003 | /api/reviews |
| invoices-service | 8004 | /api/invoices |
| notifications-service | 8005 | /api/notifications |
| Payment Worker | - | Processes payment queue |
| Notification Worker | - | Sends notifications |

---

## Install

1. **Consul:** https://developer.hashicorp.com/consul/downloads → `C:\consul`
2. **Python 3.10+:** https://python.org
3. **Project Code:** Copy/clone mma folder
4. **Dependencies:** `pip install -r requirements.txt`
5. **RabbitMQ:** See below

### Installing RabbitMQ

**Windows:**
1. Install Erlang: https://www.erlang.org/downloads
2. Install RabbitMQ: https://www.rabbitmq.com/download.html
3. It starts automatically as a Windows service
4. Enable management UI:
   ```powershell
   cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-X.X.X\sbin"
   .\rabbitmq-plugins.bat enable rabbitmq_management
   ```
5. Access: http://localhost:15672 (guest/guest)

**Linux:**
```bash
sudo apt install rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
```

---

## .env File

Create `.env` in the backend folder:

```env
SECRET_KEY=c$2$+z)@az8*tgtu%-8_^ctn5co)!3r5=+ar2j2p(oe^hdg7h4

DEBUG=True
DB_ENGINE=sqlite

# THIS machine's IP - CHANGE THIS!
DJANGO_HOST=10.237.235.___
DJANGO_PORT=8000

# Consul Leader (Machine 1)
CONSUL_HOST=10.237.235.168
CONSUL_PORT=8500

# RabbitMQ is on THIS machine
RABBITMQ_HOST=localhost

SERVICE_NAME=products-service
AUTO_REGISTER_CONSUL=true
```

---

## Run (9 Terminals!)

### Terminal 1 - Consul Agent
```powershell
cd C:\consul
.\consul.exe agent -bind=YOUR_IP -retry-join=10.237.235.168 -data-dir=data
```

### Terminal 2 - Products Service
```powershell
cd path\to\mma\backend
$env:SERVICE_NAME="products-service"
$env:DJANGO_PORT="8000"
python manage.py runserver 0.0.0.0:8000
```

### Terminal 3 - Orders Service
```powershell
$env:SERVICE_NAME="orders-service"
$env:DJANGO_PORT="8001"
python manage.py runserver 0.0.0.0:8001
```

### Terminal 4 - Payments Service
```powershell
$env:SERVICE_NAME="payments-service"
$env:DJANGO_PORT="8002"
python manage.py runserver 0.0.0.0:8002
```

### Terminal 5 - Reviews Service
```powershell
$env:SERVICE_NAME="reviews-service"
$env:DJANGO_PORT="8003"
python manage.py runserver 0.0.0.0:8003
```

### Terminal 6 - Invoices Service
```powershell
$env:SERVICE_NAME="invoices-service"
$env:DJANGO_PORT="8004"
python manage.py runserver 0.0.0.0:8004
```

### Terminal 7 - Notifications Service
```powershell
$env:SERVICE_NAME="notifications-service"
$env:DJANGO_PORT="8005"
python manage.py runserver 0.0.0.0:8005
```

### Terminal 8 - Payment Worker
```powershell
cd path\to\mma\backend
python manage.py start_consumer
```

### Terminal 9 - Notification Worker
```powershell
cd path\to\mma\backend
python manage.py start_notification_consumer
```

---

## Verify

1. **Consul UI:** Shows 6 new services (all green)
2. **RabbitMQ:** http://localhost:15672 accessible
3. **Workers:** Terminals 8-9 show "En attente de messages..."

---

## Troubleshooting

**RabbitMQ connection failed?**
- Check RabbitMQ service is running
- Try `rabbitmqctl status` in admin terminal

**Service port conflict?**
- Make sure each service uses different DJANGO_PORT
- Check no other app is using ports 8000-8005
