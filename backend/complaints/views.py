"""
NIRIKSHAN 360 — Complaint Views
===================================
All endpoints enforce JWT authentication and role-based permissions.
"""

import csv
import io
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from accounts.permissions import (
    CanSubmitComplaint, CanViewComplaint, CanAssignComplaint,
    CanEscalate, IsAnalystOrAbove,
)
from audit.models import AuditEvent
from .models import Complaint, CaseTimelineEvent, SLAPolicy
from .serializers import (
    ComplaintListSerializer, ComplaintDetailSerializer, ComplaintCreateSerializer,
    ComplaintAssignSerializer, ComplaintStatusSerializer, CSVImportSerializer,
    SLAPolicySerializer, CaseTimelineEventSerializer,
)


class ComplaintListView(generics.ListAPIView):
    """GET /api/complaints/ — paginated, filterable list of complaints."""
    serializer_class = ComplaintListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Complaint.objects.select_related("institution", "assigned_to", "duplicate_family")
        user = self.request.user

        # Nodal officers only see complaints for their institutions
        if user.role == "NODAL_OFFICER":
            inst_ids = user.institutions.values_list("id", flat=True)
            qs = qs.filter(institution_id__in=inst_ids)

        # Filters
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("urgency"):
            qs = qs.filter(urgency=params["urgency"])
        if params.get("cell"):
            qs = qs.filter(cell=params["cell"])
        if params.get("state"):
            qs = qs.filter(state__icontains=params["state"])
        if params.get("institution"):
            qs = qs.filter(institution_id=params["institution"])
        if params.get("category"):
            qs = qs.filter(category=params["category"])
        if params.get("needs_review"):
            qs = qs.filter(needs_human_review=True)
        if params.get("sla_breached"):
            qs = qs.filter(sla_deadline__lt=timezone.now()).exclude(
                status__in=["RESOLVED", "CLOSED"]
            )
        if params.get("search"):
            term = params["search"]
            qs = qs.filter(
                Q(tracking_id__icontains=term) |
                Q(title__icontains=term) |
                Q(description__icontains=term)
            )
        return qs


class ComplaintCreateView(generics.CreateAPIView):
    """POST /api/complaints/ — intake endpoint. Encrypts identity."""
    serializer_class = ComplaintCreateSerializer
    permission_classes = [CanSubmitComplaint]

    def perform_create(self, serializer):
        complaint = serializer.save()
        AuditEvent.log(
            AuditEvent.Action.COMPLAINT_CREATE,
            request=self.request,
            target_type="Complaint",
            target_id=complaint.tracking_id,
            detail=f"Complaint '{complaint.title}' submitted via {complaint.source_channel}",
        )
        return complaint

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint = self.perform_create(serializer)
        return Response(
            ComplaintDetailSerializer(complaint).data,
            status=status.HTTP_201_CREATED,
        )


class ComplaintDetailView(generics.RetrieveAPIView):
    """GET /api/complaints/<id>/ — full detail with timeline."""
    serializer_class = ComplaintDetailSerializer
    permission_classes = [CanViewComplaint]
    lookup_field = "pk"

    def get_queryset(self):
        return Complaint.objects.select_related(
            "institution", "assigned_to", "duplicate_family"
        ).prefetch_related("timeline_events")

    def get_object(self):
        # Support lookup by UUID or tracking_id
        pk = self.kwargs["pk"]
        qs = self.get_queryset()
        try:
            obj = qs.get(pk=pk)
        except (Complaint.DoesNotExist, ValueError):
            obj = qs.get(tracking_id=pk)
        self.check_object_permissions(self.request, obj)
        return obj


class ComplaintAssignView(views.APIView):
    """POST /api/complaints/<pk>/assign/ — assign to an analyst."""
    permission_classes = [CanAssignComplaint]

    def post(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except (Complaint.DoesNotExist, ValueError):
            try:
                complaint = Complaint.objects.get(tracking_id=pk)
            except Complaint.DoesNotExist:
                return Response({"error": "Complaint not found"}, status=404)

        serializer = ComplaintAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from accounts.models import User
        assignee = User.objects.get(pk=serializer.validated_data["assigned_to"])
        complaint.assigned_to = assignee
        if complaint.status == Complaint.Status.SUBMITTED:
            complaint.status = Complaint.Status.TRIAGED
        complaint.save()

        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.ASSIGNMENT,
            action=f"Assigned to {assignee.username}",
            detail=f"Case assigned to {assignee.get_role_display()} {assignee.username}",
            actor=request.user,
            actor_label=request.user.username,
        )
        AuditEvent.log(
            AuditEvent.Action.ASSIGNMENT, request=request,
            target_type="Complaint", target_id=complaint.tracking_id,
            detail=f"Assigned to {assignee.username}",
        )
        return Response(ComplaintDetailSerializer(complaint).data)


