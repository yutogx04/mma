# 5-Machine Distributed Deployment - Complete Guide

> All services, workers, and infrastructure setup

---

## Complete Service List

### Django Services (10 total)
| Service | Routes | Machine |
|---------|--------|---------|
| users-service | `/api/users`, `/api/auth` | 3 (Auth) |
| token-service | `/api/token` | 3 (Auth) |
| token-refresh-service | `/api/token/refresh` | 3 (Auth) |
| products-service | `/api/products`, `/api/categories` | 4 (Business) |
| orders-service | `/api/orders`, `/api/cart` | 4 (Business) |
| payments-service | `/api/payments`, `/api/payment-methods` | 4 (Business) |
| reviews-service | `/api/reviews` | 4 (Business) |
| invoices-service | `/api/invoices` | 4 (Business) |
| notifications-service | `/api/notifications` | 4 (Business) |
| shop-service | `/`, `/admin`, `/dashboard`, `/vendor`, `/static` | 5 (UI) |

### RabbitMQ Workers (2 total)
| Worker | Command | Purpose |
|--------|---------|---------|
| Payment Worker | `python manage.py start_consumer` | Processes payments |
| Notification Worker | `python manage.py start_notification_consumer` | Sends notifications |

---

## Quick Reference

| Machine | Role | Needs .env? | Needs Code? | What to Install |
|---------|------|-------------|-------------|-----------------|
| 1 | Consul Leader | ❌ No | ❌ No | Consul only |
| 2 | Traefik | ❌ No | ❌ No | Consul + Traefik |
| 3 | Auth | ✅ Yes | ✅ Yes | Consul + Python |
| 4 | Business + RabbitMQ | ✅ Yes | ✅ Yes | Consul + Python + RabbitMQ |
| 5 | UI | ✅ Yes | ✅ Yes | Consul + Python |

---

## Network IPs

| Machine | Role | IP |
|---------|------|----|
| 1 | Consul Leader | 10.237.235.168 |
| 2 | Traefik | 10.237.235.___ |
| 3 | Auth | 10.237.235.7 |
| 4 | Business + RabbitMQ | 10.237.235.___ |
| 5 | UI | 10.237.235.___ |

---

## Machine 1: Consul Server (Leader)

**IP: 10.237.235.168**

### Install
Download Consul: https://developer.hashicorp.com/consul/downloads
Extract to `C:\consul`

### No .env needed!

### Run
```powershell
cd C:\consul
.\consul.exe agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=10.237.235.168 -data-dir=data
```

**Linux:**
```bash
consul agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=10.237.235.168 -data-dir=./data
```

✅ Check: http://10.237.235.168:8500

---

## Machine 2: Traefik + Consul Agent

### Install
- Consul → `C:\consul`
- Traefik: https://github.com/traefik/traefik/releases → `C:\traefik`

### No .env needed!

### Run (2 terminals)

**Terminal 1 - Consul Agent:**
```powershell
cd C:\consul
.\consul.exe agent -bind=YOUR_IP -retry-join=10.237.235.168 -data-dir=data
```

**Terminal 2 - Traefik:**
```powershell
cd C:\traefik
.\traefik.exe --api.insecure=true --entrypoints.web.address=:80 --providers.consulCatalog.endpoint.address=10.237.235.168:8500 --providers.consulCatalog.exposedByDefault=false --providers.consulCatalog.prefix=traefik
```

✅ Check: http://YOUR_IP:8080

---

## Machine 3: Auth Service (10.237.235.7)

**Runs:** users-service (which auto-registers token-service and token-refresh-service)

### Install
1. Consul → `C:\consul`
2. Python 3.10+
3. Copy mma folder → `G:\mma`
4. `cd G:\mma\mma\backend && pip install -r requirements.txt`

### .env file (`G:\mma\mma\backend\.env`)
```env
SECRET_KEY=c$2$+z)@az8*tgtu%-8_^ctn5co)!3r5=+ar2j2p(oe^hdg7h4

DEBUG=True
DB_ENGINE=sqlite

DJANGO_HOST=10.237.235.7
DJANGO_PORT=8000

CONSUL_HOST=10.237.235.168
CONSUL_PORT=8500

RABBITMQ_HOST=10.237.235.X  # Machine 4's IP

SERVICE_NAME=users-service
AUTO_REGISTER_CONSUL=true
```

### Run (2 terminals)

**Terminal 1 - Consul Agent:**
```powershell
cd C:\consul
.\consul.exe agent -bind=10.237.235.7 -retry-join=10.237.235.168 -data-dir=data
```

**Terminal 2 - Users Service:**
```powershell
cd G:\mma\mma\backend
python manage.py runserver 0.0.0.0:8000
```

✅ Check: Consul UI shows 3 services (users, token, token-refresh)

---

## Machine 4: Business Logic + RabbitMQ

**Runs:** 6 Django services + 2 RabbitMQ workers

### Install
1. Consul → `C:\consul`
2. Python 3.10+
3. Copy mma folder
4. `pip install -r requirements.txt`
5. **RabbitMQ** (see below)

### Installing RabbitMQ

