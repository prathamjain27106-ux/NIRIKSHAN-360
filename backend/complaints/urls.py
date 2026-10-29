"""Complaint URL routes."""

from django.urls import path
from . import views

app_name = "complaints"

urlpatterns = [
    # Dashboard analytics
    path("dashboard/", views.DashboardAnalyticsView.as_view(), name="dashboard"),
    # SLA policies
    path("sla-policies/", views.SLAPolicyListView.as_view(), name="sla-policies"),
    # CSV import
    path("import-csv/", views.CSVImportView.as_view(), name="import-csv"),
    # Complaint CRUD
    path("", views.ComplaintListView.as_view(), name="list"),
    path("create/", views.ComplaintCreateView.as_view(), name="create"),
    path("<str:pk>/", views.ComplaintDetailView.as_view(), name="detail"),
    path("<str:pk>/assign/", views.ComplaintAssignView.as_view(), name="assign"),
    path("<str:pk>/status/", views.ComplaintStatusUpdateView.as_view(), name="status"),
    path("<str:pk>/duplicates/", views.ComplaintDuplicatesView.as_view(), name="duplicates"),
    path("<str:pk>/timeline/", views.ComplaintTimelineView.as_view(), name="timeline"),
]
