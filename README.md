#  1. Install Required Programs on Your PC

First, make sure these programs are installed:

  --------------------------------------------------------------------------------------------------
  Program           Purpose                Installation
  ----------------- ---------------------- ---------------------------------------------------------
  **Python 3.8+**   Backend logic (Django) Download at python.org

  **Docker          Runs all services in   Download at docker.com
  Desktop**         containers                                    

  **RabbitMQ**      Message broker         Download at https://www.rabbitmq.com/docs/download

  **Traefiek**      Routing Monitor        Download at https://github.com/traefik/traefik/releases

  **Consul**        Service Registry       Download at https://developer.hashicorp.com/consul/install 
                                                                                                    
  ---------------------------------------------------------------------------------------------------

### Verify installation:

``` bash
python --version
docker --version
```

------------------------------------------------------------------------

#  2. Backend Environment Setup (Secrets + Development Settings)

Before running the backend, you must create your own private `.env`
file.

### 1. Enter the backend folder:

``` bash
cd mma/backend
```

### 2. Generate a unique Django SECRET_KEY:

``` bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key.

### 3. Create your `.env` file:

``` bash
# Windows (PowerShell)
cp .env.example .env
notepad .env

# Mac/Linux
cp .env.example .env
nano .env
```

Inside `.env`, paste your secret key:

``` env
SECRET_KEY=your_generated_secret_key_here
DEBUG=True
DB_ENGINE=sqlite  # Default for development
```

> **Note:** `.env` is ignored by Git --- the key stays safe.

------------------------------------------------------------------------

#  .env --- Recommended Development Structure

``` env
# Development settings
DEBUG=True

# Database - Choose ONE
DB_ENGINE=sqlite  # sqlite, mysql, or postgresql

# For MySQL/PostgreSQL only:
# DB_NAME=mma_db
# DB_USER=username
# DB_PASSWORD=password
# DB_HOST=localhost
# DB_PORT=3306

# Service settings (when running without Docker)
SERVICE_NAME=users-service  # Change per service
DJANGO_HOST=127.0.0.1
DJANGO_PORT=8001  # Change per service (8001, 8002, etc.)
CONSUL_HOST=localhost
RABBITMQ_HOST=localhost
```

------------------------------------------------------------------------

#  3. Install Python Dependencies

``` bash
cd backend
pip install -r requirements.txt
```

------------------------------------------------------------------------

#  4. Run Everything with Docker (One Command)

1.  Return to the project root folder:

``` bash
cd ..
```

2.  Launch all services:

``` bash
docker-compose up -d
```

3.  Check running services:

``` bash
docker-compose ps
```

------------------------------------------------------------------------

#  5. Access the Application

  --------------------------------------------------------------------------------
  Service                  URL                      Purpose
  ------------------------ ------------------------ ------------------------------
  **Main Application**     http://localhost         Marketplace frontend

  **Admin Dashboard**      http://localhost/admin   Manage site (requires
                                                    superuser)

  **Consul Dashboard**     http://localhost:8500    Service registry

  **Traefik Dashboard**    http://localhost:8080    API routing monitor

  **RabbitMQ Manager**     http://localhost:15672   Queue monitoring (guest /
                                                    guest)
  --------------------------------------------------------------------------------

### I'd recommend creating an admin user before starting the app:

``` bash
python manage.py createsuperuser
```

# Docker Distributed Deployment Guide (5 Machines)

> **Deploy the application across 5 separate machines using Docker**

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Machine 1  │────▶│  Machine 2  │
│  (Browser)  │     │  (Traefik)  │     │  (Consul)   │
└─────────────┘     │  :80        │     │  :8500      │
                    └─────────────┘     └─────────────┘
                           │                   │
          ┌────────────────┼───────────────────┤
          ▼                ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Machine 3  │     │  Machine 4  │     │  Machine 5  │
│  (RabbitMQ) │     │ (Auth+MySQL)│     │ (Services)  │
│  :5672      │     │  :8000,:3306│     │ :8000-8006  │
└─────────────┘     └─────────────┘     └─────────────┘
```

| Machine | Role | IP |
|---------|------|-----|
| 1 | Traefik (Gateway) | 192.168.1.10 |
| 2 | Consul (Registry) | 192.168.1.11 |
| 3 | RabbitMQ + Workers | 192.168.1.12 |
| 4 | Auth + MySQL | 192.168.1.13 |
| 5 | App Services | 192.168.1.14 |

---

## Prerequisites

1. **Docker & Docker Compose** on all machines
2. **Shared MySQL Database** accessible from all machines
3. **Clone the repo** on Machines 3, 4, 5 (for building the image)

---

