
from django.core.management.base import BaseCommand
from config import DJANGO_HOST, DJANGO_PORT, SERVICE_NAME
from utils.consul import register_django

# Constants
HEALTH_PATH = "/health/"


class Command(BaseCommand):
    help = 'Register service with Consul'

    def handle(self, *args, **options):
        base_tags = ["traefik.enable=true"]
        service_id_prefix = f"{SERVICE_NAME}-"
        
        if SERVICE_NAME == "users-service":
            users_tags = base_tags + [
                "traefik.http.routers.users-get.entrypoints=web",
                "traefik.http.routers.users-get.rule=Method(`GET`) && PathPrefix(`/api/users`)",
                "traefik.http.routers.users-post.entrypoints=web",
                "traefik.http.routers.users-post.rule=Method(`POST`) && PathPrefix(`/api/users`)",
                "traefik.http.routers.users-put.entrypoints=web",
                "traefik.http.routers.users-put.rule=Method(`PUT`) && PathPrefix(`/api/users`)",
                "traefik.http.routers.users-delete.entrypoints=web",
                "traefik.http.routers.users-delete.rule=Method(`DELETE`) && PathPrefix(`/api/users`)",
                "traefik.http.routers.auth-get.entrypoints=web",
                "traefik.http.routers.auth-get.rule=Method(`GET`) && PathPrefix(`/api/auth`)",
                "traefik.http.routers.auth-post.entrypoints=web",
                "traefik.http.routers.auth-post.rule=Method(`POST`) && PathPrefix(`/api/auth`)",
                "traefik.http.services.users-service.loadbalancer.server.port=8000"
            ]
            register_django(
                service_id=f"{service_id_prefix}1",
                service_name="users-service",
                address=DJANGO_HOST,
                port=DJANGO_PORT,
                health_path=HEALTH_PATH,
                interval="10s",
                tags=users_tags
            )
            

            token_tags = base_tags + [
                "traefik.http.routers.token-post.entrypoints=web",
                "traefik.http.routers.token-post.rule=Method(`POST`) && PathPrefix(`/api/token`) && !PathPrefix(`/api/token/refresh`)",
                "traefik.http.services.token-service.loadbalancer.server.port=8000"
            ]
            register_django(
                service_id=f"{service_id_prefix}token-1",
                service_name="token-service",
                address=DJANGO_HOST,
                port=DJANGO_PORT,
                health_path=HEALTH_PATH,
                interval="10s",
                tags=token_tags
            )
            
            refresh_tags = base_tags + [
                "traefik.http.routers.token-refresh-post.entrypoints=web",
                "traefik.http.routers.token-refresh-post.rule=Method(`POST`) && PathPrefix(`/api/token/refresh`)",
                "traefik.http.services.token-refresh-service.loadbalancer.server.port=8000"
            ]
            register_django(
                service_id=f"{service_id_prefix}refresh-1",
                service_name="token-refresh-service",
                address=DJANGO_HOST,
                port=DJANGO_PORT,
                health_path=HEALTH_PATH,
                interval="10s",
                tags=refresh_tags
            )
            self.stdout.write(self.style.SUCCESS(f'Registered 3 services for {SERVICE_NAME}'))
            
        elif SERVICE_NAME == "products-service":
            products_tags = base_tags + [
                "traefik.http.routers.products-get.entrypoints=web",
                "traefik.http.routers.products-get.rule=Method(`GET`) && (PathPrefix(`/api/products`) || PathPrefix(`/api/categories`))",
                "traefik.http.routers.products-post.entrypoints=web",
                "traefik.http.routers.products-post.rule=Method(`POST`) && (PathPrefix(`/api/products`) || PathPrefix(`/api/categories`))",
                "traefik.http.routers.products-put.entrypoints=web",
                "traefik.http.routers.products-put.rule=Method(`PUT`) && PathPrefix(`/api/products`)",
                "traefik.http.routers.products-delete.entrypoints=web",
                "traefik.http.routers.products-delete.rule=Method(`DELETE`) && PathPrefix(`/api/products`)",
                "traefik.http.services.products-service.loadbalancer.server.port=8000"
            ]
            register_django(
                service_id=f"{service_id_prefix}1",
                service_name="products-service",
                address=DJANGO_HOST,
                port=DJANGO_PORT,
                health_path=HEALTH_PATH,
                interval="10s",
                tags=products_tags
            )
            self.stdout.write(self.style.SUCCESS(f'Registered {SERVICE_NAME}'))

        else:
            self.stdout.write(self.style.WARNING(f'No registration logic for {SERVICE_NAME}'))
