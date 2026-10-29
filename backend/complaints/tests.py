"""
NIRIKSHAN 360 — Comprehensive Tests
=======================================
Unit and integration tests for models, views, encryption, and permissions.
"""

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from accounts.crypto import encrypt_identity, decrypt_identity
from complaints.models import Complaint, CaseTimelineEvent, SLAPolicy
from institutions.models import Institution, NormCheckResult
from audit.models import AuditEvent, IdentityAccessRequest, IdentityAccessApproval


# ═══════════════════════════════════════════════
#  Encryption Tests
# ═══════════════════════════════════════════════

class CryptoTest(TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "name=Rahul Verma|contact=rahul@test.in"
        ct, nonce = encrypt_identity(plaintext)
        self.assertNotEqual(ct, b"")
        self.assertEqual(len(nonce), 12)
        result = decrypt_identity(ct, nonce)
        self.assertEqual(result, plaintext)

    def test_empty_plaintext(self):
        ct, nonce = encrypt_identity("")
        self.assertEqual(ct, b"")
        self.assertEqual(nonce, b"")

    def test_unicode_identity(self):
        plaintext = "name=राहुल वर्मा|contact=rahul@test.in"
        ct, nonce = encrypt_identity(plaintext)
        result = decrypt_identity(ct, nonce)
        self.assertEqual(result, plaintext)


# ═══════════════════════════════════════════════
#  Model Tests
# ═══════════════════════════════════════════════

class ComplaintModelTest(TestCase):
    def test_auto_tracking_id(self):
        ct, nonce = encrypt_identity("test")
        c = Complaint(
            title="Test complaint", description="Test",
            complainant_encrypted=ct, complainant_nonce=nonce,
        )
        c.save()
        self.assertTrue(c.tracking_id.startswith("NIR-"))
        self.assertEqual(c.sequence, 1)

    def test_sequential_tracking_ids(self):
        ct, nonce = encrypt_identity("test")
        c1 = Complaint(title="First", description="Test", complainant_encrypted=ct, complainant_nonce=nonce)
        c1.save()
        c2 = Complaint(title="Second", description="Test", complainant_encrypted=ct, complainant_nonce=nonce)
        c2.save()
        self.assertEqual(c2.sequence, 2)
        self.assertNotEqual(c1.tracking_id, c2.tracking_id)

    def test_sla_breach_detection(self):
        from django.utils import timezone
        from datetime import timedelta
        ct, nonce = encrypt_identity("test")
        c = Complaint(
            title="Breached", description="Test",
            complainant_encrypted=ct, complainant_nonce=nonce,
            sla_deadline=timezone.now() - timedelta(hours=1),
            status="UNDER_REVIEW",
        )
        c.save()
        self.assertTrue(c.is_sla_breached)

    def test_resolved_not_breached(self):
        from django.utils import timezone
        from datetime import timedelta
        ct, nonce = encrypt_identity("test")
        c = Complaint(
            title="Resolved", description="Test",
            complainant_encrypted=ct, complainant_nonce=nonce,
            sla_deadline=timezone.now() - timedelta(hours=1),
            status="RESOLVED",
        )
        c.save()
        self.assertFalse(c.is_sla_breached)


class InstitutionModelTest(TestCase):
    def test_create_institution(self):
        inst = Institution.objects.create(
            name="Test College", aicte_id="AICTE-TEST-001",
            state="Maharashtra", city="Pune",
        )
        self.assertEqual(str(inst), "Test College (AICTE-TEST-001)")

    def test_unique_aicte_id(self):
        Institution.objects.create(name="College A", aicte_id="AICTE-001", state="MH", city="Pune")
        with self.assertRaises(Exception):
            Institution.objects.create(name="College B", aicte_id="AICTE-001", state="KA", city="BLR")


class AuditModelTest(TestCase):
    def test_audit_log_factory(self):
        event = AuditEvent.log(
            AuditEvent.Action.SYSTEM,
            target_type="Test", target_id="123",
            detail="Test event",
        )
        self.assertEqual(event.action, "SYSTEM")
        self.assertEqual(event.actor_username, "system")

    def test_audit_with_actor(self):
        user = User.objects.create_user(username="tester", password="test123", role="ANALYST")
        event = AuditEvent.log(
            AuditEvent.Action.TRIAGE, actor=user,
            target_type="Complaint", target_id="NIR-TEST-001",
        )
        self.assertEqual(event.actor_username, "tester")
        self.assertEqual(event.actor_role, "ANALYST")


class IdentityRevealTest(TestCase):
    def test_dual_approval_required(self):
        admin1 = User.objects.create_user(username="admin1", password="pass", role="ADMIN")
        admin2 = User.objects.create_user(username="admin2", password="pass", role="ADMIN")
        bureau = User.objects.create_user(username="bureau", password="pass", role="BUREAU_HEAD")

        ct, nonce = encrypt_identity("name=Test|contact=test@test.in")
        complaint = Complaint(
            title="Test", description="Test",
            complainant_encrypted=ct, complainant_nonce=nonce,
        )
        complaint.save()

        req = IdentityAccessRequest.objects.create(
            complaint=complaint, requester=bureau, reason="Investigation",
        )
        self.assertFalse(req.is_fully_approved)

        IdentityAccessApproval.objects.create(request=req, approver=admin1, approved=True)
        self.assertFalse(req.is_fully_approved)  # Still need 2

        IdentityAccessApproval.objects.create(request=req, approver=admin2, approved=True)
        self.assertTrue(req.is_fully_approved)  # Now 2 approvals

    def test_unique_vote_per_approver(self):
        admin1 = User.objects.create_user(username="admin1", password="pass", role="ADMIN")
        ct, nonce = encrypt_identity("test")
        complaint = Complaint(title="Test", description="Test", complainant_encrypted=ct, complainant_nonce=nonce)
        complaint.save()
        req = IdentityAccessRequest.objects.create(complaint=complaint, requester=admin1, reason="Test")
        IdentityAccessApproval.objects.create(request=req, approver=admin1, approved=True)
        with self.assertRaises(Exception):
            IdentityAccessApproval.objects.create(request=req, approver=admin1, approved=True)


# ═══════════════════════════════════════════════
#  API Tests
# ═══════════════════════════════════════════════

class AuthAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin", password="admin123", role="ADMIN",
        )
        self.analyst = User.objects.create_user(
            username="analyst", password="analyst123", role="ANALYST", cell="PGRC",
        )
        self.nodal = User.objects.create_user(
            username="nodal", password="nodal123", role="NODAL_OFFICER",
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_unauthenticated_blocked(self):
        response = self.client.get("/api/complaints/")
        self.assertEqual(response.status_code, 401)

    def test_health_endpoint(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_me_endpoint(self):
        self._auth(self.admin)
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "admin")


class ComplaintAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username="admin", password="pass", role="ADMIN")
        self.analyst = User.objects.create_user(username="analyst", password="pass", role="ANALYST")
        self.nodal = User.objects.create_user(username="nodal", password="pass", role="NODAL_OFFICER")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_create_complaint(self):
        self._auth(self.admin)
        response = self.client.post("/api/complaints/create/", {
            "title": "Test complaint",
            "description": "This is a test complaint for unit testing.",
            "category": "FEE_REFUND",
            "institution_name": "Test College",
            "state": "Maharashtra",
            "complainant_name": "Test User",
            "complainant_contact": "test@test.in",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["tracking_id"].startswith("NIR-"))
        self.assertEqual(data["status"], "SUBMITTED")
        # Identity should NOT be in plaintext
        self.assertNotIn("Test User", str(data))

    def test_create_routes_by_category(self):
        self._auth(self.admin)
        response = self.client.post("/api/complaints/create/", {
            "title": "Hostel ragging",
            "description": "A serious incident needs review.",
            "category": "RAGGING",
            "institution_name": "Test College",
            "state": "Maharashtra",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["cell"], "ANTI_RAGGING")
        self.assertEqual(response.json()["urgency"], "CRITICAL")
        self.assertFalse(response.json()["needs_human_review"])

    def test_create_requires_institution_name(self):
        self._auth(self.admin)
        response = self.client.post("/api/complaints/create/", {
            "title": "Missing institution",
            "description": "This should fail validation.",
            "category": "OTHER",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("institution_name", response.json())

    def test_list_complaints(self):
        self._auth(self.analyst)
        # Create one first
        ct, nonce = encrypt_identity("test")
        Complaint(title="Listed", description="Test", complainant_encrypted=ct, complainant_nonce=nonce).save()
        response = self.client.get("/api/complaints/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 1)

    def test_filter_by_status(self):
        self._auth(self.analyst)
        ct, nonce = encrypt_identity("test")
        Complaint(title="Open", description="Test", status="SUBMITTED", complainant_encrypted=ct, complainant_nonce=nonce).save()
        Complaint(title="Closed", description="Test", status="RESOLVED", complainant_encrypted=ct, complainant_nonce=nonce).save()
        response = self.client.get("/api/complaints/?status=SUBMITTED")
        self.assertEqual(response.status_code, 200)
        for item in response.json()["results"]:
            self.assertEqual(item["status"], "SUBMITTED")

    def test_assign_complaint(self):
        self._auth(self.admin)
        ct, nonce = encrypt_identity("test")
        c = Complaint(title="To assign", description="Test", complainant_encrypted=ct, complainant_nonce=nonce)
        c.save()
        response = self.client.post(f"/api/complaints/{c.pk}/assign/", {
            "assigned_to": self.analyst.pk,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        c.refresh_from_db()
        self.assertEqual(c.assigned_to, self.analyst)

    def test_status_update(self):
        self._auth(self.analyst)
        ct, nonce = encrypt_identity("test")
        c = Complaint(title="To update", description="Test", status="SUBMITTED",
                      complainant_encrypted=ct, complainant_nonce=nonce)
        c.save()
        response = self.client.post(f"/api/complaints/{c.pk}/status/", {
            "status": "TRIAGED", "reason": "Auto-triaged",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        c.refresh_from_db()
        self.assertEqual(c.status, "TRIAGED")

    def test_invalid_status_transition_rejected(self):
        self._auth(self.analyst)
        ct, nonce = encrypt_identity("test")
        c = Complaint(
            title="To update", description="Test", status="SUBMITTED",
            complainant_encrypted=ct, complainant_nonce=nonce,
        )
        c.save()
        response = self.client.post(f"/api/complaints/{c.pk}/status/", {
            "status": "RESOLVED", "reason": "Not permitted directly",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        c.refresh_from_db()
        self.assertEqual(c.status, "SUBMITTED")

    def test_dashboard(self):
        self._auth(self.analyst)
        response = self.client.get("/api/complaints/dashboard/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_complaints", data)
        self.assertIn("monthly_trend", data)

    def test_nodal_cannot_assign(self):
        """Nodal officers should NOT be able to assign complaints."""
        self._auth(self.nodal)
        ct, nonce = encrypt_identity("test")
        c = Complaint(title="Test", description="Test", complainant_encrypted=ct, complainant_nonce=nonce)
        c.save()
        response = self.client.post(f"/api/complaints/{c.pk}/assign/", {
            "assigned_to": self.analyst.pk,
        }, format="json")
        self.assertEqual(response.status_code, 403)


class InstitutionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username="admin", password="pass", role="ADMIN")

    def test_list_institutions(self):
        self.client.force_authenticate(user=self.admin)
        Institution.objects.create(name="Test Inst", aicte_id="T-001", state="MH", city="Pune")
        response = self.client.get("/api/institutions/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 1)

    def test_institution_detail(self):
        self.client.force_authenticate(user=self.admin)
        inst = Institution.objects.create(name="Detail Inst", aicte_id="T-002", state="KA", city="BLR")
        response = self.client.get(f"/api/institutions/{inst.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Detail Inst")


class AuditAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username="admin", password="pass", role="ADMIN")
        self.auditor = User.objects.create_user(username="auditor", password="pass", role="AUDITOR")
        self.analyst = User.objects.create_user(username="analyst", password="pass", role="ANALYST")

    def test_auditor_can_view_audit_log(self):
        self.client.force_authenticate(user=self.auditor)
        AuditEvent.log(AuditEvent.Action.SYSTEM, detail="Test event")
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, 200)

    def test_analyst_cannot_view_audit_log(self):
        """Analysts should NOT see audit log — only admin/auditor."""
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, 403)

    def test_audit_events_are_immutable(self):
        """Verify AuditEvent admin blocks changes."""
        from audit.admin import AuditEventAdmin
        admin_instance = AuditEventAdmin(AuditEvent, None)
        self.assertFalse(admin_instance.has_change_permission(None))
        self.assertFalse(admin_instance.has_delete_permission(None))
