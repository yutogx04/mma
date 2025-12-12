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

  token-service:
    image: mma-backend:latest
    ports: ["8001:8000"]
    env_file: .env
    environment:
      - SERVICE_NAME=token-service
```

Run:

``` bash
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

------------------------------------------------------------------------

## 💡 TIP

Since all Machine 5 services share the same IP, always map **unique
ports**\
(8000, 8001, 8002...) and the existing `utils/apps.py` will correctly
register them in Consul.