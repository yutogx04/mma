"""
Utils App Views
Health Check endpoint for Consul
"""
from django.http import JsonResponse


def health_check(request):
    """
    Health Check endpoint for Consul
    (Course pattern - health_check)
    
    Returns {"status": "ok"} with HTTP 200 if service is healthy.
    Consul calls this endpoint regularly to verify service status.
    """
    return JsonResponse({"status": "ok"}, status=200)
