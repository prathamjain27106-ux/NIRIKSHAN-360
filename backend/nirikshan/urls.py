"""
NIRIKSHAN 360 — URL Configuration
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.db import connection


def health_check(request):
    """Health endpoint — checks database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    return JsonResponse({
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "NIRIKSHAN 360",
        "database": db_status,
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/complaints/", include("complaints.urls")),
    path("api/institutions/", include("institutions.urls")),
    path("api/audit/", include("audit.urls")),
    # Institution replies (cross-cutting)
    path("api/replies/", include([
        path("", __import__("institutions.views", fromlist=["InstitutionReplyCreateView"]).InstitutionReplyCreateView.as_view(), name="reply-create"),
        path("<uuid:pk>/review/", __import__("institutions.views", fromlist=["InstitutionReplyReviewView"]).InstitutionReplyReviewView.as_view(), name="reply-review"),
    ])),
    # Health check
    path("api/health/", health_check, name="health"),
]
