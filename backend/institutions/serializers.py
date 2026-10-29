"""
NIRIKSHAN 360 — Institution Serializers
==========================================
"""

from rest_framework import serializers
from .models import Institution, NormCheckResult, InstitutionReply


class InstitutionListSerializer(serializers.ModelSerializer):
    total_complaints = serializers.SerializerMethodField()
    open_complaints = serializers.SerializerMethodField()
    resolved_complaints = serializers.SerializerMethodField()

    class Meta:
        model = Institution
        fields = (
            "id", "name", "aicte_id", "state", "city", "institution_type",
            "student_count", "established_year", "compliance_score",
            "norm_check_status", "last_inspection", "total_complaints",
            "open_complaints", "resolved_complaints",
        )
        read_only_fields = fields

    def get_total_complaints(self, obj):
        return obj.complaints.count()

    def get_open_complaints(self, obj):
        return obj.complaints.exclude(
            status__in=["RESOLVED", "CLOSED"]
        ).count()

    def get_resolved_complaints(self, obj):
        return obj.complaints.filter(status="RESOLVED").count()


class InstitutionDetailSerializer(InstitutionListSerializer):
    nodal_officer_name = serializers.SerializerMethodField()

    class Meta(InstitutionListSerializer.Meta):
        fields = InstitutionListSerializer.Meta.fields + (
            "nodal_officer", "nodal_officer_name", "created_at", "updated_at",
        )

    def get_nodal_officer_name(self, obj):
        return obj.nodal_officer.username if obj.nodal_officer else None


class NormCheckResultSerializer(serializers.ModelSerializer):
    checked_by_name = serializers.SerializerMethodField()

    class Meta:
        model = NormCheckResult
        fields = (
            "id", "institution", "norm", "category", "status",
            "detail", "source", "checked_at", "checked_by", "checked_by_name",
        )
        read_only_fields = fields

    def get_checked_by_name(self, obj):
        return obj.checked_by.username if obj.checked_by else "System"


class InstitutionReplySerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    complaint_tracking_id = serializers.SerializerMethodField()

    class Meta:
        model = InstitutionReply
        fields = (
            "id", "complaint", "complaint_tracking_id", "institution",
            "submitted_by", "submitted_by_name", "content", "status",
            "reviewed_by", "reviewed_by_name", "created_at", "updated_at",
        )
        read_only_fields = ("id", "submitted_by", "submitted_by_name",
                           "reviewed_by", "reviewed_by_name", "status",
                           "complaint_tracking_id", "created_at", "updated_at")

    def get_submitted_by_name(self, obj):
        return obj.submitted_by.username if obj.submitted_by else None

    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.username if obj.reviewed_by else None

    def get_complaint_tracking_id(self, obj):
        return obj.complaint.tracking_id if obj.complaint else None


class InstitutionReplyCreateSerializer(serializers.Serializer):
    complaint_id = serializers.UUIDField()
    content = serializers.CharField()

    def validate_complaint_id(self, value):
        from complaints.models import Complaint
        try:
            Complaint.objects.get(pk=value)
        except Complaint.DoesNotExist:
            raise serializers.ValidationError("Complaint not found.")
        return value
