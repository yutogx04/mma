# Multi-Server Deployment Guide 

## Overview
So in here i'm gonna try and explain how to deploy the WAMS project across the machines/servers we're gonna use.



## Step 1: Configure IP Addresses

Edit `backend/config.py` with your machine IPs:

DJANGO_HOST = "192.168.1.10"
DJANGO_PORT = 8000
RABBITMQ_HOST = "192.168.1.11"
RABBITMQ_PORT = 5672
CONSUL_HOST = "192.168.1.12"
CONSUL_PORT = 8500
TRAEFIK_HOST = "192.168.1.13"

## Step 2: Setup Each Machine
(Sidenote: since again we are only 3 people, one will have to start multiple services on his machine, this is just an example of an implementation)

### Machine for Django API Server

# 1. Copy project to this machine
# 2. Install Python 3.13
# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Configure environment
# Edit .env file with correct IPs

# 5. Run Django
python manage.py runserver 


### Machine for RabbitMQ Server


# Windows: Download from https://www.rabbitmq.com/download.html, for linux i don't know but it should be on the official page there is a command to download it
# Install Erlang first, then RabbitMQ

# Start RabbitMQ
rabbitmq-server

# Enable management UI (optional but we should do it for more clarity)
rabbitmq-plugins enable rabbitmq_management
# Access at http://192.168.1.11:15672 (guest/guest)


### Machine for Worker (Payment Consumer)


# 1. Copy project to this machine
# 2. Install Python and dependencies
pip install -r requirements.txt

# 3. Run the consumer
python manage.py start_consumer


### Machine for Consul Server

# Download from https://www.consul.io/downloads
# Extract consul.exe

# Start Consul
consul agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=192.168.1.12

# Access UI at http://192.168.1.12:8500


### Machine for Traefik Reverse Proxy


# Download from https://github.com/traefik/traefik/releases or just type the command for linux
# Extract traefik.exe

# Copy traefik.yml and dynamic.yml to same folder
# Edit dynamic.yml with Django IP

# Start Traefik
traefik --configFile=traefik.yml

# Dashboard at http://192.168.1.13:8080


## Step 3: Network Configuration

1. All machines must be on the **same network** (or have routes), in this one preferbly a phone
2. Open required ports in **Windows Firewall**:
   # On Django machine
   netsh advfirewall firewall add rule name="Django" dir=in action=allow protocol=TCP localport=8000
   
   # On RabbitMQ machine
   netsh advfirewall firewall add rule name="RabbitMQ" dir=in action=allow protocol=TCP localport=5672
   
   # On Consul machine
   netsh advfirewall firewall add rule name="Consul" dir=in action=allow protocol=TCP localport=8500


## Step 4: Start Order (This is very important for everything to work!)

1. **First**: Start Consul 
2. **Second**: Start RabbitMQ 
3. **Third**: Start Django 
4. **Fourth**: Start Worker 
5. **Last**: Start Traefik 


## Step 5: Verify Deployment

# Check health (from any machine)
curl http://192.168.1.10:8000/health/
# Should return: {"status": "ok"}

# Check Consul UI
# Open: http://192.168.1.12:8500

# Check RabbitMQ UI
# Open: http://192.168.1.11:15672

# Check Traefik Dashboard
# Open: http://192.168.1.13:8080

## Using Phones as Servers

And yes, like you said faical we're gonna use phones running commands via something called **Termux** for Android or maybe you know of some other things to host with a phone:


# On Android phone with Termux
pkg install python
pip install django djangorestframework pika

# Run Django
cd backend
python manage.py runserver 0.0.0.0:8000

Get phone IP: Settings → WiFi → Your network → IP address

