"""
NIRIKSHAN 360 — Complaint Views
===================================
All endpoints enforce JWT authentication and role-based permissions.
Includes explainable triage, duplicate candidate detection & linking,
case graph relationship retrieval, and auditable human overrides.
"""

import csv
import io
import logging
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from rest_framework import generics, permissions, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from accounts.permissions import (
    CanSubmitComplaint, CanViewComplaint, CanAssignComplaint,
    CanEscalate, IsAnalystOrAbove,
)
from audit.models import AuditEvent
from .models import Complaint, CaseTimelineEvent, SLAPolicy
from .serializers import (
    ComplaintListSerializer, ComplaintDetailSerializer, ComplaintCreateSerializer,
    ComplaintAssignSerializer, ComplaintStatusSerializer, CSVImportSerializer,
    SLAPolicySerializer, CaseTimelineEventSerializer, HumanOverrideSerializer,
    DuplicateLinkSerializer, DuplicateDismissSerializer, TriagePreviewSerializer,
)
from .duplicates import find_possible_duplicates
from .graph import get_case_graph
from .triage import classify_complaint

logger = logging.getLogger(__name__)


def resolve_complaint(pk_or_tracking_id, qs=None):
    """Safely resolve a complaint by either UUID pk or human-readable tracking_id."""
    if qs is None:
        qs = Complaint.objects
    try:
        return qs.get(pk=pk_or_tracking_id)
    except (Complaint.DoesNotExist, ValueError, ValidationError):
        try:
            return qs.get(tracking_id=pk_or_tracking_id)
        except (Complaint.DoesNotExist, ValueError):
            raise NotFound(f"Complaint '{pk_or_tracking_id}' not found.")


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
    """POST /api/complaints/ — intake endpoint. Encrypts identity and performs explainable triage."""
    serializer_class = ComplaintCreateSerializer
    permission_classes = [CanSubmitComplaint]

    def perform_create(self, serializer):
        complaint = serializer.save()
        AuditEvent.log(
            AuditEvent.Action.COMPLAINT_CREATE,
            request=self.request,
            target_type="Complaint",
            target_id=complaint.tracking_id,
            detail=f"Complaint '{complaint.title}' submitted via {complaint.source_channel}. Auto-triaged as {complaint.category}.",
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
    """GET /api/complaints/<id>/ — full detail with timeline and triage explainability."""
    serializer_class = ComplaintDetailSerializer
    permission_classes = [CanViewComplaint]
    lookup_field = "pk"

    def get_queryset(self):
        return Complaint.objects.select_related(
            "institution", "assigned_to", "duplicate_family"
        ).prefetch_related("timeline_events")

    def get_object(self):
        pk = self.kwargs["pk"]
        obj = resolve_complaint(pk, qs=self.get_queryset())
        self.check_object_permissions(self.request, obj)
        return obj


class ComplaintAssignView(views.APIView):
    """POST /api/complaints/<pk>/assign/ — assign to an analyst."""
    permission_classes = [CanAssignComplaint]

    def post(self, request, pk):
        complaint = resolve_complaint(pk)
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
        complaint = resolve_complaint(pk)
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
    """
    GET /api/complaints/<pk>/duplicates/ — find possible-duplicate candidates
    with explainable similarity breakdown and officer confirmation required.
    """
    permission_classes = [IsAnalystOrAbove]

    def get(self, request, pk):
        complaint = resolve_complaint(pk)
        candidates_data = find_possible_duplicates(complaint)
        formatted = []
        for item in candidates_data:
            formatted.append({
                "complaint": ComplaintListSerializer(item["candidate"]).data,
                "candidate_id": item["candidate_id"],
                "similarity_score": item["similarity_score"],
                "similarity_explanation": item["explanation"],
                "explanation": item["explanation"],
            })

        return Response({
            "complaint": complaint.tracking_id,
            "candidates": formatted,
            "policy": "Never auto-merge cases. Officer confirmation required before linking.",
        })


class ComplaintDuplicateLinkView(views.APIView):
    """
    POST /api/complaints/<pk>/link-duplicate/ — officer confirms and links duplicate case.
    NEVER auto-merges or deletes cases.
    """
    permission_classes = [IsAnalystOrAbove]

    def post(self, request, pk):
        complaint = resolve_complaint(pk)
        serializer = DuplicateLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        canonical_id = serializer.validated_data["canonical_id"]
        reason = serializer.validated_data["reason"]

        canonical = resolve_complaint(canonical_id)

        if canonical.pk == complaint.pk:
            return Response({"error": "Cannot link a complaint as a duplicate of itself."}, status=400)

        complaint.duplicate_family = canonical
        complaint.is_duplicate_flagged = True
        complaint.save()

        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.DUPLICATE,
            action=f"Duplicate Linked to {canonical.tracking_id}",
            detail=f"Confirmed duplicate by officer {request.user.username}. Reason: {reason}",
            actor=request.user,
            actor_label=request.user.username,
        )

        AuditEvent.log(
            AuditEvent.Action.DUPLICATE_LINK, request=request,
            target_type="Complaint", target_id=complaint.tracking_id,
            detail=f"Linked as duplicate of {canonical.tracking_id} by {request.user.username}. Reason: {reason}",
        )

        return Response({
            "message": f"Successfully linked {complaint.tracking_id} to canonical case {canonical.tracking_id}.",
            "complaint": ComplaintDetailSerializer(complaint).data,
        })


