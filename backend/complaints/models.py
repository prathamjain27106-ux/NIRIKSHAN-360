"""
NIRIKSHAN 360 — Complaint Models
===================================
Full complaint lifecycle: intake → triage → routing → review → resolution.
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


def generate_tracking_id():
    """Generate a unique tracking ID like NIR-2026-00042."""
    year = timezone.now().year
    # Get the next sequence number
    last = Complaint.objects.order_by("-sequence").first()
    seq = (last.sequence + 1) if last else 1
    return f"NIR-{year}-{seq:05d}"


class SLAPolicy(models.Model):
    """Configurable SLA deadline rules per cell/urgency combination.
    These are prototype defaults, NOT official AICTE deadlines."""

    class Cell(models.TextChoices):
        RB = "RB", "Regulation Bureau"
        PGRC = "PGRC", "Public Grievance Redressal Cell"
        ANTI_RAGGING = "ANTI_RAGGING", "Anti-Ragging Cell"
        ICC = "ICC", "Internal Complaints Committee"
        SCHOLARSHIP = "SCHOLARSHIP", "Scholarship Cell"

    class Urgency(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    cell = models.CharField(max_length=20, choices=Cell.choices)
    urgency = models.CharField(max_length=10, choices=Urgency.choices)
    deadline_hours = models.PositiveIntegerField(
        help_text="Hours from submission until SLA breach. Configurable, NOT an official AICTE deadline.",
    )

    class Meta:
        unique_together = ("cell", "urgency")
        verbose_name = "SLA Policy"
        verbose_name_plural = "SLA Policies"

    def __str__(self):
        return f"{self.cell}/{self.urgency}: {self.deadline_hours}h"


class Complaint(models.Model):
    """A complaint case filed against an AICTE-approved institution."""

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        TRIAGED = "TRIAGED", "Triaged"
        ROUTED = "ROUTED", "Routed"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        AWAITING_REPLY = "AWAITING_REPLY", "Awaiting Reply"
        RESOLVED = "RESOLVED", "Resolved"
        ESCALATED = "ESCALATED", "Escalated"
        CLOSED = "CLOSED", "Closed"

    class Category(models.TextChoices):
        FEE_REFUND = "FEE_REFUND", "Fee Refund"
        CERTIFICATE_WITHHOLDING = "CERTIFICATE_WITHHOLDING", "Certificate Withholding"
        RAGGING = "RAGGING", "Ragging"
        SEXUAL_HARASSMENT = "SEXUAL_HARASSMENT", "Sexual Harassment"
        SCHOLARSHIP_ISSUE = "SCHOLARSHIP_ISSUE", "Scholarship Issue"
        APPROVAL_VIOLATION = "APPROVAL_VIOLATION", "Approval Violation"
        FACULTY_ISSUE = "FACULTY_ISSUE", "Faculty Issue"
        INFRASTRUCTURE = "INFRASTRUCTURE", "Infrastructure"
        ADMISSION_IRREGULARITY = "ADMISSION_IRREGULARITY", "Admission Irregularity"
        OTHER = "OTHER", "Other"

    class SourceChannel(models.TextChoices):
        WEB_PORTAL = "WEB_PORTAL", "Web Portal"
        EMAIL = "EMAIL", "Email"
        CSV_IMPORT = "CSV_IMPORT", "CSV Import"
        PHONE = "PHONE", "Phone"
        WALK_IN = "WALK_IN", "Walk-in"

    class Language(models.TextChoices):
        EN = "en", "English"
        HI = "hi", "Hindi"
        HINGLISH = "hinglish", "Hinglish"

    # Tracking
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracking_id = models.CharField(max_length=20, unique=True, db_index=True)
    sequence = models.PositiveIntegerField(unique=True)

    # Content
    title = models.CharField(max_length=500)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.EN)
    source_channel = models.CharField(
        max_length=20, choices=SourceChannel.choices, default=SourceChannel.WEB_PORTAL,
    )

    # Identity — NEVER plaintext. Encrypted with AES-GCM.
    complainant_encrypted = models.BinaryField(
        help_text="AES-GCM encrypted complainant identity. Never stored in plaintext.",
    )
    complainant_nonce = models.BinaryField(
        help_text="AES-GCM nonce for decryption.", null=True, blank=True,
    )
    is_anonymous = models.BooleanField(
        default=False, help_text="Whether complainant chose anonymous mode.",
    )

    # Institution
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="complaints",
    )
    institution_name_text = models.CharField(
        max_length=300, blank=True, default="",
        help_text="Free-text institution name if not matched to an Institution record.",
    )
    state = models.CharField(max_length=100, db_index=True, blank=True, default="")

    # Triage & Routing
    urgency = models.CharField(
        max_length=10, choices=SLAPolicy.Urgency.choices, default=SLAPolicy.Urgency.MEDIUM,
    )
    cell = models.CharField(
        max_length=20, choices=SLAPolicy.Cell.choices, blank=True, default="",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED, db_index=True,
    )
    routing_confidence = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0-100 confidence of automated routing.",
    )
    needs_human_review = models.BooleanField(default=True)

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assigned_complaints",
    )

    # SLA
    sla_deadline = models.DateTimeField(null=True, blank=True)

    # Duplicate detection (flag only, NEVER auto-merge)
    duplicate_family = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="duplicates",
        help_text="Reference to the canonical complaint if flagged as duplicate. Merge requires human approval.",
    )
    is_duplicate_flagged = models.BooleanField(default=False)

    # Evidence
    evidence_references = models.JSONField(
        default=list, blank=True,
        help_text="List of evidence file references (paths/URLs).",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cell", "status"]),
            models.Index(fields=["urgency", "status"]),
            models.Index(fields=["institution", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.sequence:
            last = Complaint.objects.order_by("-sequence").first()
            self.sequence = (last.sequence + 1) if last else 1
        if not self.tracking_id:
            self.tracking_id = f"NIR-{timezone.now().year}-{self.sequence:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_id}: {self.title[:60]}"

    @property
    def is_sla_breached(self):
        if not self.sla_deadline:
            return False
        if self.status in (self.Status.RESOLVED, self.Status.CLOSED):
            return False
        return timezone.now() > self.sla_deadline


class CaseTimelineEvent(models.Model):
    """An event in the case's journey/timeline."""

    class EventType(models.TextChoices):
        SUBMISSION = "SUBMISSION", "Submission"
        TRIAGE = "TRIAGE", "Triage"
        ROUTING = "ROUTING", "Routing"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        STATUS_CHANGE = "STATUS_CHANGE", "Status Change"
        ESCALATION = "ESCALATION", "Escalation"
        RESOLUTION = "RESOLUTION", "Resolution"
        REPLY = "REPLY", "Institution Reply"
        EVIDENCE = "EVIDENCE", "Evidence Added"
        NOTE = "NOTE", "Internal Note"
        SYSTEM = "SYSTEM", "System Event"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE, related_name="timeline_events",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    action = models.CharField(max_length=200)
    detail = models.TextField(blank=True, default="")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    actor_label = models.CharField(
        max_length=100, blank=True, default="System",
        help_text="Display name of the actor (does not reveal encrypted identities).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.complaint.tracking_id}: {self.action}"
