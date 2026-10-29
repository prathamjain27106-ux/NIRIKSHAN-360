"""
NIRIKSHAN 360 — Institution Views
=====================================
"""

from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from accounts.permissions import IsAnalystOrAbove, IsNodalOfficer, CanViewComplaint
from audit.models import AuditEvent
from complaints.models import CaseTimelineEvent
from .models import Institution, NormCheckResult, InstitutionReply
from .serializers import (
    InstitutionListSerializer, InstitutionDetailSerializer,
    NormCheckResultSerializer, InstitutionReplySerializer,
    InstitutionReplyCreateSerializer,
)


class InstitutionListView(generics.ListAPIView):
    """GET /api/institutions/ — list with search."""
    serializer_class = InstitutionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Institution.objects.prefetch_related("complaints")
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) | Q(aicte_id__icontains=search) |
                Q(state__icontains=search) | Q(city__icontains=search)
            )
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state__icontains=state)
        inst_type = self.request.query_params.get("type")
        if inst_type:
            qs = qs.filter(institution_type=inst_type)
        return qs


class InstitutionDetailView(generics.RetrieveAPIView):
    """GET /api/institutions/<id>/ — full profile."""
    serializer_class = InstitutionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Institution.objects.all()


class NormCheckListView(generics.ListAPIView):
    """GET /api/institutions/<id>/norm-checks/ — norm-check results."""
    serializer_class = NormCheckResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return NormCheckResult.objects.filter(
            institution_id=self.kwargs["pk"]
        ).select_related("checked_by")


class ComplianceRadarView(views.APIView):
    """GET /api/institutions/<id>/compliance-radar/ — radar data."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            inst = Institution.objects.get(pk=pk)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found"}, status=404)

        norms = NormCheckResult.objects.filter(institution=inst)
        categories = norms.values_list("category", flat=True).distinct()

        dimensions = []
        for cat in categories:
            cat_norms = norms.filter(category=cat)
            total = cat_norms.count()
            passed = cat_norms.filter(status="PASS").count()
            score = round((passed / total) * 100) if total > 0 else 0
            dimensions.append({
                "label": cat,
                "value": score,
                "benchmark": 70,  # Configurable benchmark
            })

        if not dimensions:
            # Default dimensions when no norm checks exist
            dimensions = [
                {"label": "Faculty", "value": inst.compliance_score, "benchmark": 70},
                {"label": "Infrastructure", "value": max(0, inst.compliance_score - 10), "benchmark": 70},
                {"label": "Governance", "value": max(0, inst.compliance_score - 5), "benchmark": 70},
                {"label": "Student Welfare", "value": min(100, inst.compliance_score + 5), "benchmark": 70},
                {"label": "Financial", "value": max(0, inst.compliance_score - 8), "benchmark": 70},
            ]

        return Response({
            "institution_id": str(inst.id),
            "institution_name": inst.name,
            "overall_score": inst.compliance_score,
            "dimensions": dimensions,
        })


class InstitutionReplyListView(generics.ListAPIView):
    """GET /api/institutions/<id>/replies/ — replies for an institution."""
    serializer_class = InstitutionReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InstitutionReply.objects.filter(
            institution_id=self.kwargs["pk"]
        ).select_related("submitted_by", "reviewed_by", "complaint")


class InstitutionReplyCreateView(views.APIView):
    """POST /api/replies/ — submit a right-of-reply (nodal officers only)."""
    permission_classes = [IsNodalOfficer]

    def post(self, request):
        serializer = InstitutionReplyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from complaints.models import Complaint
        complaint = Complaint.objects.get(pk=serializer.validated_data["complaint_id"])

        # Verify the nodal officer is associated with this institution
        if complaint.institution and not request.user.institutions.filter(pk=complaint.institution_id).exists():
            return Response(
                {"error": "You can only reply to complaints against your institution."},
                status=status.HTTP_403_FORBIDDEN,
            )

        inst = complaint.institution
        if not inst:
            return Response(
                {"error": "Complaint has no linked institution."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reply = InstitutionReply.objects.create(
            complaint=complaint,
            institution=inst,
            submitted_by=request.user,
            content=serializer.validated_data["content"],
        )

        # Timeline event
        CaseTimelineEvent.objects.create(
            complaint=complaint,
            event_type=CaseTimelineEvent.EventType.REPLY,
            action="Institution Reply Received",
            detail=f"Reply from {inst.name}",
            actor=request.user,
            actor_label=request.user.username,
        )
        AuditEvent.log(
            AuditEvent.Action.REPLY_SUBMITTED, request=request,
            target_type="InstitutionReply", target_id=str(reply.id),
            detail=f"Reply submitted for {complaint.tracking_id}",
        )
        return Response(
            InstitutionReplySerializer(reply).data,
            status=status.HTTP_201_CREATED,
        )


class InstitutionReplyReviewView(views.APIView):
    """POST /api/replies/<id>/review/ — accept/reject a reply (analysts)."""
    permission_classes = [IsAnalystOrAbove]

    def post(self, request, pk):
        try:
            reply = InstitutionReply.objects.get(pk=pk)
        except InstitutionReply.DoesNotExist:
            return Response({"error": "Reply not found"}, status=404)

        action = request.data.get("action")  # "accept" or "reject"
        if action not in ("accept", "reject"):
            return Response(
                {"error": "action must be 'accept' or 'reject'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reply.status = (
            InstitutionReply.ReviewStatus.ACCEPTED if action == "accept"
            else InstitutionReply.ReviewStatus.REJECTED
        )
        reply.reviewed_by = request.user
        reply.save()

        AuditEvent.log(
            AuditEvent.Action.REPLY_REVIEWED, request=request,
            target_type="InstitutionReply", target_id=str(reply.id),
            detail=f"Reply {action}ed for {reply.complaint.tracking_id}",
        )
        return Response(InstitutionReplySerializer(reply).data)
