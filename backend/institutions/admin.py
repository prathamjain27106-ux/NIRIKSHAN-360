"""Admin registrations for institutions app."""
from django.contrib import admin
from .models import Institution, NormCheckResult, InstitutionReply


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "aicte_id", "state", "institution_type", "compliance_score", "norm_check_status")
    list_filter = ("institution_type", "norm_check_status", "state")
    search_fields = ("name", "aicte_id", "city")


@admin.register(NormCheckResult)
class NormCheckResultAdmin(admin.ModelAdmin):
    list_display = ("institution", "norm", "status", "checked_at")
    list_filter = ("status",)


@admin.register(InstitutionReply)
class InstitutionReplyAdmin(admin.ModelAdmin):
    list_display = ("complaint", "institution", "submitted_by", "status", "created_at")
    list_filter = ("status",)
