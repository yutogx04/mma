from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'utils'
    
    def ready(self):
        """
        Register service with Consul on Django startup
        (Course pattern - auto-registration)
        """
        import os
        # Only register in main process, not in autoreload
        if os.environ.get('RUN_MAIN') == 'true':
            try:
                from config import DJANGO_HOST, DJANGO_PORT
                from .consul import register_django
                register_django(
                    service_id="django-service-1",
                    service_name="django-service",
                    address=DJANGO_HOST,
                    port=DJANGO_PORT,
                    health_path="/health/",
                    interval="10s"
                )
            except Exception as e:
                print(f"[Consul] Erreur au démarrage: {e}")