class ComplaintDuplicateDismissView(views.APIView):
    """
    POST /api/complaints/<pk>/dismiss-duplicate/ — officer dismisses false-positive candidate.
    """
    permission_classes = [IsAnalystOrAbove]

    def post(self, request, pk):
        complaint = resolve_complaint(pk)
        serializer = DuplicateDismissSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cand_id = serializer.validated_data["candidate_id"]
        reason = serializer.validated_data["reason"]

        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.NOTE,
            action=f"Duplicate Candidate Dismissed ({cand_id})",
            detail=f"Candidate dismissed as false positive. Reason: {reason}",
            actor=request.user,
            actor_label=request.user.username,
        )

        AuditEvent.log(
            AuditEvent.Action.DUPLICATE_DISMISS, request=request,
            target_type="Complaint", target_id=complaint.tracking_id,
            detail=f"Candidate {cand_id} dismissed as false-positive duplicate. Reason: {reason}",
        )

        return Response({
            "message": f"Candidate {cand_id} dismissed as false positive.",
            "complaint": ComplaintDetailSerializer(complaint).data,
        })


class ComplaintHumanOverrideView(views.APIView):
    """
    POST /api/complaints/<pk>/override/ — auditable human override for triage,
    category, urgency, cell, or SLA deadline with required justification.
    """
    permission_classes = [IsAnalystOrAbove]

    def post(self, request, pk):
        complaint = resolve_complaint(pk)
        serializer = HumanOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        field = serializer.validated_data["field"]
        value = serializer.validated_data.get("value", "").strip()
        reason = serializer.validated_data["reason"]

        old_val = ""
        new_val = value

        if field == "approve_triage":
            old_val = f"needs_human_review={complaint.needs_human_review}"
            complaint.needs_human_review = False
            new_val = "needs_human_review=False"
            if complaint.status == Complaint.Status.SUBMITTED:
                complaint.status = Complaint.Status.ROUTED
        elif field == "category":
            if value not in dict(Complaint.Category.choices):
                return Response({"error": f"Invalid category '{value}'"}, status=400)
            old_val = complaint.category
            complaint.category = value
            complaint.needs_human_review = False
            hours = SLAPolicy.get_deadline_hours(complaint.cell, complaint.urgency, complaint.category)
            complaint.sla_deadline = timezone.now() + timezone.timedelta(hours=hours)
        elif field == "urgency":
            if value not in dict(SLAPolicy.Urgency.choices):
                return Response({"error": f"Invalid urgency '{value}'"}, status=400)
            old_val = complaint.urgency
            complaint.urgency = value
            hours = SLAPolicy.get_deadline_hours(complaint.cell, complaint.urgency, complaint.category)
            complaint.sla_deadline = timezone.now() + timezone.timedelta(hours=hours)
        elif field == "cell":
            if value not in dict(SLAPolicy.Cell.choices):
                return Response({"error": f"Invalid cell '{value}'"}, status=400)
            old_val = complaint.cell
            complaint.cell = value
            hours = SLAPolicy.get_deadline_hours(complaint.cell, complaint.urgency, complaint.category)
            complaint.sla_deadline = timezone.now() + timezone.timedelta(hours=hours)
        elif field == "sla_deadline":
            dt = parse_datetime(value)
            if not dt:
                return Response({"error": "Invalid datetime format. Expected ISO-8601 string."}, status=400)
            old_val = str(complaint.sla_deadline)
            complaint.sla_deadline = dt

        complaint.save()

        # Create Timeline Event
        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.OVERRIDE,
            action=f"Human Override: {field}",
            detail=f"Updated {field} from '{old_val}' to '{new_val}'. Reason: {reason}",
            actor=request.user,
            actor_label=request.user.username,
        )

        # Log immutable Audit Entry
        AuditEvent.log(
            AuditEvent.Action.OVERRIDE, request=request,
            target_type="Complaint", target_id=complaint.tracking_id,
            detail=f"Human override on {field}: '{old_val}' → '{new_val}'. Reason: {reason}",
        )

        return Response({
            "message": f"Successfully updated {field}.",
            "complaint": ComplaintDetailSerializer(complaint).data,
        })


