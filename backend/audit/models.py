"""
NIRIKSHAN 360 — Audit Models
================================
Audit event logging and identity reveal workflow.
"""

import uuid
from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Immutable audit log entry for every consequential system action."""

    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        COMPLAINT_CREATE = "COMPLAINT_CREATE", "Complaint Created"
        TRIAGE = "TRIAGE", "Triage"
        ROUTING = "ROUTING", "Routing"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        STATUS_CHANGE = "STATUS_CHANGE", "Status Change"
        ESCALATION = "ESCALATION", "Escalation"
        RESOLUTION = "RESOLUTION", "Resolution"
        DUPLICATE_FLAG = "DUPLICATE_FLAG", "Duplicate Flag"
        DUPLICATE_LINK = "DUPLICATE_LINK", "Duplicate Linked"
        DUPLICATE_DISMISS = "DUPLICATE_DISMISS", "Duplicate Dismissed"
        OVERRIDE = "OVERRIDE", "Human Override"
        IDENTITY_REVEAL_REQUEST = "IDENTITY_REVEAL_REQUEST", "Identity Reveal Request"
        IDENTITY_REVEAL_APPROVE = "IDENTITY_REVEAL_APPROVE", "Identity Reveal Approved"
        IDENTITY_REVEAL_DENY = "IDENTITY_REVEAL_DENY", "Identity Reveal Denied"
        IDENTITY_REVEALED = "IDENTITY_REVEALED", "Identity Revealed"
        CSV_IMPORT = "CSV_IMPORT", "CSV Import"
        NORM_CHECK = "NORM_CHECK", "Norm Check"
        REPLY_SUBMITTED = "REPLY_SUBMITTED", "Institution Reply Submitted"
        REPLY_REVIEWED = "REPLY_REVIEWED", "Institution Reply Reviewed"
        SYSTEM = "SYSTEM", "System Event"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    actor_username = models.CharField(max_length=150, default="system")
    actor_role = models.CharField(max_length=20, blank=True, default="")
    action = models.CharField(max_length=30, choices=Action.choices)
    target_type = models.CharField(max_length=50, blank=True, default="")
    target_id = models.CharField(max_length=100, blank=True, default="")
    detail = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        # Audit events are append-only; no updates or deletes
        managed = True

    def __str__(self):
        return f"{self.timestamp}: {self.action} by {self.actor_username}"

    @classmethod
    def log(cls, action, request=None, actor=None, target_type="", target_id="", detail=""):
        """Create an audit event. Convenience factory."""
        ip = None
        actor_username = "system"
        actor_role = ""
        if request and hasattr(request, "user") and request.user.is_authenticated:
            actor = request.user
            ip = request.META.get("REMOTE_ADDR")
        if actor:
            actor_username = actor.username
            actor_role = getattr(actor, "role", "")
        return cls.objects.create(
            action=action, actor=actor, actor_username=actor_username,
            actor_role=actor_role, target_type=target_type, target_id=str(target_id),
            detail=detail, ip_address=ip,
        )


class IdentityAccessRequest(models.Model):
    """Two-distinct-approver identity reveal workflow.
    Requires two different authorized users to approve before decryption."""

    class RequestStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved (2 approvals received)"
        DENIED = "DENIED", "Denied"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(
        "complaints.Complaint", on_delete=models.CASCADE,
        related_name="identity_requests",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="identity_requests_made",
    )
    reason = models.TextField(help_text="Justification for identity reveal")
    status = models.CharField(
        max_length=10, choices=RequestStatus.choices, default=RequestStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reveal request for {self.complaint_id} by {self.requester}"

    @property
    def approval_count(self):
        return self.approvals.filter(approved=True).count()

    @property
    def is_fully_approved(self):
        # Require 2 distinct approvers
        return self.approval_count >= 2


class IdentityAccessApproval(models.Model):
    """A single approval/denial for an identity reveal request."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        IdentityAccessRequest, on_delete=models.CASCADE, related_name="approvals",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="identity_approvals_given",
    )
    approved = models.BooleanField()
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("request", "approver")  # Each user can only vote once

    def __str__(self):
        vote = "approved" if self.approved else "denied"
        return f"{self.approver} {vote} reveal for {self.request.complaint_id}"
