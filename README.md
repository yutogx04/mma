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

# Distributed Application Deployment Guide (5 Machines)

This guide details how to deploy the application across 5 separate
machines.

##  IMPORTANT

**Prerequisite:** You must have a shared **MySQL Database accessible to
all machines**.\
This guide assumes you will configure the database connection details in
the `.env` file on each machine.

------------------------------------------------------------------------

##  Network Setup

Assign static IP addresses to your 5 machines to ensure they can find
each other:

  Machine     Role                   IP
  ----------- ---------------------- ----------------
  Machine 1   Traefik / Gateway      `192.168.1.10`
  Machine 2   Consul / Registry      `192.168.1.11`
  Machine 3   Messaging / RabbitMQ   `192.168.1.12`
  Machine 4   Auth / Core / DB       `192.168.1.13`
  Machine 5   App / Services         `192.168.1.14`

(Adjust these IPs to match your actual network.)

------------------------------------------------------------------------

##  Machine 1: The Gateway (Traefik)

**Role:** Accepts all incoming traffic and routes it to the correct
service.

Create a folder `deployment` and inside it create `docker-compose.yml`:

``` yaml
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
      - "--entrypoints.web.address=:80"
```

Run:

``` bash
docker-compose up -d
```

------------------------------------------------------------------------

##  Machine 2: The Registry (Consul)

**Role:** Tracks where every service is running.

Create `docker-compose.yml`:

``` yaml
version: '3.8'
services:
  consul:
    image: consul:1.15
    ports:
      - "8500:8500"
    command: agent -server -bootstrap-expect=1 -ui -client=0.0.0.0
```

Run:

``` bash
docker-compose up -d
```

------------------------------------------------------------------------

##  Machine 3: Messaging (RabbitMQ + Workers)

**Role:** Background tasks, payments, notifications.

Create `.env`:

    RABBITMQ_HOST=192.168.1.12
    CONSUL_HOST=192.168.1.11
    DJANGO_HOST=192.168.1.12
    DATABASE_URL=mysql://user:pass@192.168.1.13:3306/db_name

Create `docker-compose.yml`:

``` yaml
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]

  payment-worker:
    image: mma-backend:latest
    command: python manage.py start_consumer
    env_file: .env
    depends_on: [rabbitmq]

  notification-worker:
    image: mma-backend:latest
    command: python manage.py start_notification_consumer
    env_file: .env
    depends_on: [rabbitmq]
```

Run:

``` bash
docker-compose up -d
```

------------------------------------------------------------------------

##  Machine 4: Core (Auth & Database)

**Role:** Hosts Database + Users/Token services.

Install **MySQL** here and enable remote access.

Create `.env`:

    RABBITMQ_HOST=192.168.1.12
    CONSUL_HOST=192.168.1.11
    DJANGO_HOST=192.168.1.13
    DATABASE_URL=mysql://user:pass@127.0.0.1:3306/db_name
    SERVICE_NAME=users-service

Create `docker-compose.yml`:

``` yaml
version: '3.8'
services:
  users-service:
    image: mma-backend:latest
    ports: ["8000:8000"]
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

------------------------------------------------------------------------

##  Machine 5: Marketplace (All App Services)

**Role:** Products, Orders, Shop, etc.

Create `.env`:

    RABBITMQ_HOST=192.168.1.12
    CONSUL_HOST=192.168.1.11
    DJANGO_HOST=192.168.1.14
    DATABASE_URL=mysql://user:pass@192.168.1.13:3306/db_name

Create `docker-compose.yml`:

``` yaml
version: '3.8'
services:
  products:
    image: mma-backend:latest
    ports: ["8000:8000"]
    env_file: .env
    environment:
      - SERVICE_NAME=products-service

  orders:
    image: mma-backend:latest
    ports: ["8001:8000"]
    env_file: .env
    environment:
       - SERVICE_NAME=orders-service

  # Add other services (shop, reviews, invoices...)
  # Use ports 8002, 8003, 8004...
```

Run:

``` bash
docker-compose up -d
```

------------------------------------------------------------------------

## 💡 TIP

Since all Machine 5 services share the same IP, always map **unique
ports**\
(8000, 8001, 8002...) and the existing `utils/apps.py` will correctly
register them in Consul.

# No Docker Deployment Guide

If we don't use Docker, we must run every service as a standard program directly on each operating system (Windows/Linux).

##  WARNING
Since you don't have containers to isolate processes, one will need to **open MULTIPLE TERMINALS** on each machine to run the different services simultaneously.

##  Prerequisites (Install on ALL machines)

- **Python 3.10+**
  ```bash
  pip install -r backend/requirements.txt
  ```

- **Git**

#  Machine 1: The Gateway (Traefik)

## Role: Runs Traefik reverse proxy

### 1. Download Traefik

### 2. Create Traefik Config

```yaml
api:
  insecure: true
providers:
  consulCatalog:
    endpoint:
      address: "192.168.1.11:8500"
entryPoints:
  web:
    address: ":80"
```

### 3. Run Traefik

**Windows**
```powershell
.	raefik.exe --configfile=traefik.yml
```

**Linux**
```bash
./traefik --configfile=traefik.yml
```

#  Machine 2: The Registry (Consul)

## Role: Consul Service Registry

**Windows**
```powershell
.\consul.exe agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=192.168.1.11 -data-dir=./data
```

**Linux**
```bash
./consul agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=192.168.1.11 -data-dir=./data
```

#  Machine 3: Messaging (RabbitMQ + Workers)

## Install RabbitMQ

## Python Workers

### Terminal 1 — Payment Worker
```powershell
$env:RABBITMQ_HOST="192.168.1.12"
$env:CONSUL_HOST="192.168.1.11"
$env:DATABASE_URL="mysql://..."
python manage.py start_consumer
```

### Terminal 2 — Notification Worker
```powershell
$env:RABBITMQ_HOST="192.168.1.12"
$env:CONSUL_HOST="192.168.1.11"
$env:DATABASE_URL="mysql://..."
python manage.py start_notification_consumer
```

#  Machine 4: Core (Auth & Database)

### Terminal 1 (Users — 8000)
```powershell
$env:SERVICE_NAME="users-service"
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2 (Token — 8001)
```powershell
$env:SERVICE_NAME="token-service"
python manage.py runserver 0.0.0.0:8001
```

#  Machine 5: Marketplace Services

### Products (8000)
```powershell
$env:SERVICE_NAME="products-service"
python manage.py runserver 0.0.0.0:8000
```

### Orders (8001)
```powershell
$env:SERVICE_NAME="orders-service"
python manage.py runserver 0.0.0.0:8001
```

### Shop (8002)
```powershell
$env:SERVICE_NAME="shop-service"
python manage.py runserver 0.0.0.0:8002
```

### Reviews (8003)
```powershell
$env:SERVICE_NAME="reviews-service"
python manage.py runserver 0.0.0.0:8003
```

## TIP
Setting `$env:SERVICE_NAME` tells the code which service is running so it registers correctly with Consul.