class ComplaintStatusUpdateView(views.APIView):
    """POST /api/complaints/<pk>/status/ — update status."""
    permission_classes = [IsAnalystOrAbove]

    def post(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except (Complaint.DoesNotExist, ValueError):
            try:
                complaint = Complaint.objects.get(tracking_id=pk)
            except Complaint.DoesNotExist:
                return Response({"error": "Complaint not found"}, status=404)

        serializer = ComplaintStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = complaint.status
        new_status = serializer.validated_data["status"]
        reason = serializer.validated_data.get("reason", "")
        allowed_transitions = {
            Complaint.Status.SUBMITTED: {
                Complaint.Status.TRIAGED, Complaint.Status.ROUTED,
            },
            Complaint.Status.TRIAGED: {
                Complaint.Status.ROUTED, Complaint.Status.UNDER_REVIEW,
            },
            Complaint.Status.ROUTED: {Complaint.Status.UNDER_REVIEW},
            Complaint.Status.UNDER_REVIEW: {
                Complaint.Status.AWAITING_REPLY, Complaint.Status.RESOLVED,
                Complaint.Status.ESCALATED,
            },
            Complaint.Status.AWAITING_REPLY: {
                Complaint.Status.UNDER_REVIEW, Complaint.Status.RESOLVED,
                Complaint.Status.ESCALATED,
            },
            Complaint.Status.ESCALATED: {
                Complaint.Status.UNDER_REVIEW, Complaint.Status.RESOLVED,
            },
            Complaint.Status.RESOLVED: {Complaint.Status.CLOSED},
            Complaint.Status.CLOSED: set(),
        }
        if new_status != old_status and new_status not in allowed_transitions[old_status]:
            return Response(
                {
                    "status": [
                        f"Cannot change status from {old_status} to {new_status}.",
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        complaint.status = new_status
        if new_status in ("RESOLVED", "CLOSED"):
            complaint.resolved_at = timezone.now()
        complaint.save()

        event_type = (
            CaseTimelineEvent.EventType.ESCALATION if new_status == "ESCALATED"
            else CaseTimelineEvent.EventType.RESOLUTION if new_status in ("RESOLVED", "CLOSED")
            else CaseTimelineEvent.EventType.STATUS_CHANGE
        )
        CaseTimelineEvent.objects.create(
            complaint=complaint, event_type=event_type,
            action=f"Status: {old_status} → {new_status}",
            detail=reason or f"Status changed to {new_status}",
            actor=request.user, actor_label=request.user.username,
        )
        audit_action = (
            AuditEvent.Action.ESCALATION if new_status == "ESCALATED"
            else AuditEvent.Action.RESOLUTION if new_status == "RESOLVED"
            else AuditEvent.Action.STATUS_CHANGE
        )
        AuditEvent.log(
            audit_action, request=request,
            target_type="Complaint", target_id=complaint.tracking_id,
            detail=f"{old_status} → {new_status}. {reason}",
        )
        return Response(ComplaintDetailSerializer(complaint).data)


class ComplaintDuplicatesView(views.APIView):
    """GET /api/complaints/<pk>/duplicates/ — find potential duplicate candidates."""
    permission_classes = [IsAnalystOrAbove]

    def get(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except (Complaint.DoesNotExist, ValueError):
            return Response({"error": "Complaint not found"}, status=404)

        # Simple text-similarity-based duplicate detection
        candidates = Complaint.objects.filter(
            Q(institution=complaint.institution) | Q(institution_name_text=complaint.institution_name_text),
            category=complaint.category,
        ).exclude(pk=complaint.pk).order_by("-created_at")[:10]

        return Response({
            "complaint": complaint.tracking_id,
            "candidates": ComplaintListSerializer(candidates, many=True).data,
        })


class ComplaintTimelineView(generics.ListAPIView):
    """GET /api/complaints/<pk>/timeline/ — case journey events."""
    serializer_class = CaseTimelineEventSerializer
    permission_classes = [CanViewComplaint]
    pagination_class = None

    def get_queryset(self):
        pk = self.kwargs["pk"]
        try:
            complaint = Complaint.objects.get(pk=pk)
        except (Complaint.DoesNotExist, ValueError):
            complaint = Complaint.objects.get(tracking_id=pk)
        return CaseTimelineEvent.objects.filter(complaint=complaint)


class DashboardAnalyticsView(views.APIView):
    """GET /api/complaints/dashboard/ — aggregate metrics."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Complaint.objects.all()
        now = timezone.now()
        thirty_days_ago = now - timezone.timedelta(days=30)

        total = qs.count()
        pending_triage = qs.filter(status="SUBMITTED").count()
        sla_breaches = qs.filter(
            sla_deadline__lt=now
        ).exclude(status__in=["RESOLVED", "CLOSED"]).count()
        resolved_30d = qs.filter(resolved_at__gte=thirty_days_ago).count()

        # Average resolution time
        resolved = qs.filter(resolved_at__isnull=False)
        if resolved.exists():
            from django.db.models import Avg, F
            avg_delta = resolved.annotate(
                delta=F("resolved_at") - F("created_at")
            ).aggregate(avg=Avg("delta"))["avg"]
            avg_days = round(avg_delta.total_seconds() / 86400, 1) if avg_delta else 0
        else:
            avg_days = 0

        # By cell
        by_cell = dict(
            qs.values_list("cell").annotate(c=Count("id")).order_by("cell")
        )

        # By urgency
        by_urgency = dict(
            qs.values_list("urgency").annotate(c=Count("id")).order_by("urgency")
        )
        by_status = dict(
            qs.values_list("status").annotate(c=Count("id")).order_by("status")
        )

        # By state
        by_state = dict(
            qs.exclude(state="").values_list("state").annotate(c=Count("id")).order_by("-c")[:15]
        )

        # Monthly trend (last 6 months)
        monthly = []
        for i in range(5, -1, -1):
            month_start = (now - timezone.timedelta(days=30 * i)).replace(day=1)
            if i > 0:
                month_end = (now - timezone.timedelta(days=30 * (i - 1))).replace(day=1)
            else:
                month_end = now
            received = qs.filter(created_at__gte=month_start, created_at__lt=month_end).count()
            resolved_m = qs.filter(resolved_at__gte=month_start, resolved_at__lt=month_end).count()
            monthly.append({
                "month": month_start.strftime("%b"),
                "received": received,
                "resolved": resolved_m,
            })

        # SLA performance by cell
        sla_perf = []
        for cell_code, _ in SLAPolicy.Cell.choices:
            cell_total = qs.filter(cell=cell_code).count()
            if cell_total == 0:
                continue
            breached = qs.filter(
                cell=cell_code, sla_deadline__lt=now,
            ).exclude(status__in=["RESOLVED", "CLOSED"]).count()
            sla_perf.append({
                "cell": cell_code,
                "within_sla": round((cell_total - breached) / cell_total * 100),
                "breached": round(breached / cell_total * 100),
            })

        return Response({
            "total_complaints": total,
            "pending_triage": pending_triage,
            "sla_breaches": sla_breaches,
            "resolved_30d": resolved_30d,
            "avg_resolution_days": avg_days,
            "complaints_by_cell": by_cell,
            "complaints_by_status": by_status,
            "complaints_by_urgency": by_urgency,
            "state_distribution": by_state,
            "monthly_trend": monthly,
            "sla_performance": sla_perf,
        })


class CSVImportView(views.APIView):
    """POST /api/complaints/import-csv/ — bulk import from CSV."""
    permission_classes = [IsAnalystOrAbove]

    def post(self, request):
        serializer = CSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data["csv_file"]
        decoded = csv_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        created = 0
        errors = []
        for i, row in enumerate(reader, start=2):  # Row 2 onwards (header is row 1)
            try:
                create_ser = ComplaintCreateSerializer(data={
                    "title": row.get("title", ""),
                    "description": row.get("description", ""),
                    "category": row.get("category", "OTHER"),
                    "institution_name": row.get("institution_name", ""),
                    "state": row.get("state", ""),
                    "language": row.get("language", "en"),
                    "source_channel": "CSV_IMPORT",
                    "complainant_name": row.get("complainant_name", ""),
                    "complainant_contact": row.get("complainant_contact", ""),
                })
                if create_ser.is_valid():
                    create_ser.save()
                    created += 1
                else:
                    errors.append({"row": i, "errors": create_ser.errors})
            except Exception as e:
                errors.append({"row": i, "errors": str(e)})

        AuditEvent.log(
            AuditEvent.Action.CSV_IMPORT, request=request,
            target_type="Bulk Import",
            detail=f"CSV import: {created} created, {len(errors)} errors",
        )
        return Response({
            "created": created, "errors": errors,
            "message": f"Imported {created} complaints with {len(errors)} errors.",
        })


class SLAPolicyListView(generics.ListCreateAPIView):
    """GET/POST /api/sla-policies/ — configurable SLA deadlines."""
    serializer_class = SLAPolicySerializer
    queryset = SLAPolicy.objects.all()
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated()]
        return [IsAnalystOrAbove()]
