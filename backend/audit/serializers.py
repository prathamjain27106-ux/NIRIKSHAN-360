"""
NIRIKSHAN 360 — Audit Serializers
====================================
"""

from rest_framework import serializers
from .models import AuditEvent, IdentityAccessRequest, IdentityAccessApproval


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = (
            "id", "timestamp", "actor_username", "actor_role", "action",
            "target_type", "target_id", "detail", "ip_address",
        )
        read_only_fields = fields


class IdentityAccessApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = IdentityAccessApproval
        fields = ("id", "approver", "approver_name", "approved", "comment", "created_at")
        read_only_fields = ("id", "approver", "approver_name", "created_at")

    def get_approver_name(self, obj):
        return obj.approver.username if obj.approver else None


class IdentityAccessRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.SerializerMethodField()
    approvals = IdentityAccessApprovalSerializer(many=True, read_only=True)
    approval_count = serializers.IntegerField(read_only=True, source="approval_count")
    is_fully_approved = serializers.BooleanField(read_only=True)
    complaint_tracking_id = serializers.SerializerMethodField()

    class Meta:
        model = IdentityAccessRequest
        fields = (
            "id", "complaint", "complaint_tracking_id", "requester",
            "requester_name", "reason", "status", "approval_count",
            "is_fully_approved", "approvals", "created_at", "updated_at",
        )
        read_only_fields = ("id", "requester", "requester_name", "status",
                           "approval_count", "is_fully_approved", "approvals",
                           "complaint_tracking_id", "created_at", "updated_at")

    def get_requester_name(self, obj):
        return obj.requester.username if obj.requester else None

    def get_complaint_tracking_id(self, obj):
        return obj.complaint.tracking_id if obj.complaint else None


class IdentityRevealRequestCreateSerializer(serializers.Serializer):
    complaint_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=1000)


class IdentityRevealApproveSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    comment = serializers.CharField(max_length=500, required=False, default="")
