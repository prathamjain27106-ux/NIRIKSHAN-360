"""
NIRIKSHAN 360 — URL Configuration
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/complaints/", include("complaints.urls")),
    path("api/institutions/", include("institutions.urls")),
    path("api/audit/", include("audit.urls")),
    # Health check
    path("api/health/", lambda request: __import__("django.http", fromlist=["JsonResponse"]).JsonResponse({"status": "ok", "service": "NIRIKSHAN 360"})),
]
