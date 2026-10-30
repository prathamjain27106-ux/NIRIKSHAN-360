"""
NIRIKSHAN 360 — Complaint Serializers
========================================
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Complaint, CaseTimelineEvent, SLAPolicy
from .triage import classify_complaint
from accounts.crypto import encrypt_identity


class SLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAPolicy
        fields = ("id", "cell", "category", "urgency", "deadline_hours")


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
    is_overdue = serializers.SerializerMethodField()
    sla_hours_remaining = serializers.SerializerMethodField()
    duplicate_of = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = (
            "id", "tracking_id", "title", "category", "status", "urgency", "cell",
            "institution_name", "state", "routing_confidence", "needs_human_review",
            "triage_method", "triage_reasons", "is_duplicate_flagged", "duplicate_of",
            "sla_deadline", "is_escalated", "sla_breached", "is_overdue", "sla_hours_remaining",
            "assigned_to", "source_channel", "language", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_institution_name(self, obj):
        if obj.institution:
            return obj.institution.name
        return obj.institution_name_text or "Unknown"

    def get_sla_breached(self, obj):
        return obj.is_sla_breached

    def get_is_overdue(self, obj):
        return obj.is_overdue

    def get_sla_hours_remaining(self, obj):
        return obj.sla_hours_remaining

    def get_duplicate_of(self, obj):
        if obj.duplicate_family:
            return obj.duplicate_family.tracking_id
        return None


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer — includes timeline but NOT decrypted identity."""
    institution_name = serializers.SerializerMethodField()
    sla_breached = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    sla_hours_remaining = serializers.SerializerMethodField()
    duplicate_of = serializers.SerializerMethodField()
    timeline = CaseTimelineEventSerializer(source="timeline_events", many=True, read_only=True)
    assigned_to_username = serializers.SerializerMethodField()
    evidence_count = serializers.SerializerMethodField()
    complainant_encrypted_display = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = (
            "id", "tracking_id", "title", "description", "category", "status",
            "urgency", "cell", "institution", "institution_name", "state",
            "routing_confidence", "needs_human_review", "triage_method", "triage_reasons",
            "is_duplicate_flagged", "duplicate_of", "sla_deadline", "sla_breached",
            "is_escalated", "is_overdue", "sla_hours_remaining", "assigned_to", "assigned_to_username",
            "source_channel", "language", "is_anonymous", "complainant_encrypted_display",
            "evidence_references", "evidence_count", "timeline", "created_at",
            "updated_at", "resolved_at",
        )
        read_only_fields = fields

    def get_institution_name(self, obj):
        return obj.institution.name if obj.institution else obj.institution_name_text or "Unknown"

    def get_sla_breached(self, obj):
        return obj.is_sla_breached

    def get_is_overdue(self, obj):
        return obj.is_overdue

    def get_sla_hours_remaining(self, obj):
        return obj.sla_hours_remaining

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
    """Intake serializer — encrypts identity before storage and executes explainable triage."""
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

        # Perform multilingual explainable triage
        title = validated_data["title"]
        desc = validated_data["description"]
        lang = validated_data.get("language", "en")
        user_cat = validated_data.get("category", "OTHER")

        triage_res = classify_complaint(title, desc, language=lang)

        # If user explicitly selected a non-OTHER category and automated triage was uncertain/OTHER,
        # prioritize user category; otherwise use automated triage result
        if user_cat != "OTHER" and triage_res["category"] == "OTHER":
            route_map = {
                "RAGGING": ("ANTI_RAGGING", "CRITICAL"),
                "SEXUAL_HARASSMENT": ("ICC", "CRITICAL"),
                "FEE_REFUND": ("PGRC", "HIGH"),
                "CERTIFICATE_WITHHOLDING": ("PGRC", "MEDIUM"),
                "SCHOLARSHIP_ISSUE": ("SCHOLARSHIP", "MEDIUM"),
                "APPROVAL_VIOLATION": ("RB", "HIGH"),
                "FACULTY_ISSUE": ("RB", "MEDIUM"),
                "INFRASTRUCTURE": ("RB", "LOW"),
                "ADMISSION_IRREGULARITY": ("RB", "HIGH"),
            }
            cell, urgency = route_map.get(user_cat, ("PGRC", "MEDIUM"))
            assigned_cat = user_cat
            confidence = 100
            reasons = [f"User selected category '{user_cat}'. Destination cell {cell} assigned per standard routing rules."]
            needs_review = False
        else:
            assigned_cat = triage_res["category"]
            cell = triage_res["destination_cell"]
            urgency = triage_res["priority"]
            confidence = triage_res["confidence_score"]
            reasons = triage_res["reasons"]
            needs_review = triage_res["needs_human_review"]

        complaint = Complaint(
            title=title,
            description=desc,
            category=assigned_cat,
            language=triage_res.get("language_detected", lang),
            source_channel=validated_data.get("source_channel", "WEB_PORTAL"),
            state=validated_data.get("state", ""),
            institution=institution,
            institution_name_text=inst_name if not institution else "",
            complainant_encrypted=ciphertext,
            complainant_nonce=nonce,
            is_anonymous=is_anon,
            cell=cell,
            urgency=urgency,
            routing_confidence=confidence,
            needs_human_review=needs_review,
            triage_reasons=reasons,
            triage_method=triage_res["triage_method"],
            evidence_references=validated_data.get("evidence_references", []),
        )

        # Calculate SLA deadline
        hours = SLAPolicy.get_deadline_hours(cell, urgency, assigned_cat)
        complaint.sla_deadline = timezone.now() + timezone.timedelta(hours=hours)
        complaint.save()

        # Create submission timeline event
        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.SUBMISSION,
            action="Complaint Submitted",
            detail=f"Complaint received via {complaint.get_source_channel_display()}",
            actor_label="System",
        )

        # Create triage timeline event with explainability
        reasons_summary = "; ".join(reasons[:2])
        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.TRIAGE,
            action=f"Auto-Triage ({assigned_cat})",
            detail=f"Confidence: {confidence}%. Cell: {cell}. Urgency: {urgency}. Reasons: {reasons_summary}",
            actor_label="Triage Engine",
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


class HumanOverrideSerializer(serializers.Serializer):
    """Auditable human override for triage, cell, category, urgency, or SLA."""
    field = serializers.ChoiceField(
        choices=["category", "urgency", "cell", "sla_deadline", "approve_triage"]
    )
    value = serializers.CharField(required=False, default="", allow_blank=True)
    reason = serializers.CharField(min_length=5, max_length=1000, required=True)


class DuplicateLinkSerializer(serializers.Serializer):
    """Confirm and link a duplicate complaint (never auto-merged)."""
    canonical_id = serializers.CharField(required=True)
    confirm = serializers.BooleanField(required=True)
    reason = serializers.CharField(min_length=5, max_length=1000, required=True)

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("Officer confirmation is required to link duplicate cases.")
        return value


class DuplicateDismissSerializer(serializers.Serializer):
    """Dismiss a false-positive duplicate candidate."""
    candidate_id = serializers.CharField(required=True)
    reason = serializers.CharField(min_length=5, max_length=1000, required=True)


class TriagePreviewSerializer(serializers.Serializer):
    """Preview explainable multilingual triage without saving."""
    title = serializers.CharField(max_length=500)
    description = serializers.CharField()
    language = serializers.ChoiceField(choices=Complaint.Language.choices, required=False, default="en")


class CSVImportSerializer(serializers.Serializer):
    """Validate CSV import file."""
    csv_file = serializers.FileField()
