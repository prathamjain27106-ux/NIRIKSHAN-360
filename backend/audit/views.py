"""
NIRIKSHAN 360 — Audit Views
===============================
"""

from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from accounts.permissions import IsAuditorOrAdmin, IsAdminOrBureauHead
from accounts.crypto import decrypt_identity
from .models import AuditEvent, IdentityAccessRequest, IdentityAccessApproval
from .serializers import (
    AuditEventSerializer, IdentityAccessRequestSerializer,
    IdentityRevealRequestCreateSerializer, IdentityRevealApproveSerializer,
)


class AuditEventListView(generics.ListAPIView):
    """GET /api/audit/ — paginated audit log (admin/auditor only)."""
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuditorOrAdmin]

    def get_queryset(self):
        qs = AuditEvent.objects.all()
        params = self.request.query_params
        if params.get("action"):
            qs = qs.filter(action=params["action"])
        if params.get("actor"):
            qs = qs.filter(actor_username__icontains=params["actor"])
        if params.get("target"):
            qs = qs.filter(target_id__icontains=params["target"])
        return qs


class IdentityRevealRequestView(views.APIView):
    """POST /api/identity/request/ — request identity reveal.
    GET — list pending requests."""
    permission_classes = [IsAdminOrBureauHead]

    def get(self, request):
        qs = IdentityAccessRequest.objects.select_related("complaint", "requester")
        return Response(IdentityAccessRequestSerializer(qs, many=True).data)

    def post(self, request):
        serializer = IdentityRevealRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from complaints.models import Complaint
        complaint = Complaint.objects.get(pk=serializer.validated_data["complaint_id"])

        # Check for existing pending request
        existing = IdentityAccessRequest.objects.filter(
            complaint=complaint,
            status=IdentityAccessRequest.RequestStatus.PENDING,
        ).first()
        if existing:
            return Response(
                {"error": "A pending reveal request already exists for this complaint.",
                 "request_id": str(existing.id)},
                status=status.HTTP_409_CONFLICT,
            )

        reveal_req = IdentityAccessRequest.objects.create(
            complaint=complaint,
            requester=request.user,
            reason=serializer.validated_data["reason"],
        )

        AuditEvent.log(
            AuditEvent.Action.IDENTITY_REVEAL_REQUEST, request=request,
            target_type="Complaint", target_id=complaint.tracking_id,
            detail=f"Identity reveal requested. Reason: {reveal_req.reason}",
        )
        return Response(
            IdentityAccessRequestSerializer(reveal_req).data,
            status=status.HTTP_201_CREATED,
        )


class IdentityRevealApproveView(views.APIView):
    """POST /api/identity/<request_id>/approve/ — approve/deny reveal.
    Two distinct approvers required."""
    permission_classes = [IsAdminOrBureauHead]

    def post(self, request, pk):
        try:
            reveal_req = IdentityAccessRequest.objects.get(pk=pk)
        except IdentityAccessRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)

        if reveal_req.status != IdentityAccessRequest.RequestStatus.PENDING:
            return Response(
                {"error": f"Request is already {reveal_req.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Requester cannot approve their own request
        if reveal_req.requester == request.user:
            return Response(
                {"error": "You cannot approve your own reveal request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if already voted
        if reveal_req.approvals.filter(approver=request.user).exists():
            return Response(
                {"error": "You have already voted on this request."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = IdentityRevealApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approval = IdentityAccessApproval.objects.create(
            request=reveal_req,
            approver=request.user,
            approved=serializer.validated_data["approved"],
            comment=serializer.validated_data.get("comment", ""),
        )

        action = AuditEvent.Action.IDENTITY_REVEAL_APPROVE if approval.approved else AuditEvent.Action.IDENTITY_REVEAL_DENY
        AuditEvent.log(
            action, request=request,
            target_type="IdentityAccessRequest", target_id=str(reveal_req.id),
            detail=f"{'Approved' if approval.approved else 'Denied'}. {approval.comment}",
        )

        # Check if any denial → deny the whole request
        if not approval.approved:
            reveal_req.status = IdentityAccessRequest.RequestStatus.DENIED
            reveal_req.save()
            return Response({
                "message": "Identity reveal request denied.",
                "request": IdentityAccessRequestSerializer(reveal_req).data,
            })

        # Check if fully approved (2 distinct approvers)
        if reveal_req.is_fully_approved:
            reveal_req.status = IdentityAccessRequest.RequestStatus.APPROVED
            reveal_req.save()

            # Decrypt and return identity
            complaint = reveal_req.complaint
            try:
                ct = bytes(complaint.complainant_encrypted) if not isinstance(complaint.complainant_encrypted, bytes) else complaint.complainant_encrypted
                nonce = bytes(complaint.complainant_nonce) if complaint.complainant_nonce and not isinstance(complaint.complainant_nonce, bytes) else (complaint.complainant_nonce or b"")
                identity = decrypt_identity(ct, nonce)
            except Exception:
                identity = "[decryption failed]"

            AuditEvent.log(
                AuditEvent.Action.IDENTITY_REVEALED, request=request,
                target_type="Complaint", target_id=complaint.tracking_id,
                detail="Identity decrypted after dual approval.",
            )
            return Response({
                "message": "Identity reveal approved and decrypted.",
                "identity": identity,
                "request": IdentityAccessRequestSerializer(reveal_req).data,
            })

        return Response({
            "message": f"Approval recorded. {reveal_req.approval_count}/2 approvals received.",
            "request": IdentityAccessRequestSerializer(reveal_req).data,
        })