**Windows:**
1. Install Erlang: https://www.erlang.org/downloads
2. Install RabbitMQ: https://www.rabbitmq.com/download.html
3. Start RabbitMQ service (automatically starts)
4. Enable management: `rabbitmq-plugins enable rabbitmq_management`
5. Access: http://localhost:15672 (guest/guest)

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
```

### .env file
```env
SECRET_KEY=c$2$+z)@az8*tgtu%-8_^ctn5co)!3r5=+ar2j2p(oe^hdg7h4

DEBUG=True
DB_ENGINE=sqlite

DJANGO_HOST=10.237.235.X  # THIS machine's IP
DJANGO_PORT=8000

CONSUL_HOST=10.237.235.168
CONSUL_PORT=8500

RABBITMQ_HOST=localhost  # RabbitMQ is on THIS machine

SERVICE_NAME=products-service
AUTO_REGISTER_CONSUL=true
```

### Run (9 terminals!)

**Terminal 1 - Consul Agent:**
```powershell
cd C:\consul
.\consul.exe agent -bind=YOUR_IP -retry-join=10.237.235.168 -data-dir=data
```

**Terminals 2-7 - Django Services:**

For each, run in `G:\mma\mma\backend`:

| Terminal | Commands |
|----------|----------|
| 2 | `$env:SERVICE_NAME="products-service"; $env:DJANGO_PORT="8000"; python manage.py runserver 0.0.0.0:8000` |
| 3 | `$env:SERVICE_NAME="orders-service"; $env:DJANGO_PORT="8001"; python manage.py runserver 0.0.0.0:8001` |
| 4 | `$env:SERVICE_NAME="payments-service"; $env:DJANGO_PORT="8002"; python manage.py runserver 0.0.0.0:8002` |
| 5 | `$env:SERVICE_NAME="reviews-service"; $env:DJANGO_PORT="8003"; python manage.py runserver 0.0.0.0:8003` |
| 6 | `$env:SERVICE_NAME="invoices-service"; $env:DJANGO_PORT="8004"; python manage.py runserver 0.0.0.0:8004` |
| 7 | `$env:SERVICE_NAME="notifications-service"; $env:DJANGO_PORT="8005"; python manage.py runserver 0.0.0.0:8005` |

**Terminal 8 - Payment Worker:**
```powershell
cd G:\mma\mma\backend
python manage.py start_consumer
```

**Terminal 9 - Notification Worker:**
```powershell
cd G:\mma\mma\backend
python manage.py start_notification_consumer
```

✅ Check: Consul UI shows 6 services + RabbitMQ at http://localhost:15672

---

## Machine 5: UI Service (Shop)

**Runs:** shop-service (handles /, /admin, /dashboard, /vendor, /static)

### Install
1. Consul → `C:\consul`
2. Python 3.10+
3. Copy mma folder
4. `pip install -r requirements.txt`

### .env file
```env
SECRET_KEY=c$2$+z)@az8*tgtu%-8_^ctn5co)!3r5=+ar2j2p(oe^hdg7h4

DEBUG=True
DB_ENGINE=sqlite

DJANGO_HOST=10.237.235.X  # THIS machine's IP
DJANGO_PORT=8000

CONSUL_HOST=10.237.235.168
CONSUL_PORT=8500

RABBITMQ_HOST=10.237.235.Y  # Machine 4's IP

SERVICE_NAME=shop-service
AUTO_REGISTER_CONSUL=true
```

### Run (2 terminals)

**Terminal 1 - Consul Agent:**
```powershell
cd C:\consul
.\consul.exe agent -bind=YOUR_IP -retry-join=10.237.235.168 -data-dir=data
```

**Terminal 2 - Shop Service:**
```powershell
cd path\to\mma\backend
python manage.py runserver 0.0.0.0:8000
```

✅ Check: Consul UI shows shop-service

---

## Verification Checklist

| Step | Check |
|------|-------|
| 1 | Consul UI (http://10.237.235.168:8500) shows 5 nodes |
| 2 | Consul UI shows 10 services (all green) |
| 3 | Traefik (http://MACHINE_2:8080) shows all routers |
| 4 | RabbitMQ (http://MACHINE_4:15672) is accessible |
| 5 | App (http://MACHINE_2) loads homepage |

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required) |
| `DEBUG` | Debug mode | True |
| `DB_ENGINE` | Database type | sqlite |
| `DJANGO_HOST` | This machine's IP | 127.0.0.1 |
| `DJANGO_PORT` | Service port | 8000 |
| `CONSUL_HOST` | Consul leader IP | localhost |
| `CONSUL_PORT` | Consul port | 8500 |
| `RABBITMQ_HOST` | RabbitMQ machine IP | localhost |
| `SERVICE_NAME` | Service to register | django-service |
| `AUTO_REGISTER_CONSUL` | Enable registration | false |

---

## Troubleshooting

**Service not registering?**
- `DJANGO_HOST` must be YOUR IP, not `127.0.0.1`
- `CONSUL_HOST` must be `10.237.235.168`
- `AUTO_REGISTER_CONSUL=true` (no quotes!)

**Consul agent can't join?**
- Check Machine 1 is running first
- Firewall: allow ports 8301, 8500

**RabbitMQ connection failed?**
- Check RabbitMQ service is running
- `RABBITMQ_HOST` points to correct IP

**Payment not processing?**
- Check `start_consumer` terminal for errors
- Verify RabbitMQ has `payment` queue
