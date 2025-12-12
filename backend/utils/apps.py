from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'utils'
    
    def ready(self):
        import os
        # Only auto-register if explicitly enabled (for Docker deployment)
        # For local development, use JSON files in consul/services/ instead
        if os.environ.get('RUN_MAIN') == 'true' and os.environ.get('AUTO_REGISTER_CONSUL') == 'true':
            try:
                from config import DJANGO_HOST, DJANGO_PORT, SERVICE_NAME
                from .consul import register_django
                
                base_tags = ["traefik.enable=true"]
                service_id_prefix = f"{SERVICE_NAME}-"
                
                if SERVICE_NAME == "users-service":
                    # 1. Users Service
                    users_tags = base_tags + [
                        "traefik.http.routers.users-get.rule=Method('GET') && PathPrefix('/api/users')",
                        "traefik.http.routers.users-post.rule=Method('POST') && PathPrefix('/api/users')",
                        "traefik.http.routers.users-put.rule=Method('PUT') && PathPrefix('/api/users')",
                        "traefik.http.routers.users-delete.rule=Method('DELETE') && PathPrefix('/api/users')",
                        "traefik.http.routers.auth-get.rule=Method('GET') && PathPrefix('/api/auth')",
                        "traefik.http.routers.auth-post.rule=Method('POST') && PathPrefix('/api/auth')",
                        "traefik.http.services.users-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="users-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=users_tags
                    )
                    
                    # 2. Token Service (JWT generation)
                    token_tags = base_tags + [
                        "traefik.http.routers.token-post.rule=Method('POST') && PathPrefix('/api/token') && !PathPrefix('/api/token/refresh')",
                        "traefik.http.services.token-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}token-1",
                        service_name="token-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=token_tags
                    )
                    
                    # 3. Token Refresh Service
                    refresh_tags = base_tags + [
                        "traefik.http.routers.token-refresh-post.rule=Method('POST') && PathPrefix('/api/token/refresh')",
                        "traefik.http.services.token-refresh-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}refresh-1",
                        service_name="token-refresh-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=refresh_tags
                    )
                    
                elif SERVICE_NAME == "products-service":
                    # 4. Products Service
                    products_tags = base_tags + [
                        "traefik.http.routers.products-get.rule=Method('GET') && (PathPrefix('/api/products') || PathPrefix('/api/categories'))",
                        "traefik.http.routers.products-post.rule=Method('POST') && (PathPrefix('/api/products') || PathPrefix('/api/categories'))",
                        "traefik.http.routers.products-put.rule=Method('PUT') && PathPrefix('/api/products')",
                        "traefik.http.routers.products-delete.rule=Method('DELETE') && PathPrefix('/api/products')",
                        "traefik.http.services.products-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="products-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=products_tags
                    )
                    
                elif SERVICE_NAME == "orders-service":
                    # 5. Orders Service
                    orders_tags = base_tags + [
                        "traefik.http.routers.orders-get.rule=Method('GET') && (PathPrefix('/api/orders') || PathPrefix('/api/cart'))",
                        "traefik.http.routers.orders-post.rule=Method('POST') && (PathPrefix('/api/orders') || PathPrefix('/api/cart'))",
                        "traefik.http.routers.orders-put.rule=Method('PUT') && PathPrefix('/api/orders')",
                        "traefik.http.routers.orders-delete.rule=Method('DELETE') && (PathPrefix('/api/orders') || PathPrefix('/api/cart'))",
                        "traefik.http.services.orders-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="orders-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=orders_tags
                    )
                    
                elif SERVICE_NAME == "payments-service":
                    # 6. Payments Service
                    payments_tags = base_tags + [
                        "traefik.http.routers.payments-get.rule=Method('GET') && (PathPrefix('/api/payments') || PathPrefix('/api/payment-methods'))",
                        "traefik.http.routers.payments-post.rule=Method('POST') && (PathPrefix('/api/payments') || PathPrefix('/api/payment-methods'))",
                        "traefik.http.routers.payments-delete.rule=Method('DELETE') && PathPrefix('/api/payment-methods')",
                        "traefik.http.services.payments-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="payments-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=payments_tags
                    )
                    
                elif SERVICE_NAME == "reviews-service":
                    # 7. Reviews Service
                    reviews_tags = base_tags + [
                        "traefik.http.routers.reviews-get.rule=Method('GET') && PathPrefix('/api/reviews')",
                        "traefik.http.routers.reviews-post.rule=Method('POST') && PathPrefix('/api/reviews')",
                        "traefik.http.routers.reviews-put.rule=Method('PUT') && PathPrefix('/api/reviews')",
                        "traefik.http.routers.reviews-delete.rule=Method('DELETE') && PathPrefix('/api/reviews')",
                        "traefik.http.services.reviews-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="reviews-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=reviews_tags
                    )
                    
                elif SERVICE_NAME == "invoices-service":
                    # 8. Invoices Service
                    invoices_tags = base_tags + [
                        "traefik.http.routers.invoices-get.rule=Method('GET') && PathPrefix('/api/invoices')",
                        "traefik.http.routers.invoices-post.rule=Method('POST') && PathPrefix('/api/invoices')",
                        "traefik.http.services.invoices-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="invoices-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=invoices_tags
                    )
                    
                elif SERVICE_NAME == "notifications-service":
                    # 9. Notifications Service
                    notifications_tags = base_tags + [
                        "traefik.http.routers.notifications-get.rule=Method('GET') && PathPrefix('/api/notifications')",
                        "traefik.http.routers.notifications-post.rule=Method('POST') && PathPrefix('/api/notifications')",
                        "traefik.http.services.notifications-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="notifications-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=notifications_tags
                    )
                    
                elif SERVICE_NAME == "shop-service":
                    # 10. Shop Service (handles admin, static, dashboard, root)
                    shop_tags = base_tags + [
                        "traefik.http.routers.shop-api.rule=PathPrefix('/api/shops')",
                        "traefik.http.routers.shop-admin.rule=PathPrefix('/admin')",
                        "traefik.http.routers.shop-static.rule=PathPrefix('/static')",
                        "traefik.http.routers.shop-media.rule=PathPrefix('/media')",
                        "traefik.http.routers.shop-dashboard.rule=PathPrefix('/dashboard')",
                        "traefik.http.routers.shop-root.rule=PathPrefix('/')",
                        "traefik.http.routers.shop-root.priority=1",
                        "traefik.http.services.shop-service.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name="shop-service",
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=shop_tags
                    )
                    
                else:
                    # Fallback for any other service names
                    fallback_tags = base_tags + [
                        f"traefik.http.routers.{SERVICE_NAME}.rule=PathPrefix('/api')",
                        f"traefik.http.services.{SERVICE_NAME}.loadbalancer.server.port=8000"
                    ]
                    register_django(
                        service_id=f"{service_id_prefix}1",
                        service_name=SERVICE_NAME,
                        address=DJANGO_HOST,
                        port=DJANGO_PORT,
                        health_path="/health/",
                        interval="10s",
                        tags=fallback_tags
                    )
                    
            except Exception as e:
                print(f"[Consul] Erreur au démarrage: {e}")

