"""Admin registrations for complaints app."""
from django.contrib import admin
from .models import Complaint, CaseTimelineEvent, SLAPolicy


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("tracking_id", "title", "status", "urgency", "cell", "institution", "created_at")
    list_filter = ("status", "urgency", "cell", "category")
    search_fields = ("tracking_id", "title", "description")
    readonly_fields = ("tracking_id", "sequence", "complainant_encrypted", "complainant_nonce")


@admin.register(CaseTimelineEvent)
class CaseTimelineEventAdmin(admin.ModelAdmin):
    list_display = ("complaint", "event_type", "action", "actor_label", "created_at")
    list_filter = ("event_type",)


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ("cell", "urgency", "deadline_hours")
