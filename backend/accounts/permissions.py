"""
NIRIKSHAN 360 — Role-Based Permissions
=========================================
Server-side permission enforcement. Never rely on frontend buttons as security.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Only system administrators."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "ADMIN"


class IsAdminOrBureauHead(permissions.BasePermission):
    """Administrators or bureau heads."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("ADMIN", "BUREAU_HEAD")


class IsAnalystOrAbove(permissions.BasePermission):
    """Analysts, bureau heads, or administrators."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "ADMIN", "BUREAU_HEAD", "ANALYST",
        )


class IsAuditorOrAdmin(permissions.BasePermission):
    """Auditors or administrators — for audit log access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("ADMIN", "AUDITOR")


class IsNodalOfficer(permissions.BasePermission):
    """Institution nodal officers only."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "NODAL_OFFICER"


class CanViewComplaint(permissions.BasePermission):
    """All authenticated users can view complaints.
    Object-level: nodal officers can only see complaints about their institution."""
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ("ADMIN", "BUREAU_HEAD", "ANALYST", "AUDITOR"):
            return True
        if user.role == "NODAL_OFFICER":
            # Can only view complaints for their institution
            return (
                hasattr(user, "institutions") and
                obj.institution_id in user.institutions.values_list("id", flat=True)
            )
        return False


class CanSubmitComplaint(permissions.BasePermission):
    """Anyone authenticated can submit a complaint."""
    def has_permission(self, request, view):
        return request.user.is_authenticated


class CanAssignComplaint(permissions.BasePermission):
    """Only admin, bureau head, or analyst can assign complaints."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            "ADMIN", "BUREAU_HEAD", "ANALYST",
        )


class CanEscalate(permissions.BasePermission):
    """Only admin or bureau head can escalate."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("ADMIN", "BUREAU_HEAD")


class ReadOnly(permissions.BasePermission):
    """Allow any authenticated user read-only access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method in permissions.SAFE_METHODS