## Machine 1: Traefik

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    command:
      - "--api.insecure=true"
      - "--providers.consulcatalog=true"
      - "--providers.consulcatalog.endpoint.address=192.168.1.11:8500"
      - "--providers.consulcatalog.exposedByDefault=false"
      - "--providers.consulcatalog.prefix=traefik"
      - "--entrypoints.web.address=:80"
```

```bash
docker-compose up -d
```

---

## Machine 2: Consul

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  consul:
    image: consul:1.15
    ports:
      - "8500:8500"
    command: agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=192.168.1.11
```

```bash
docker-compose up -d
```

---

## Machine 3: RabbitMQ + Workers

Create `.env`:
```
RABBITMQ_HOST=192.168.1.12
CONSUL_HOST=192.168.1.11
AUTO_REGISTER_CONSUL=true
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"

  payment-worker:
    build: ./backend
    command: python manage.py start_consumer
    env_file: .env
    depends_on:
      - rabbitmq

  notification-worker:
    build: ./backend
    command: python manage.py start_notification_consumer
    env_file: .env
    depends_on:
      - rabbitmq
```

```bash
docker-compose up -d
```

---

## Machine 4: Auth + MySQL

Install MySQL and create database:
```sql
CREATE DATABASE mma_db;
CREATE USER 'mma_admin'@'%' IDENTIFIED BY 'password';
GRANT ALL ON mma_db.* TO 'mma_admin'@'%';
FLUSH PRIVILEGES;
```

Create `.env`:
```
RABBITMQ_HOST=192.168.1.12
CONSUL_HOST=192.168.1.11
DJANGO_HOST=192.168.1.13
AUTO_REGISTER_CONSUL=true
SERVICE_NAME=users-service
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  users-service:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=users-service
      - AUTO_REGISTER_CONSUL=true
```

> **Note**: This automatically registers `token-service` and `token-refresh-service` too!

```bash
docker-compose up -d
```

---

## Machine 5: App Services

Create `.env`:
```
RABBITMQ_HOST=192.168.1.12
CONSUL_HOST=192.168.1.11
DJANGO_HOST=192.168.1.14
AUTO_REGISTER_CONSUL=true
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  products-service:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=products-service
      - AUTO_REGISTER_CONSUL=true

  orders-service:
    build: ./backend
    ports:
      - "8001:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=orders-service
      - AUTO_REGISTER_CONSUL=true

  payments-service:
    build: ./backend
    ports:
      - "8002:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=payments-service
      - AUTO_REGISTER_CONSUL=true

  reviews-service:
    build: ./backend
    ports:
      - "8003:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=reviews-service
      - AUTO_REGISTER_CONSUL=true

  invoices-service:
    build: ./backend
    ports:
      - "8004:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=invoices-service
      - AUTO_REGISTER_CONSUL=true

  notifications-service:
    build: ./backend
    ports:
      - "8005:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=notifications-service
      - AUTO_REGISTER_CONSUL=true

  shop-service:
    build: ./backend
    ports:
      - "8006:8000"
    env_file: .env
    environment:
      - SERVICE_NAME=shop-service
      - AUTO_REGISTER_CONSUL=true
```

```bash
docker-compose up -d
```

---

## Verification

1. **Consul UI**: http://192.168.1.11:8500
   - Should show 10 healthy services

2. **Traefik Dashboard**: http://192.168.1.10:8080
   - Should show all routers

3. **Application**: http://192.168.1.10
   - Access via Traefik gateway

4. **RabbitMQ**: http://192.168.1.12:15672
   - Login: guest/guest

---

## Summary

| Machine | Containers |
|---------|-----------|
| 1 | traefik |
| 2 | consul |
| 3 | rabbitmq, payment-worker, notification-worker |
| 4 | users-service |
| 5 | products, orders, payments, reviews, invoices, notifications, shop |
| **Total** | **13 containers** |

# No Docker Deployment Guide 

> **For running services across 5 machines without Docker**

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Phone     │────▶│  Machine 1  │────▶│  Machine 2  │
│  (Client)   │     │  (Traefik)  │     │  (Consul)   │
└─────────────┘     │  :80        │     │  :8500      │
                    └─────────────┘     └─────────────┘
                           │                   │
          ┌────────────────┼───────────────────┤
          ▼                ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Machine 3  │     │  Machine 4  │     │  Machine 5  │
│  (RabbitMQ) │     │ (Auth+MySQL)│     │ (Services)  │
│  :5672      │     │  :8000,:3306│     │ :8000-8006  │
└─────────────┘     └─────────────┘     └─────────────┘
```

| Machine | Role | IP (Example) |
|---------|------|--------------|
| 1 | Traefik (Reverse Proxy) | 192.168.1.10 |
| 2 | Consul (Service Registry) | 192.168.1.11 |
| 3 | RabbitMQ + Workers | 192.168.1.12 |
| 4 | Auth + MySQL Database | 192.168.1.13 |
| 5 | Application Services | 192.168.1.14 |

---

## Prerequisites

### On ALL Machines
```bash
# Python 3.10+
pip install -r backend/requirements.txt

