"""Institution URL routes."""

from django.urls import path
from . import views

app_name = "institutions"

urlpatterns = [
    path("", views.InstitutionListView.as_view(), name="list"),
    path("<uuid:pk>/", views.InstitutionDetailView.as_view(), name="detail"),
    path("<uuid:pk>/norm-checks/", views.NormCheckListView.as_view(), name="norm-checks"),
    path("<uuid:pk>/norm-check/", views.NormCheckListView.as_view(), name="norm-check-alias"),
    path("<uuid:pk>/run-norm-check/", views.RunNormCheckView.as_view(), name="run-norm-check"),
    path("<uuid:pk>/compliance-radar/", views.ComplianceRadarView.as_view(), name="compliance-radar"),
    path("<uuid:pk>/replies/", views.InstitutionReplyListView.as_view(), name="replies"),
]
