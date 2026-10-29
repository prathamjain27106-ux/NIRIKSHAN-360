"""
NIRIKSHAN 360 — Complaint Serializers
========================================
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Complaint, CaseTimelineEvent, SLAPolicy
from accounts.crypto import encrypt_identity


class SLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAPolicy
        fields = ("id", "cell", "urgency", "deadline_hours")


class CaseTimelineEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = CaseTimelineEvent
        fields = ("id", "event_type", "action", "detail", "actor_name", "actor_label", "created_at")
        read_only_fields = fields

    def get_actor_name(self, obj):
        return obj.actor_label or (obj.actor.username if obj.actor else "System")


class ComplaintListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no encrypted identity."""
    institution_name = serializers.SerializerMethodField()
    sla_breached = serializers.SerializerMethodField()
    duplicate_of = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = (
            "id", "tracking_id", "title", "category", "status", "urgency", "cell",
            "institution_name", "state", "routing_confidence", "needs_human_review",
            "is_duplicate_flagged", "duplicate_of", "sla_deadline", "sla_breached",
            "assigned_to", "source_channel", "language", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_institution_name(self, obj):
        if obj.institution:
            return obj.institution.name
        return obj.institution_name_text or "Unknown"

    def get_sla_breached(self, obj):
        return obj.is_sla_breached

    def get_duplicate_of(self, obj):
        if obj.duplicate_family:
            return obj.duplicate_family.tracking_id
        return None


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer — includes timeline but NOT decrypted identity."""
    institution_name = serializers.SerializerMethodField()
    sla_breached = serializers.SerializerMethodField()
    duplicate_of = serializers.SerializerMethodField()
    timeline = CaseTimelineEventSerializer(source="timeline_events", many=True, read_only=True)
    assigned_to_username = serializers.SerializerMethodField()
    evidence_count = serializers.SerializerMethodField()
    # Encrypted identity is shown as a hex digest, not plaintext
    complainant_encrypted_display = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = (
            "id", "tracking_id", "title", "description", "category", "status",
            "urgency", "cell", "institution", "institution_name", "state",
            "routing_confidence", "needs_human_review", "is_duplicate_flagged",
            "duplicate_of", "sla_deadline", "sla_breached", "assigned_to",
            "assigned_to_username", "source_channel", "language", "is_anonymous",
            "complainant_encrypted_display", "evidence_references", "evidence_count",
            "timeline", "created_at", "updated_at", "resolved_at",
        )
        read_only_fields = fields

    def get_institution_name(self, obj):
        return obj.institution.name if obj.institution else obj.institution_name_text or "Unknown"

    def get_sla_breached(self, obj):
        return obj.is_sla_breached

    def get_duplicate_of(self, obj):
        return obj.duplicate_family.tracking_id if obj.duplicate_family else None

    def get_assigned_to_username(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None

    def get_evidence_count(self, obj):
        return len(obj.evidence_references) if obj.evidence_references else 0

    def get_complainant_encrypted_display(self, obj):
        if obj.is_anonymous:
            return "[ANONYMOUS]"
        if obj.complainant_encrypted:
            ct = bytes(obj.complainant_encrypted) if not isinstance(obj.complainant_encrypted, bytes) else obj.complainant_encrypted
            return ct.hex()[:32] + "..."
        return "[no identity stored]"


class ComplaintCreateSerializer(serializers.Serializer):
    """Intake serializer — encrypts identity before storage."""
    title = serializers.CharField(max_length=500)
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=Complaint.Category.choices, default="OTHER")
    institution_name = serializers.CharField(max_length=300)
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    state = serializers.CharField(max_length=100, required=False, default="")
    language = serializers.ChoiceField(choices=Complaint.Language.choices, default="en")
    source_channel = serializers.ChoiceField(
        choices=Complaint.SourceChannel.choices, default="WEB_PORTAL",
    )
    complainant_name = serializers.CharField(max_length=200, required=False, default="")
    complainant_contact = serializers.CharField(max_length=200, required=False, default="")
    is_anonymous = serializers.BooleanField(default=False)
    evidence_references = serializers.ListField(
        child=serializers.CharField(), required=False, default=list,
    )

    def create(self, validated_data):
        # Build identity string and encrypt
        name = validated_data.pop("complainant_name", "")
        contact = validated_data.pop("complainant_contact", "")
        identity_str = f"name={name}|contact={contact}" if (name or contact) else ""
        is_anon = validated_data.get("is_anonymous", False)

        if is_anon or not identity_str:
            ciphertext, nonce = b"", b""
        else:
            ciphertext, nonce = encrypt_identity(identity_str)

        # Resolve institution
        inst_id = validated_data.pop("institution_id", None)
        inst_name = validated_data.pop("institution_name", "")
        institution = None
        if inst_id:
            from institutions.models import Institution
            try:
                institution = Institution.objects.get(pk=inst_id)
            except Institution.DoesNotExist:
                pass

        complaint = Complaint(
            title=validated_data["title"],
            description=validated_data["description"],
            category=validated_data.get("category", "OTHER"),
            language=validated_data.get("language", "en"),
            source_channel=validated_data.get("source_channel", "WEB_PORTAL"),
            state=validated_data.get("state", ""),
            institution=institution,
            institution_name_text=inst_name if not institution else "",
            complainant_encrypted=ciphertext,
            complainant_nonce=nonce,
            is_anonymous=is_anon,
            evidence_references=validated_data.get("evidence_references", []),
        )
        # Demonstration routing rules are deliberately explicit and human-reviewable.
        route_by_category = {
            Complaint.Category.RAGGING: SLAPolicy.Cell.ANTI_RAGGING,
            Complaint.Category.SEXUAL_HARASSMENT: SLAPolicy.Cell.ICC,
            Complaint.Category.SCHOLARSHIP_ISSUE: SLAPolicy.Cell.SCHOLARSHIP,
            Complaint.Category.APPROVAL_VIOLATION: SLAPolicy.Cell.RB,
            Complaint.Category.FEE_REFUND: SLAPolicy.Cell.PGRC,
            Complaint.Category.CERTIFICATE_WITHHOLDING: SLAPolicy.Cell.PGRC,
        }
        complaint.cell = route_by_category.get(
            complaint.category, SLAPolicy.Cell.PGRC,
        )
        complaint.routing_confidence = 100 if complaint.category in route_by_category else 0
        complaint.needs_human_review = complaint.routing_confidence < 100
        urgency_by_category = {
            Complaint.Category.RAGGING: SLAPolicy.Urgency.CRITICAL,
            Complaint.Category.SEXUAL_HARASSMENT: SLAPolicy.Urgency.CRITICAL,
        }
        complaint.urgency = urgency_by_category.get(
            complaint.category, SLAPolicy.Urgency.MEDIUM,
        )
        policy = SLAPolicy.objects.filter(
            cell=complaint.cell, urgency=complaint.urgency,
        ).first()
        if policy:
            complaint.sla_deadline = timezone.now() + timezone.timedelta(
                hours=policy.deadline_hours,
            )
        complaint.save()

        # Create submission timeline event
        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.SUBMISSION,
            action="Complaint Submitted",
            detail=f"Complaint received via {complaint.get_source_channel_display()}",
            actor_label="System",
        )

        return complaint


class ComplaintAssignSerializer(serializers.Serializer):
    """Assign a complaint to an analyst."""
    assigned_to = serializers.IntegerField(help_text="User ID of the assignee")

    def validate_assigned_to(self, value):
        from accounts.models import User
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if user.role not in ("ADMIN", "BUREAU_HEAD", "ANALYST"):
            raise serializers.ValidationError("Can only assign to admin, bureau head, or analyst.")
        return value


class ComplaintStatusSerializer(serializers.Serializer):
    """Update complaint status with required reason."""
    status = serializers.ChoiceField(choices=Complaint.Status.choices)
    reason = serializers.CharField(max_length=500, required=False, default="")


class CSVImportSerializer(serializers.Serializer):
    """Validate CSV import file."""
    csv_file = serializers.FileField()
