"""
NIRIKSHAN 360 — Institution Models
====================================
Institution profiles and norm-check results with stored evidence.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Institution(models.Model):
    """An AICTE-approved institution."""

    class InstitutionType(models.TextChoices):
        ENGINEERING = "ENGINEERING", "Engineering"
        PHARMACY = "PHARMACY", "Pharmacy"
        MANAGEMENT = "MANAGEMENT", "Management"
        ARCHITECTURE = "ARCHITECTURE", "Architecture"
        APPLIED_ARTS = "APPLIED_ARTS", "Applied Arts"

    class NormStatus(models.TextChoices):
        COMPLIANT = "COMPLIANT", "Compliant"
        PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT", "Partially Compliant"
        NON_COMPLIANT = "NON_COMPLIANT", "Non-Compliant"
        INSUFFICIENT_DATA = "INSUFFICIENT_DATA", "Insufficient Data"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    aicte_id = models.CharField(max_length=50, unique=True, help_text="AICTE permanent ID")
    state = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=100)
    institution_type = models.CharField(
        max_length=20, choices=InstitutionType.choices, default=InstitutionType.ENGINEERING,
    )
    student_count = models.PositiveIntegerField(default=0)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    compliance_score = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Compliance review signal 0-100. Not a verdict—requires human review.",
    )
    norm_check_status = models.CharField(
        max_length=25, choices=NormStatus.choices, default=NormStatus.INSUFFICIENT_DATA,
    )
    last_inspection = models.DateField(null=True, blank=True)
    nodal_officer = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="institutions", limit_choices_to={"role": "NODAL_OFFICER"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.aicte_id})"


class NormCheckResult(models.Model):
    """A single norm-check finding for an institution supported by a stored evidence record."""

    class Status(models.TextChoices):
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"
        INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE", "Insufficient Evidence"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"

    class Finding(models.TextChoices):
        SUPPORTED = "SUPPORTED", "Supported"
        CONTRADICTED = "CONTRADICTED", "Contradicted"
        INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE", "Insufficient Evidence"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="norm_checks",
    )
    norm = models.CharField(max_length=200, help_text="Name of the norm being checked")
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=25, choices=Status.choices)
    finding = models.CharField(
        max_length=25, choices=Finding.choices, default=Finding.INSUFFICIENT_EVIDENCE,
        help_text="Evidence verdict: SUPPORTED, CONTRADICTED, or INSUFFICIENT_EVIDENCE",
    )
    detail = models.TextField(help_text="Explanation of finding")
    source = models.CharField(max_length=300, help_text="Regulatory source reference")
    source_url = models.CharField(max_length=500, blank=True, default="", help_text="Source URL of evidence record")
    verified_at = models.DateTimeField(null=True, blank=True, help_text="Verification/retrieval timestamp")
    excerpt = models.TextField(blank=True, default="", help_text="Relevant excerpt from disclosure record")
    field_name = models.CharField(max_length=150, blank=True, default="")
    reported_value = models.CharField(max_length=150, blank=True, default="")
    required_norm = models.CharField(max_length=150, blank=True, default="")
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
    )

    class Meta:
        ordering = ["-checked_at"]

    def __str__(self):
        return f"{self.institution.name}: {self.norm} — {self.finding}"


class InstitutionReply(models.Model):
    """Institution's right-of-reply to a complaint."""

    class ReviewStatus(models.TextChoices):
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(
        "complaints.Complaint", on_delete=models.CASCADE, related_name="institution_replies",
    )
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="replies",
    )
    submitted_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True,
        limit_choices_to={"role": "NODAL_OFFICER"},
    )
    content = models.TextField()
    status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING_REVIEW,
    )
    reviewed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_replies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Institution replies"

    def __str__(self):
        return f"Reply to {self.complaint_id} by {self.institution.name}"
