from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from blog.api import router as blog_router
from core.health import live, ready

api = NinjaAPI()
api.add_router("/", blog_router)

urlpatterns = [
    path("health/live", live, name="health-live"),
    path("health/ready", ready, name="health-ready"),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
