"""Audit URL routes."""

from django.urls import path
from . import views

app_name = "audit"

urlpatterns = [
    path("", views.AuditEventListView.as_view(), name="list"),
    path("identity/request/", views.IdentityRevealRequestView.as_view(), name="identity-request"),
    path("identity/<uuid:pk>/approve/", views.IdentityRevealApproveView.as_view(), name="identity-approve"),
]