def _supervisor(user):
    return user.is_authenticated and user.role in ("ADMIN", "BUREAU_HEAD")


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def systemic_pulse_analysis(request):
    """Return explainable operational anomalies for the management dashboard."""
    qs = Complaint.objects.all()
    total = qs.count()
    unreviewed = qs.filter(needs_human_review=True).count()
    ratio = (unreviewed / total) if total else 0
    anomalies = []
    if total and ratio > 0.15:
        anomalies.append(
            {
                "rule": "Internal Process Bottleneck",
                "confidence_percentage": round(min(100, ratio * 100), 1),
                "current_count": unreviewed,
                "total_count": total,
                "details": (
                    f"{unreviewed} of {total} cases ({ratio:.1%}) remain unreviewed, "
                    "exceeding the 15% operational threshold."
                ),
                "action": "Review pending triage cases",
            }
        )
    return Response(
        {
            "rule": "unreviewed_cases / total_cases > 15%",
            "supporting_counts": {"total_cases": total, "unreviewed_cases": unreviewed},
            "confidence_parameters": {
                "unreviewed_ratio": round(ratio, 4),
                "threshold": 0.15,
                "sample_size": total,
            },
            "anomalies": anomalies,
        }
    )


@api_view(["POST"])
@permission_classes([IsAnalystOrAbove])
def csv_import_handler(request):
    """Validate a historic RB/PGRC CSV and return a non-destructive preview."""
    upload = request.FILES.get("csv_file")
    if not upload:
        return Response({"detail": "csv_file is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        decoded = upload.read().decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(decoded)))
    except (UnicodeDecodeError, csv.Error) as exc:
        logger.warning("CSV import rejected: %s", exc)
        return Response({"detail": "CSV must be valid UTF-8 data."}, status=status.HTTP_400_BAD_REQUEST)

    aliases = {
        "case_id": ("case_id", "complaint_id", "tracking_id"),
        "title": ("title", "subject", "issue"),
        "description": ("description", "details", "complaint"),
        "category": ("category", "issue_category", "cell"),
        "institution": ("institution", "institution_name", "college"),
    }
    existing_text = set(Complaint.objects.values_list("title", "description"))
    preview = []
    for row_number, row in enumerate(rows, start=2):
        mapped = {
            field: next((row.get(key, "").strip() for key in keys if row.get(key)), "")
            for field, keys in aliases.items()
        }
        errors = []
        if not mapped["title"]:
            errors.append("title/subject is required")
        if not mapped["description"]:
            errors.append("description/details is required")
        duplicate_warning = (mapped["title"], mapped["description"]) in existing_text
        preview.append(
            {
                "row": row_number,
                "mapped": mapped,
                "valid": not errors,
                "errors": errors,
                "duplicate_warning": duplicate_warning,
            }
        )
    AuditEvent.log(
        AuditEvent.Action.CSV_IMPORT,
        request=request,
        target_type="Bulk Import",
        detail=f"Previewed {len(preview)} historic RB/PGRC rows.",
    )
    return Response({"label": "DEMO DATA ACTIVE", "preview": preview, "created": 0})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def override_triage_decision(request, pk):
    """Allow only supervisors to change triage category or priority."""
    if not _supervisor(request.user):
        return Response({"detail": "Supervisor role required."}, status=status.HTTP_403_FORBIDDEN)
    complaint = resolve_complaint(pk)
    field = request.data.get("field")
    value = str(request.data.get("value", "")).strip()
    justification = str(request.data.get("justification_explanation", "")).strip()
    if field not in ("category", "priority", "urgency") or not value:
        return Response({"detail": "field and value are required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(justification) < 5:
        return Response({"detail": "justification_explanation is required."}, status=status.HTTP_400_BAD_REQUEST)
    if field == "category" and value not in dict(Complaint.Category.choices):
        return Response({"detail": "Invalid category."}, status=status.HTTP_400_BAD_REQUEST)
    if field in ("priority", "urgency") and value not in dict(SLAPolicy.Urgency.choices):
        return Response({"detail": "Invalid priority."}, status=status.HTTP_400_BAD_REQUEST)
    old_value = complaint.category if field == "category" else complaint.urgency
    if field == "category":
        complaint.category = value
    else:
        complaint.urgency = value
    complaint.needs_human_review = False
    complaint.save(update_fields=["category", "urgency", "needs_human_review", "updated_at"])
    AuditEvent.log(
        AuditEvent.Action.OVERRIDE,
        request=request,
        target_type="Complaint",
        target_id=complaint.tracking_id,
        detail=f"Triage {field} changed from '{old_value}' to '{value}'. Justification: {justification}",
    )
    return Response({"message": "Triage decision overridden.", "complaint": ComplaintDetailSerializer(complaint).data})


class CaseGraphView(views.APIView):
    """
    GET /api/complaints/graph/ — case graph relationships with labeled edges.
    Connects to Neo4j if configured; falls back seamlessly to PostgreSQL.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        complaint_id = request.query_params.get("complaint_id")
        institution_id = request.query_params.get("institution_id")
        graph_data = get_case_graph(complaint_id=complaint_id, institution_id=institution_id)
        return Response(graph_data)


class TriagePreviewView(views.APIView):
    """
    POST /api/complaints/triage-preview/ — interactive explainable multilingual triage preview.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TriagePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.validated_data["title"]
        desc = serializer.validated_data["description"]
        lang = serializer.validated_data.get("language", "en")
        result = classify_complaint(title, desc, language=lang)
        return Response(result)


class CheckEscalationsView(views.APIView):
    """
    POST /api/complaints/check-escalations/ — check for overdue cases and auto-escalate.
    """
    permission_classes = [IsAnalystOrAbove]

    def post(self, request):
        overdue_qs = Complaint.objects.filter(
            sla_deadline__lt=timezone.now(),
            is_escalated=False,
        ).exclude(status__in=[Complaint.Status.RESOLVED, Complaint.Status.CLOSED])
        escalated_ids = []
        for c in overdue_qs:
            if c.escalate_if_overdue(request=request):
                escalated_ids.append(c.tracking_id)
                CaseTimelineEvent.objects.create(
                    complaint=c,
                    event_type=CaseTimelineEvent.EventType.ESCALATION,
                    action="SLA Breach — Auto-Escalated",
                    detail="SLA deadline exceeded; case escalated to Bureau Head.",
                    actor_label="SLA Monitor",
                )

        return Response({
            "escalated_count": len(escalated_ids),
            "escalated_cases": escalated_ids,
        })


class ComplaintTimelineView(generics.ListAPIView):
    """GET /api/complaints/<pk>/timeline/ — case journey events."""
    serializer_class = CaseTimelineEventSerializer
    permission_classes = [CanViewComplaint]
    pagination_class = None

    def get_queryset(self):
        pk = self.kwargs["pk"]
        complaint = resolve_complaint(pk)
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
        for i, row in enumerate(reader, start=2):
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
    """GET/POST /api/complaints/sla-policies/ — configurable SLA deadlines."""
    serializer_class = SLAPolicySerializer
    queryset = SLAPolicy.objects.all()
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated()]
        return [IsAnalystOrAbove()]
