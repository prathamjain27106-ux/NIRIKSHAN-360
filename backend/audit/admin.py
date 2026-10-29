"""Admin registrations for audit app."""
from django.contrib import admin
from .models import AuditEvent, IdentityAccessRequest, IdentityAccessApproval


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "action", "actor_username", "target_type", "target_id")
    list_filter = ("action",)
    search_fields = ("actor_username", "target_id", "detail")
    readonly_fields = ("id", "timestamp", "actor", "actor_username", "actor_role", "action",
                       "target_type", "target_id", "detail", "ip_address")

    def has_change_permission(self, request, obj=None):
        return False  # Audit events are immutable

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IdentityAccessRequest)
class IdentityAccessRequestAdmin(admin.ModelAdmin):
    list_display = ("complaint", "requester", "status", "created_at")
    list_filter = ("status",)


@admin.register(IdentityAccessApproval)
class IdentityAccessApprovalAdmin(admin.ModelAdmin):
    list_display = ("request", "approver", "approved", "created_at")
