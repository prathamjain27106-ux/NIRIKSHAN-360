"""Complaint URL routes."""

from django.urls import path
from . import views

app_name = "complaints"

urlpatterns = [
    # Dashboard analytics
    path("dashboard/", views.DashboardAnalyticsView.as_view(), name="dashboard"),
    path("systemic-pulse/", views.systemic_pulse_analysis, name="systemic-pulse"),
    path("import-csv/preview/", views.csv_import_handler, name="import-csv-preview"),
    # SLA policies
    path("sla-policies/", views.SLAPolicyListView.as_view(), name="sla-policies"),
    # Case graph
    path("graph/", views.CaseGraphView.as_view(), name="graph"),
    # Triage preview
    path("triage-preview/", views.TriagePreviewView.as_view(), name="triage-preview"),
    # SLA escalations batch check
    path("check-escalations/", views.CheckEscalationsView.as_view(), name="check-escalations"),
    # CSV import
    path("import-csv/", views.CSVImportView.as_view(), name="import-csv"),
    # Complaint CRUD & operations
    path("", views.ComplaintListView.as_view(), name="list"),
    path("create/", views.ComplaintCreateView.as_view(), name="create"),
    path("<str:pk>/", views.ComplaintDetailView.as_view(), name="detail"),
    path("<str:pk>/assign/", views.ComplaintAssignView.as_view(), name="assign"),
    path("<str:pk>/status/", views.ComplaintStatusUpdateView.as_view(), name="status"),
    path("<str:pk>/override/", views.ComplaintHumanOverrideView.as_view(), name="override"),
    path("<str:pk>/triage-override/", views.override_triage_decision, name="triage-override"),
    path("<str:pk>/duplicates/", views.ComplaintDuplicatesView.as_view(), name="duplicates"),
    path("<str:pk>/link-duplicate/", views.ComplaintDuplicateLinkView.as_view(), name="link-duplicate"),
    path("<str:pk>/dismiss-duplicate/", views.ComplaintDuplicateDismissView.as_view(), name="dismiss-duplicate"),
    path("<str:pk>/timeline/", views.ComplaintTimelineView.as_view(), name="timeline"),
]
