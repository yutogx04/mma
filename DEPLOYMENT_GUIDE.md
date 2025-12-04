# Multi-Server Deployment Guide (Without Docker)

## Overview
This guide explains how to deploy the MMA project across multiple physical machines/servers.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Machine 1     │     │   Machine 2     │
│   (Frontend)    │────▶│   (Traefik)     │
│   User Browser  │     │   Reverse Proxy │
└─────────────────┘     └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Machine 3   │     │   Machine 4   │     │   Machine 5   │
│   Django API  │────▶│   RabbitMQ    │◀────│   Worker      │
│   Port 8000   │     │   Port 5672   │     │   (Consumer)  │
└───────┬───────┘     └───────────────┘     └───────────────┘
        │
        ▼
┌───────────────┐
│   Machine 6   │
│   Consul      │
│   Port 8500   │
└───────────────┘
```

---

## Machine Requirements

| Machine | Role | Software | Port |
|---------|------|----------|------|
| Machine 1 | User | Web Browser | - |
| Machine 2 | Traefik | Traefik binary | 80, 8080 |
| Machine 3 | Django API | Python 3.13, Django | 8000 |
| Machine 4 | RabbitMQ | RabbitMQ Server | 5672, 15672 |
| Machine 5 | Worker | Python 3.13, Django | - |
| Machine 6 | Consul | Consul binary | 8500 |

---

## Step 1: Configure IP Addresses

Edit `backend/config.py` with your machine IPs:

```python
# Example IPs - Replace with YOUR actual machine IPs
DJANGO_HOST = "192.168.1.10"
DJANGO_PORT = 8000
RABBITMQ_HOST = "192.168.1.11"
RABBITMQ_PORT = 5672
CONSUL_HOST = "192.168.1.12"
CONSUL_PORT = 8500
TRAEFIK_HOST = "192.168.1.13"
```

---

## Step 2: Setup Each Machine

### Machine 3 - Django API Server

```bash
# 1. Copy project to this machine
# 2. Install Python 3.13
# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Configure environment
# Edit .env file with correct IPs

# 5. Run Django
python manage.py runserver 0.0.0.0:8000
```

### Machine 4 - RabbitMQ Server

```bash
# Windows: Download from https://www.rabbitmq.com/download.html
# Install Erlang first, then RabbitMQ

# Start RabbitMQ
rabbitmq-server

# Enable management UI (optional)
rabbitmq-plugins enable rabbitmq_management
# Access at http://192.168.1.11:15672 (guest/guest)
```

### Machine 5 - Worker (Payment Consumer)

```bash
# 1. Copy project to this machine
# 2. Install Python and dependencies
pip install -r requirements.txt

# 3. Run the consumer
python manage.py start_consumer
```

### Machine 6 - Consul Server

```bash
# Download from https://www.consul.io/downloads
# Extract consul.exe

# Start Consul
consul agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=192.168.1.12

# Access UI at http://192.168.1.12:8500
```

### Machine 2 - Traefik Reverse Proxy

```bash
# Download from https://github.com/traefik/traefik/releases
# Extract traefik.exe

# Copy traefik.yml and dynamic.yml to same folder
# Edit dynamic.yml with Django IP

# Start Traefik
traefik --configFile=traefik.yml

# Dashboard at http://192.168.1.13:8080
```

---

## Step 3: Network Configuration

1. All machines must be on the **same network** (or have routes)
2. Open required ports in **Windows Firewall**:
   ```powershell
   # On Django machine
   netsh advfirewall firewall add rule name="Django" dir=in action=allow protocol=TCP localport=8000
   
   # On RabbitMQ machine
   netsh advfirewall firewall add rule name="RabbitMQ" dir=in action=allow protocol=TCP localport=5672
   
   # On Consul machine
   netsh advfirewall firewall add rule name="Consul" dir=in action=allow protocol=TCP localport=8500
   ```

---

## Step 4: Start Order (Important!)

1. **First**: Start Consul (Machine 6)
2. **Second**: Start RabbitMQ (Machine 4)
3. **Third**: Start Django (Machine 3)
4. **Fourth**: Start Worker (Machine 5)
5. **Last**: Start Traefik (Machine 2)

---

## Step 5: Verify Deployment

```bash
# Check health (from any machine)
curl http://192.168.1.10:8000/health/
# Should return: {"status": "ok"}

# Check Consul UI
# Open: http://192.168.1.12:8500

# Check RabbitMQ UI
# Open: http://192.168.1.11:15672

# Check Traefik Dashboard
# Open: http://192.168.1.13:8080
```

---

## Using Phones as Servers

Yes, you can use phones running **Termux** (Android):

```bash
# On Android phone with Termux
pkg install python
pip install django djangorestframework pika

# Run Django
cd backend
python manage.py runserver 0.0.0.0:8000
```

Get phone IP: Settings → WiFi → Your network → IP address