# Clone repository
git clone <your-repo-url>
cd mma/backend
```

### Firewall Ports (Open These)
| Machine | Ports |
|---------|-------|
| 1 | 80, 8080 |
| 2 | 8500 |
| 3 | 5672, 15672 |
| 4 | 8000, 3306 |
| 5 | 8000-8006 |

### Django Settings
Add to `backend/backend/settings.py`:
```python
ALLOWED_HOSTS = ['*']  # Or list all machine IPs
```

---

## Machine 1: Traefik

### Download
[Traefik Releases](https://github.com/traefik/traefik/releases)

### Config (`traefik.yml`)
```yaml
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"

providers:
  consulCatalog:
    endpoint:
      address: "192.168.1.11:8500"
    exposedByDefault: false
    prefix: traefik

log:
  level: INFO
```

### Run
```bash
.\traefik.exe --configfile=traefik.yml
```

---

## Machine 2: Consul

### Download
[HashiCorp Consul](https://developer.hashicorp.com/consul/downloads)

### Run
```bash
.\consul.exe agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=192.168.1.11 -data-dir=./data
```

---

## Machine 3: RabbitMQ + Workers

### Install RabbitMQ
[RabbitMQ Downloads](https://www.rabbitmq.com/download.html) - Start as service

### Terminal 1: Payment Worker
```powershell
$env:RABBITMQ_HOST="192.168.1.12"
$env:CONSUL_HOST="192.168.1.11"
python manage.py start_consumer
```

### Terminal 2: Notification Worker
```powershell
$env:RABBITMQ_HOST="192.168.1.12"
$env:CONSUL_HOST="192.168.1.11"
python manage.py start_notification_consumer
```

---

## Machine 4: Auth + MySQL

### MySQL Setup
1. Install MySQL Server
2. Create database
3. Note: `mysql://user:pass@192.168.1.13:3306/dbname`

### Terminal 1: Users Service
```powershell
$env:SERVICE_NAME="users-service"
$env:DJANGO_HOST="192.168.1.13"
$env:DJANGO_PORT="8000"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8000
```

> **Note**: This also registers `token-service` and `token-refresh-service` automatically!

---

## Machine 5: Application Services

### Terminal 1: Products
```powershell
$env:SERVICE_NAME="products-service"
$env:DJANGO_HOST="192.168.1.14"
$env:DJANGO_PORT="8000"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2: Orders
```powershell
$env:SERVICE_NAME="orders-service"
$env:DJANGO_HOST="192.168.1.14"
$env:DJANGO_PORT="8001"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8001
```

### Terminal 3: Payments
```powershell
$env:SERVICE_NAME="payments-service"
$env:DJANGO_HOST="192.168.1.14"
$env:DJANGO_PORT="8002"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8002
```

### Terminal 4: Reviews
```powershell
$env:SERVICE_NAME="reviews-service"
$env:DJANGO_HOST="192.168.1.14"
$env:DJANGO_PORT="8003"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8003
```

### Terminal 5: Invoices
```powershell
$env:SERVICE_NAME="invoices-service"
$env:DJANGO_HOST="192.168.1.14"
$env:DJANGO_PORT="8004"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8004
```

### Terminal 6: Notifications
```powershell
$env:SERVICE_NAME="notifications-service"
$env:DJANGO_HOST="192.168.1.14"
$env:DJANGO_PORT="8005"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8005
```

### Terminal 7: Shop 
```powershell
$env:SERVICE_NAME="shop-service"
$env:DJANGO_HOST="192.168.1.14"
$env:DJANGO_PORT="8006"
$env:CONSUL_HOST="192.168.1.11"
$env:RABBITMQ_HOST="192.168.1.12"
$env:AUTO_REGISTER_CONSUL="true"
python manage.py runserver 0.0.0.0:8006
```

---

## Verification

### 1. Check Consul UI
- URL: `http://192.168.1.11:8500`
- Should show 10 healthy services (green)

### 2. Check Traefik Dashboard
- URL: `http://192.168.1.10:8080`
- Should show all routers

### 3. Access App from Phone
- Connect phone to same WiFi network
- Open browser: `http://192.168.1.10`

---

## Quick Reference

| Total Terminals | 13 |
|-----------------|-----|
| Machine 1 | 1 |
| Machine 2 | 1 |
| Machine 3 | 3 (RabbitMQ daemon + 2 workers) |
| Machine 4 | 1 |
| Machine 5 | 7 |