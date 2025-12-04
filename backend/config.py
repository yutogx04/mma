"""
Configuration for Multi-Server Deployment
Edit these values with your actual machine IP addresses
"""
import os

# =====================================================
# MACHINE IP ADDRESSES - EDIT THESE FOR YOUR NETWORK
# =====================================================

# Django API Server (this machine or remote)
DJANGO_HOST = os.getenv("DJANGO_HOST", "127.0.0.1")
DJANGO_PORT = int(os.getenv("DJANGO_PORT", "8000"))

# RabbitMQ Server
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))

# Consul Server
CONSUL_HOST = os.getenv("CONSUL_HOST", "localhost")
CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))

# Traefik Reverse Proxy
TRAEFIK_HOST = os.getenv("TRAEFIK_HOST", "localhost")
TRAEFIK_PORT = int(os.getenv("TRAEFIK_PORT", "80"))


# =====================================================
# Helper functions for service URLs
# =====================================================

def get_rabbitmq_url():
    """Get RabbitMQ connection URL"""
    return f"{RABBITMQ_HOST}"

def get_consul_url():
    """Get Consul API URL"""
    return f"http://{CONSUL_HOST}:{CONSUL_PORT}"

def get_django_url():
    """Get Django API URL"""
    return f"http://{DJANGO_HOST}:{DJANGO_PORT}"

def get_health_check_url():
    """Get health check URL for Consul"""
    return f"http://{DJANGO_HOST}:{DJANGO_PORT}/health/"
