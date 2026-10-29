"""
NIRIKSHAN 360 — Custom User Model
===================================
Extends Django's AbstractUser with role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with RBAC role field for AICTE bureau/cell access control."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "System Administrator"
        BUREAU_HEAD = "BUREAU_HEAD", "Bureau Head"
        ANALYST = "ANALYST", "Complaint Analyst"
        NODAL_OFFICER = "NODAL_OFFICER", "Institution Nodal Officer"
        AUDITOR = "AUDITOR", "Auditor"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ANALYST,
        help_text="Determines the user's permissions across the platform.",
    )
    cell = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Assigned AICTE cell: RB, PGRC, ANTI_RAGGING, ICC, SCHOLARSHIP, or empty for cross-cell roles.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
