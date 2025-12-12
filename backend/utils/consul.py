import requests
from config import CONSUL_HOST, CONSUL_PORT, DJANGO_HOST, DJANGO_PORT, get_health_check_url



def register_django(
    service_id: str,
    service_name: str,
    address: str,
    port: int,
    health_path: str = "/health/",
    interval: str = "10s",
    tags: list = None
):
    try:
        check_url = f"http://{address}:{port}{health_path}"
        service_data = {
            "ID": service_id,
            "Name": service_name,
            "Address": address,
            "Port": port,
            "Check": {"HTTP": check_url, "Interval": interval},
            "Tags": tags or []
        }
        requests.put(
            f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/agent/service/register",
            json=service_data
        )
        print(f"[Consul] Service enregistré: {service_name} ({address}:{port})")
    except Exception as e:
        print(f"[Consul] Erreur d'enregistrement: {e}")


def discover_service(name):
    try:
        url = f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/catalog/service/{name}"
        response = requests.get(url).json()
        if response:
            svc = response[0]
            return f"http://{svc['ServiceAddress']}:{svc['ServicePort']}"
    except Exception as e:
        print(f"[Consul] Erreur de découverte: {e}")
    return None


def discover(name):
    return discover_service(name)


def deregister_service(service_id: str):
    try:
        requests.put(
            f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/agent/service/deregister/{service_id}"
        )
        print(f"[Consul] Service désenregistré: {service_id}")
    except Exception as e:
        print(f"[Consul] Erreur de désenregistrement: {e}")
