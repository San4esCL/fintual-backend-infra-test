from django.db import connection
from django.http import JsonResponse


def live(_request):
    return JsonResponse({"status": "ok"})


def ready(_request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
